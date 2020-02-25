"""
Get realtime info on stop passages of STIB/MVIB (opendata-api.stib-mivb.be).

A module to get information about the next passages from a stop
of STIB/MVIB, the public transportation company of Brussels (Belgium).

This code is released under the terms of the MIT license. See the LICENSE
file for more details.
"""
import json
from datetime import *

import pytz

from .common import APIClient
from .common import LOGGER
from .shapefile_reader import ShapefileReader

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
        t1 = datetime.strptime(str(t1), "%Y-%m-%dT%H:%M:%S")
    t2 = datetime.strptime(t2.split("+")[0], "%Y-%m-%dT%H:%M:%S")  # 2020-02-08T14:40:00+01:00
    delta = t2 - t1
    ret = max(0, delta.seconds)
    return delta.seconds


# {'passingTimes': [{'destination': {'fr': 'MOORTEBEEK', 'nl': 'MOORTEBEEK'}, 'expectedArrivalTime': '2020-02-10T17:36:00+01:00', 'lineId': '46'}
def sort_and_truncate_to(number, passingTimes):
    if len(passingTimes) == 0:
        return passingTimes
    elif len(passingTimes) > 1:
        LOGGER.warn("Should have gotten only one element in list this can cause weird behavior: " + str(passingTimes))
    time_getter = lambda j: datetime.strptime(j['expectedArrivalTime'].split("+")[0], "%Y-%m-%dT%H:%M:%S")
    res = []
    c = 0
    for passing in passingTimes[0]['passingTimes']:
        if "expectedArrivalTime" in passing.keys():
            res.append(passing)
            res.sort(key=(lambda p: time_getter(p)))
            c += 1
            if len(res) > number:
                res.pop()
    res = {'passingTimes': res, 'pointId': passingTimes[0]['pointId']}
    res = [res]
    return res


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
                 max_passages_per_stop=5,
                 time_ordered_result=False,
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
        self.max_passages_per_stop = max_passages_per_stop
        self.time_ordered_result = time_ordered_result
        self.filtered_out_stop_ids = filtered_out_stop_ids
        self.shapefile_info = ShapefileReader(loop, self.session, client_id, client_secret)
        self._linesinfo = None

    async def update_passages(self, now=None):
        if self._linesinfo is None:
            self._linesinfo = await self.shapefile_info.get_stop_info(self.stop_name, self.filtered_out_stop_ids)
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

        api_client = APIClient(self.loop, self.session, self.client_id, self.client_secret)

        if now is None:
            now = datetime.now()
        LOGGER.info("Fetching stop data at : " + str(now))

        # todo hotfix while we get an answer on multiple ids in the same call
        if False:
            call_URL_suffix = PASSING_TIME_BY_POINT_SUFFIX + "%2C".join(stop_ids)

            print("Calling URL: " + call_URL_suffix)
            raw_result = await api_client.api_call(call_URL_suffix, {'Accept': 'application/json'})
            if now is None:
                now = datetime.now()
                LOGGER.info(now)
            print("Got result from "+call_URL_suffix+" : "+str(raw_result))
            json_result = json.loads(raw_result)

        json_result = {'points': []}
        for stop_id in stop_ids:
            call_URL_suffix = PASSING_TIME_BY_POINT_SUFFIX + stop_id
            raw_result = await api_client.api_call(call_URL_suffix, {'Accept': 'application/json'})
            LOGGER.info("Got result from " + call_URL_suffix + " : " + str(raw_result))
            try:
                json_result['points'].extend(
                    sort_and_truncate_to(self.max_passages_per_stop, json.loads(raw_result)['points']))
            except:
                LOGGER.error(
                    "Something went wrong: Can't refresh stop info for stop_id: " + stop_id + "... " + str(raw_result))

        new_passages = []
        for point_info_json in json_result['points']:
            point_id = point_info_json['pointId']
            for pass_json in point_info_json['passingTimes']:
                pass_dest = pass_json['destination'][self.lang]
                pass_arrival_time = pass_json['expectedArrivalTime']
                pass_msg = ""
                if "message" in pass_json.keys():
                    pass_msg = pass_json["message"][self.lang]
                pass_arriving_in_seconds = get_time_delta(now, pass_arrival_time)
                pass_arriving_in_minutes = pass_arriving_in_seconds // 60
                pass_arriving_in_seconds = pass_arriving_in_seconds - (pass_arriving_in_minutes * 60)
                pass_line_number = pass_json['lineId']
                passage = {"destination": pass_dest,
                           "arrival_time": pass_arrival_time,
                           "stop_id": point_id,
                           "message": pass_msg,
                           "arriving_in": {"min": pass_arriving_in_minutes, "sec": pass_arriving_in_seconds}}
                additional_info = self._linesinfo[pass_line_number][0].copy()
                additional_info.pop("stop_id")
                passage.update(additional_info)
                new_passages.append(passage)
        LOGGER.info("New values for passages: " + str(new_passages))
        if self.time_ordered_result:
            new_passages.sort(key=(lambda j: datetime.strptime(j['arrival_time'].split("+")[0], "%Y-%m-%dT%H:%M:%S")))
        self._passages = new_passages

        if selfcreatedsession is True:
            await api_client.close()

    @property
    def passages(self):
        """Return the passages."""
        return self._passages
