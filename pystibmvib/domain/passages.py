from datetime import *

from .line import LineInfo
from ..util.util import get_time_delta


class Passage:
    def __init__(self, stop_id: int, lineId: int, destination: str, expectedArrivalTime: str, lineInfos: LineInfo):
        self.stop_id = stop_id
        self.lineId = lineId
        self.destination = destination
        self.expectedArrivalTime = expectedArrivalTime
        self.lineInfos = lineInfos
        delta = get_time_delta(datetime.now(), expectedArrivalTime)
        self.arriving_in = {"min": delta // 60, "sec": delta % 60}

    def to_dict(self):
        return {"stop_id": self.stop_id, "lineId": self.lineId, "destination": self.destination,
                "expectedArrivalTime": self.expectedArrivalTime, "arriving_in": self.arriving_in,
                "line_color": self.lineInfos.get_line_color(), "line_type": self.lineInfos.get_line_type()}

    def __str__(self):
        return str(self.to_dict())

    def __repr__(self):
        return self.__str__()
