"""
A module to get information about the next passages from a stop
of De Lijn, the public transportation company of Flanders (Belgium)

"""
from .common import BASE_URL, LOGGER

from datetime import timedelta, datetime
import pytz

class Passages():
    """A class to get passage information."""

    def __init__(self, loop, stopid, maxpassages, subscriptionkey, session=None):
        """Initialize the class."""
        self.loop = loop
        self.session = session
        self.stopid = str(stopid)
        self.maxpassages = maxpassages
        self.subscriptionkey = subscriptionkey
        self._passages = []

    async def get_passages(self):
        """Get passages info from stopid."""
        from .common import CommonFunctions
        entitynum = self.stopid[:1]
        common = CommonFunctions(self.loop, self.session, self.subscriptionkey)
        passages = []
        tzone = pytz.timezone('Europe/Brussels')

        endpointcolours = '{}kleuren/'.format(BASE_URL)
        colourshex = {}
        resultcolours = await common.api_call(endpointcolours)
        for colours in resultcolours['kleuren']:
            colourshex.update({str(colours.get('code')): colours.get('hex')})

        stopname = str(self.stopid)
        endpointstop = '{}haltes/{}/{}'.format(BASE_URL, str(entitynum), str(self.stopid))
        resultstop = await common.api_call(endpointstop)
        if resultstop != None:
            stopname = "{}, {}".format(str(resultstop.get('omschrijving')),str(resultstop.get('omschrijvingGemeente')))


        endpointrealtime = '{}haltes/{}/{}/real-time'.format(BASE_URL, str(entitynum), str(self.stopid))
        resultrealtime = await common.api_call(endpointrealtime)

        for stoppassages in resultrealtime['halteDoorkomsten'] or []:
            try:
                for index, passage in zip(range(self.maxpassages), stoppassages['doorkomsten']):
                    ent_num = passage.get('entiteitnummer')
                    line_number = passage.get('lijnnummer')
                    direction = passage.get('richting')
                    final_destination = passage.get('bestemming')
                    due_at_sch = passage.get('dienstregelingTijdstip')
                    due_at_rt = passage.get('real-timeTijdstip')
                    due_in_min = None

                    if due_at_rt != None:
                        dt_rt_local = tzone.localize(datetime.strptime(due_at_rt, "%Y-%m-%dT%H:%M:%S"), is_dst=None)
                        dt_now_local = tzone.localize(datetime.now(), is_dst=None)
                        diff = dt_rt_local - dt_now_local
                        due_in_min = int(diff.total_seconds() / 60)
                    elif due_at_sch != None:
                        dt_rt_local = tzone.localize(datetime.strptime(due_at_sch, "%Y-%m-%dT%H:%M:%S"), is_dst=None)
                        dt_now_local = tzone.localize(datetime.now(), is_dst=None)
                        diff = dt_rt_local - dt_now_local
                        due_in_min = int(diff.total_seconds() / 60)

                    endpointlinepublic = '{}lijnen/{}/{}'.format(BASE_URL, str(ent_num), str(line_number))
                    resultlinepublic = await common.api_call(endpointlinepublic)
                    line_number_public = resultlinepublic.get('lijnnummerPubliek')
                    line_desc = resultlinepublic.get('omschrijving')
                    line_transport_type = resultlinepublic.get('vervoertype')

                    endpointlinecolours = '{}lijnen/{}/{}/lijnkleuren'.format(BASE_URL, str(ent_num), str(line_number))
                    resultlinecolours = await common.api_call(endpointlinecolours)
                    line_number_colourFront = resultlinecolours.get('voorgrond').get('code')
                    line_number_colourFrontHex = colourshex.get(str(line_number_colourFront))
                    line_number_colourBack = resultlinecolours.get('achtergrond').get('code')
                    line_number_colourBackHex = colourshex.get(str(line_number_colourBack))
                    line_number_colourFrontBorder = resultlinecolours.get('voorgrondRand').get('code')
                    line_number_colourFrontBorderHex = colourshex.get(str(line_number_colourFrontBorder))
                    line_number_colourBackBorder = resultlinecolours.get('achtergrondRand').get('code')
                    line_number_colourBackBorderHex = colourshex.get(str(line_number_colourBackBorder))

                    passages.append({'stopname': stopname,
                                     'line_number': line_number,
                                     'direction': direction,
                                     'final_destination': final_destination,
                                     'due_at_sch': due_at_sch,
                                     'due_at_rt': due_at_rt,
                                     'due_in_min': due_in_min,
                                     'line_number_public': line_number_public,
                                     'line_desc': line_desc,
                                     'line_transport_type': line_transport_type,
                                     'line_number_colourFront': line_number_colourFront,
                                     'line_number_colourFrontHex': line_number_colourFrontHex,
                                     'line_number_colourBack': line_number_colourBack,
                                     'line_number_colourBackHex': line_number_colourBackHex,
                                     'line_number_colourFrontBorder': line_number_colourFrontBorder,
                                     'line_number_colourFrontBorderHex': line_number_colourFrontBorderHex,
                                     'line_number_colourBackBorder': line_number_colourBackBorder,
                                     'line_number_colourBackBorderHex': line_number_colourBackBorderHex
                                      })
            except (TypeError, KeyError, IndexError) as error:
                LOGGER.error('Error connecting to De Lijn api, %s', error)
        await common.close()
        self._passages = passages

    @property
    def passages(self):
        """Return the passages."""
        return self._passages