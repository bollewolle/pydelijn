# pystibmvib [![GitHub version](https://badge.fury.io/gh/helldog136%2Fpystibmvib.svg)](https://badge.fury.io/gh/helldog136%2Fpystibmvib) [![Build Status](https://travis-ci.com/helldog136%2Fpystibmvib.svg?branch=master)](https://travis-ci.com/helldog136/pystibmvib) [![PyPI version](https://badge.fury.io/py/pystibmvib.svg)](https://badge.fury.io/py/pystibmvib)
A Python package to retrieve realtime data of passages at stops of STIB/MVIB, the public transport company of Brussels (Belgium)

Main purpose at the moment is to feed a sensor in Home-Assistant

**Important note**: a developer account needs to be created at https://opendata.stib-mivb.be/ to generate a subscription key for the api's.

## Install

```bash
pip install pystibmvib
```

### Example usage

```python
"""Example usage of pystibmvib."""
import asyncio
import aiohttp
from pystibmvib.api import Passages


async def test_pystibmvib():
    """Example usage of pystibmvib."""
    subscriptionkey = '<put your opendata.stib-mivb.be subscription key here>'
    stopid = 2838
    maxpassages = 10
    custom_session = aiohttp.ClientSession()
    stibmvibdata = Passages(LOOP,
                          stopid,
                          maxpassages,
                          subscriptionkey,
                          custom_session,
                          True)
    await stibmvibdata.get_passages()
    await custom_session.close()

    print_data(stibmvibdata)


def print_data(stibmvibdata):
    """Pretty Print the data."""
    for line in stibmvibdata.passages:
        print("----------------------------------------")
        print("Passage #: %s" % (line['passage']))
        print("Stop Name: %s" % (line['stopname']))
        print("Line Number (technical): %s" % (line['line_number']))
        print("Line Number (public): %s" % (line['line_number_public']))
        print("Line Description: %s" % (line['line_desc']))
        print("Line Transport Type: %s" % (line['line_transport_type']))
        print("Direction: %s" % (line['direction']))
        print("Final Destination: %s" % (line['final_destination']))
        print("Due At (schedule): %s" % (line['due_at_schedule']))
        print("Due At (real-time): %s" % (line['due_at_realtime']))
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
LOOP.run_until_complete(test_pystibmvib())
LOOP.close()

