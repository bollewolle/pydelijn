import math
from datetime import *


def get_time_delta(t1, t2):
    if not type(t1) == type(datetime.now()):
        t1 = datetime.strptime(str(t1), "%Y-%m-%dT%H:%M:%S")
    t2 = datetime.strptime(t2.split("+")[0], "%Y-%m-%dT%H:%M:%S")  # 2020-02-08T14:40:00+01:00
    delta = t2.timestamp() - t1.timestamp()
    ret = max(0, int(math.floor(delta)))
    return ret
