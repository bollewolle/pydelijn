"""Example usage of pystibmvib."""
import aiohttp

from pystibmvib.api import Passages


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    subscriptionkey = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'  # '<put your opendata.stib-mivb.be subscription key here>'

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

