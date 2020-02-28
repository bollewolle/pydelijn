"""Example usage of pystibmvib."""
import aiohttp
import asyncio

from pystibmvib import Passages

try:
    async def test_shapefile_reader():
        """Example usage of pystibmvib."""
        client_id = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
        client_secret = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'

        stop_name = "scherdemael"
        filtered_out_stop_ids = ['3713']
        custom_session = aiohttp.ClientSession()

        r = Passages(LOOP, stop_name, client_id, client_secret, filtered_out_stop_ids=filtered_out_stop_ids,
                     session=custom_session, time_ordered_result=True)

        await r.update_passages()

        await custom_session.close()



    LOOP = asyncio.get_event_loop()
    LOOP.run_until_complete(test_shapefile_reader())
    LOOP.close()
except:
    pass
