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
import aiohttp 

from pystibmvib import Passages


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    client_id = '<put your opendata.stib-mivb.be client id here>'
    client_secret = '<put your opendata.stib-mivb.be client secret here>'


    stop_name = "scherdemael"
    filtered_out_stop_ids = ['3713']
    custom_session = aiohttp.ClientSession()

    r = Passages(LOOP, stop_name, client_id, client_secret, filtered_out_stop_ids=filtered_out_stop_ids, session=custom_session)

    await r.update_passages()
    print(r.passages)

    await custom_session.close()



import asyncio

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_shapefile_reader())
LOOP.close()

