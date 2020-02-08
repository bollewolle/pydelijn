"""
Get realtime info on stop passages of STIB/MVIB (opendata-api.stib-mivb.be).

A module to get information about the next passages from a stop
of STIB/MVIB, the public transportation company of Brussels (Belgium).

This code is released under the terms of the MIT license. See the LICENSE
file for more details.
"""
from datetime import *
import pytz
import json

from .common import BASE_URL, LOGGER
from .shapefile_reader import ShapefileReader

from .common import CommonFunctions

PASSING_TIME_BY_POINT_SUFFIX = "/OperationMonitoring/4.0/PassingTimeByPoint/"


def convert_to_utc(localtime, timeformat):
    """Convert local time of Europe/Brussels of the API into UTC."""
    if localtime is None:
        return None
    if timeformat is None:
        timeformat = '%Y-%m-%dT%H:%M:%S'
    localtimezone = pytz.timezone('Europe/Brussels')
    localtimenaive = datetime.strptime(localtime, timeformat)
    dtlocal = localtimezone.localize(localtimenaive)
    dtutc = dtlocal.astimezone(pytz.utc)
    return dtutc


def get_time_delta(t1, t2):
    if not type(t1) == type(datetime.now()):
        t1 = datetime.strptime('05/01/2012', "%")
    t2 = datetime.strptime(t2.split("+")[0], "%Y-%m-%dT%H:%M:%S")  # 2020-02-08T14:40:00+01:00
    delta = t2 - t1
    return delta.seconds


class Passages():
    """A class to get passage information."""

    def __init__(self,
                 loop,
                 stop_name,
                 client_id,
                 client_secret,
                 filtered_out_stop_ids=None,
                 session=None,
                 utcoutput=None,
                 lang='fr'):
        """Initialize the class."""
        if filtered_out_stop_ids is None:
            filtered_out_stop_ids = []
        self.loop = loop
        self.session = session
        self.stop_name = stop_name
        self.client_id = client_id
        self.client_secret = client_secret
        self._passages = []
        self.lang = lang
        self.utcoutput = utcoutput
        self.shapefile_info = ShapefileReader(loop, session, client_id, client_secret)
        self._linesinfo = self.shapefile_info.get_stop_info(self.stop_name, filtered_out_stop_ids)

    async def update_passages(self, now=None):
        """Get passages info for given stopname."""
        stop_ids = []
        for line_id, lineinfos in self._linesinfo.items():
            for lineinfo in lineinfos:
                sid = lineinfo["stop_id"]
                if sid not in stop_ids:
                    stop_ids.append(sid)

        selfcreatedsession = False
        if self.session is None:
            selfcreatedsession = True

        # https://opendata-api.stib-mivb.be/OperationMonitoring/4.0/PassingTimeByPoint/%7Bpoint

        common = CommonFunctions(self.loop, self.session, self.client_id, self.client_secret)

        callURL = BASE_URL + PASSING_TIME_BY_POINT_SUFFIX + \
                      str(stop_ids).replace("'", "")\
                                   .replace(" ", "")\
                                   .replace(",", "%2C")\
                                   .replace("[", "")\
                                   .replace("]", "")

        print("Calling URL: " + callURL)
        raw_result = await common.api_call(callURL, {'Accept': 'application/json'})
        if now is None:
            now = datetime.now()
            print(now)
        print("Got result from "+callURL+" : "+str(raw_result))
        json_result = json.loads(raw_result)

        new_passages = []
        for point_info_json in json_result['points']:
            point_id = point_info_json['pointId']
            for pass_json in point_info_json['passingTimes']:
                pass_dest = pass_json['destination'][self.lang]
                pass_arrival_time = pass_json['expectedArrivalTime']
                pass_arriving_in_seconds = get_time_delta(now, pass_arrival_time)
                pass_arriving_in_minutes = pass_arriving_in_seconds//60
                pass_arriving_in_seconds = pass_arriving_in_seconds - (pass_arriving_in_minutes*60)
                pass_line_number = pass_json['lineId']
                passage = {"destination": pass_dest,
                           "arrival_time": pass_arrival_time,
                           "point_id": point_id,
                           "arriving_in": {"min": pass_arriving_in_minutes, "sec": pass_arriving_in_seconds}}
                additional_info = self._linesinfo[pass_line_number][0].copy()
                additional_info.pop("stop_id")
                passage.update(additional_info)
                new_passages.append(passage)
        print("New values for passages: " + str(new_passages))
        self._passages = new_passages

        if selfcreatedsession is True:
            await common.close()

    @property
    def passages(self):
        """Return the passages."""
        return self._passages
