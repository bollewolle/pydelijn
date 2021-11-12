"""
Get realtime info on stop passages of De Lijn (api.delijn.be).

A module to get information about the next passages from a stop
of De Lijn, the public transportation company of Flanders (Belgium).

This code is released under the terms of the MIT license. See the LICENSE
file for more details.
"""
from datetime import datetime
import pytz
from .common import BASE_URL, LOGGER, CommonFunctions


def convert_to_utc(localtime, timeformat):
    """Convert local time of Europe/Brussels of the API into UTC."""
    if localtime is None:
        return None
    if timeformat is None:
        timeformat = "%Y-%m-%dT%H:%M:%S"
    localtimezone = pytz.timezone("Europe/Brussels")
    localtimenaive = datetime.strptime(localtime, timeformat)
    dtlocal = localtimezone.localize(localtimenaive)
    dtutc = dtlocal.astimezone(pytz.utc)
    return dtutc


class Passages:
    """A class to get passage information."""

    def __init__(
        self, stopid, maxpassages, subscriptionkey, session=None, utcoutput=None
    ):
        """Initialize the class."""
        self.session = session
        self.stopid = str(stopid)
        self.stopname = self.stopid
        self.maxpassages = maxpassages
        self.subscriptionkey = subscriptionkey
        self._passages = []
        self.utcoutput = utcoutput
        self._colourshex = None
        self._linecolours = {}
        self._linepublic = {}

    async def get_stopname(self):
        """Get the stop name from the stopid."""
        if self.stopname == self.stopid:
            selfcreatedsession = False
            if self.session is None:
                selfcreatedsession = True
            entitynum = self.stopid[:1]
            endpointstop = "{}haltes/{}/{}".format(
                BASE_URL, str(entitynum), str(self.stopid)
            )
            common = CommonFunctions(self.session, self.subscriptionkey)
            resultstop = await common.api_call(endpointstop)
            if resultstop is not None:
                self.stopname = "{}, {}".format(
                    str(resultstop.get("omschrijving")),
                    str(resultstop.get("omschrijvingGemeente")),
                )
            if selfcreatedsession is True:
                await common.close()
        return self.stopname

    async def get_colourshex(self, common):
        """Get the colours hex codes."""
        if self._colourshex is None:
            endpointcolours = "{}kleuren/".format(BASE_URL)
            colourshex = {}
            resultcolours = await common.api_call(endpointcolours)
            if resultcolours is not None:
                for colours in resultcolours["kleuren"]:
                    colourshex.update({str(colours.get("code")): colours.get("hex")})
                self._colourshex = colourshex
        return self._colourshex

    async def get_linecolours(self, common, ent_num, linenumber):
        """Get the colours of the line."""
        if (ent_num, linenumber) not in self._linecolours:
            endpointlinecolours = "{}lijnen/{}/" "{}/lijnkleuren".format(
                BASE_URL, str(ent_num), str(linenumber)
            )
            resultlinecolours = await common.api_call(endpointlinecolours)
            if resultlinecolours is not None:
                self._linecolours[(ent_num, linenumber)] = resultlinecolours
        return self._linecolours[(ent_num, linenumber)]

    async def get_linepublic(self, common, ent_num, linenumber):
        """Get the line information."""
        if (ent_num, linenumber) not in self._linepublic:
            endpointlinepublic = "{}lijnen/{}/{}".format(
                BASE_URL, str(ent_num), str(linenumber)
            )
            resultlinepublic = await common.api_call(endpointlinepublic)
            if resultlinepublic is not None:
                self._linepublic[(ent_num, linenumber)] = resultlinepublic
        return self._linepublic[(ent_num, linenumber)]

    async def get_passages(self):
        """Get passages info from stopid."""
        selfcreatedsession = False
        if self.session is None:
            selfcreatedsession = True
        entitynum = self.stopid[:1]
        common = CommonFunctions(self.session, self.subscriptionkey)
        passages = []
        tzone = pytz.timezone("Europe/Brussels")

        colourshex = await self.get_colourshex(common)

        endpointrealtime = "{}haltes/{}/{}/real-time".format(
            BASE_URL, str(entitynum), str(self.stopid)
        )
        resultrealtime = await common.api_call(endpointrealtime)
        if resultrealtime is not None:
            for stoppassages in resultrealtime["halteDoorkomsten"] or []:
                try:
                    for index, passage in zip(
                        range(self.maxpassages), stoppassages["doorkomsten"]
                    ):
                        ent_num = passage.get("entiteitnummer")
                        linenumber = passage.get("lijnnummer")
                        direction = passage.get("richting")
                        final_destination = passage.get("bestemming")
                        due_at_schedule = passage.get("dienstregelingTijdstip")
                        due_at_realtime = passage.get("real-timeTijdstip")
                        realtime_info = passage.get("predictionStatussen")
                        if realtime_info[0] == "GEENREALTIME":
                            is_realtime = False
                        elif realtime_info[0] == "REALTIME":
                            is_realtime = True
                        else:
                            is_realtime = False
                            LOGGER.warning("unknown realtime info: %s", realtime_info)

                        due_in_min = None

                        timeformat = "%Y-%m-%dT%H:%M:%S"
                        if self.utcoutput is True:
                            if due_at_realtime is not None:
                                dt_rt_utc = convert_to_utc(due_at_realtime, timeformat)
                                due_at_realtime = dt_rt_utc.isoformat()

                            if due_at_schedule is not None:
                                dt_sch_utc = convert_to_utc(due_at_schedule, timeformat)
                                due_at_schedule = dt_sch_utc.isoformat()

                            dt_now_utc = datetime.now(pytz.utc)
                            if due_at_realtime is not None:
                                diff = dt_rt_utc - dt_now_utc
                                due_in_min = int(diff.total_seconds() / 60)
                            elif due_at_schedule is not None:
                                diff = dt_sch_utc - dt_now_utc
                                due_in_min = int(diff.total_seconds() / 60)
                        else:
                            if due_at_realtime is not None:
                                dt_rt_local = tzone.localize(
                                    datetime.strptime(due_at_realtime, timeformat)
                                )
                                dt_now_local = tzone.localize(datetime.now())
                                diff = dt_rt_local - dt_now_local
                                due_in_min = int(diff.total_seconds() / 60)
                            elif due_at_schedule is not None:
                                dt_sch_local = tzone.localize(
                                    datetime.strptime(due_at_schedule, timeformat)
                                )
                                dt_now_local = tzone.localize(datetime.now())
                                diff = dt_sch_local - dt_now_local
                                due_in_min = int(diff.total_seconds() / 60)

                        resultlinepublic = await self.get_linepublic(
                            common, ent_num, linenumber
                        )
                        if resultlinepublic is not None:
                            linenumberpublic = resultlinepublic.get("lijnnummerPubliek")
                            linedesc = resultlinepublic.get("omschrijving")
                            linetransporttype = resultlinepublic.get("vervoertype")

                            resultlinecolours = await self.get_linecolours(
                                common, ent_num, linenumber
                            )
                            if resultlinecolours is not None and colourshex is not None:
                                linenumcolfront = resultlinecolours.get(
                                    "voorgrond"
                                ).get("code")
                                linenumcolfronthex = colourshex.get(
                                    str(linenumcolfront)
                                )
                                linenumcolback = resultlinecolours.get(
                                    "achtergrond"
                                ).get("code")
                                linenumcolbackhex = colourshex.get(str(linenumcolback))
                                linenumcolfrontborder = resultlinecolours.get(
                                    "voorgrondRand"
                                ).get("code")
                                linenumcolfrontborderhex = colourshex.get(
                                    str(linenumcolfrontborder)
                                )
                                linenumcolbackborder = resultlinecolours.get(
                                    "achtergrondRand"
                                ).get("code")
                                linenumcolbackborderhex = colourshex.get(
                                    str(linenumcolbackborder)
                                )

                                passages.append(
                                    {
                                        "passage": index,
                                        "line_number": linenumber,
                                        "direction": direction,
                                        "final_destination": final_destination,
                                        "due_at_schedule": due_at_schedule,
                                        "due_at_realtime": due_at_realtime,
                                        "due_in_min": due_in_min,
                                        "is_realtime": is_realtime,
                                        "line_number_public": linenumberpublic,
                                        "line_desc": linedesc,
                                        "line_transport_type": linetransporttype,
                                        "line_number_colourFront": linenumcolfront,
                                        "line_number_colourFrontHex": linenumcolfronthex,
                                        "line_number_colourBack": linenumcolback,
                                        "line_number_colourBackHex": linenumcolbackhex,
                                        "line_number_colourFrontBorder": linenumcolfrontborder,
                                        "line_number_colourFrontBorderHex": linenumcolfrontborderhex,
                                        "line_number_colourBackBorder": linenumcolbackborder,
                                        "line_number_colourBackBorderHex": linenumcolbackborderhex,
                                    }
                                )
                except (TypeError, KeyError, IndexError) as error:
                    LOGGER.warning("Error connecting to De Lijn api, %s", error)
        if selfcreatedsession is True:
            await common.close()
        self._passages = passages

    @property
    def passages(self):
        """Return the passages."""
        return self._passages
