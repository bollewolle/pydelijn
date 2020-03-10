import json
import logging

from pystibmvib import STIBAPIClient
from pystibmvib.ShapefileService import ShapefileService
from pystibmvib.domain.passages import Passage

LOGGER = logging.getLogger(__name__)

PASSING_TIME_BY_POINT_SUFFIX = "/OperationMonitoring/4.0/PassingTimeByPoint/"


class STIBService:
    def __init__(self, stib_api_client: STIBAPIClient):
        self._shapefile_service = ShapefileService(stib_api_client)
        self.api_client = stib_api_client

    async def getPassages(self, stop_name, line_filters=None):
        stop_infos = await self._shapefile_service.get_stop_infos(stop_name)

        atomic_stop_infos = stop_infos.get_lines()
        if line_filters is not None:
            for line_nr, line_dest in line_filters:
                atomic_stop_infos = filter(lambda s: s.get_line_nr() == line_nr and s.get_destination().upper() == line_dest.upper(), atomic_stop_infos)

        passages = []
        for atomic in atomic_stop_infos:
            call_URL_suffix = PASSING_TIME_BY_POINT_SUFFIX + atomic.get_stop_id()

            raw_passages = await self.api_client.api_call(call_URL_suffix)
            print(raw_passages)
            raw_passages = json.loads(raw_passages)
            for point in raw_passages["points"]:
                for json_passage in point["passingTimes"]:
                    print(json_passage)
                    passages.append(Passage(point["pointId"], json_passage["lineId"], json_passage["destination"], json_passage["expectedArrivalTime"], await self._shapefile_service.get_line_info(json_passage["lineId"])))
            print(raw_passages)
        print(passages)

        return passages
