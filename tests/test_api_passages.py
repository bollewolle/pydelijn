"""Example usage of pystibmvib."""
import aiohttp

from pystibmvib.api import Passages


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    client_id = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
    client_secret = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'


    stop_name = "de brouckere"
    filtered_out_stop_ids = []#'1465','1820']
    custom_session = aiohttp.ClientSession()

    r = Passages(LOOP, stop_name, client_id, client_secret, filtered_out_stop_ids=filtered_out_stop_ids, session=custom_session, time_ordered_result=True)

    await r.update_passages()
    print(r.passages)

    await custom_session.close()



import asyncio

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_shapefile_reader())
LOOP.close()