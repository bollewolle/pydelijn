"""Common attributes and functions."""
from pystibmvib.STIBService import PASSING_TIME_BY_POINT_SUFFIX
from pystibmvib.ShapefileService import ENDPOINT_SHAPEFILES
from pystibmvib import AbstractSTIBAPIClient


class MockAPIClient(AbstractSTIBAPIClient):
    """A class for common functions."""

    def __init__(self):
        pass

    async def api_call(self, endpoint_suffix: str, additional_headers=None):
        if endpoint_suffix == ENDPOINT_SHAPEFILES:
            return open("../resources/shapefiles.zip", 'rb').read()
        elif endpoint_suffix.startswith(PASSING_TIME_BY_POINT_SUFFIX):
            if endpoint_suffix.endswith("3755"):
                return '{"points": [{"passingTimes": [{"destination": {"fr": "WTC / GLIBERT", "nl": "WTC / GLIBERT"}, "expectedArrivalTime": "2020-03-10T11:15:00+01:00", "lineId": "46"}, {"destination": {"fr": "WTC / GLIBERT", "nl": "WTC / GLIBERT"}, "expectedArrivalTime": "2020-03-10T11:24:00+01:00", "lineId": "46"}], "pointId": "3755"}]}'
