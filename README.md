# pydelijn [![GitHub version](https://badge.fury.io/gh/bollewolle%2Fpydelijn.svg)](https://badge.fury.io/gh/bollewolle%2Fpydelijn) [![Build Status](https://travis-ci.com/bollewolle/pydelijn.svg?branch=master)](https://travis-ci.com/bollewolle/pydelijn) [![PyPI version](https://badge.fury.io/py/pydelijn.svg)](https://badge.fury.io/py/pydelijn)
A Python package to retrieve realtime data of passages at stops of De Lijn, the public transport company in Flanders (Belgium)

Main purpose at the moment is to feed a sensor in Home-Assistant

**Important note**: a developer account needs to be created at https://data.delijn.be to generate a subscription key for the api's.

## Install

```bash
pip install pydelijn
```

### Example usage

```python
"""Example usage of pydelijn."""
import asyncio
import aiohttp
from pydelijn.api import Passages


async def test_pydelijn():
    """Example usage of pydelijn."""
    subscriptionkey = '<put your data.delijn.be subscriptionkey here>'
    stopid = 200551
    maxpassages = 10
    custom_session = aiohttp.ClientSession()
    delijndata = Passages(LOOP,
                          stopid,
                          maxpassages,
                          subscriptionkey,
                          custom_session)
    await delijndata.get_departures()

    print_data(delijndata)


def print_data(delijndata):
    """Pretty Print the data."""
    for line in delijndata.passages:
        print("----------------------------------------")
        print("Passage #: %s" % (line['passage']))
        print("Stop Name: %s" % (line['stopname']))
        print("Line Number (technical): %s" % (line['line_number']))
        print("Line Number (public): %s" % (line['line_number_public']))
        print("Line Description: %s" % (line['line_desc']))
        print("Line Transport Type: %s" % (line['line_transport_type']))
        print("Direction: %s" % (line['direction']))
        print("Final Destination: %s" % (line['final_destination']))
        print("Due At (schedule): %s" % (line['due_at_sch']))
        print("Due At (real-time): %s" % (line['due_at_rt']))
        print("Due In (min): %s" % (line['due_in_min']))
        print("Line Colour - Front: %s - Hex: %s" % (
            line['line_number_colourFront'],
            line['line_number_colourFrontHex']))
        print("Line Colour - Back: %s - Hex: %s" % (
            line['line_number_colourBack'],
            line['line_number_colourBackHex']))
        print("Line Colour - Front Border: %s - Hex: %s" % (
            line['line_number_colourFrontBorder'],
            line['line_number_colourFrontBorderHex']))
        print("Line Colour - Back Border: %s - Hex: %s" % (
            line['line_number_colourBackBorder'],
            line['line_number_colourBackBorderHex']))


LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_pydelijn())
