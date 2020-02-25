import aiohttp

from pystibmvib.shapefile_reader import ShapefileReader


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    client_id = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
    client_secret = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'

    line_id = 46
    maxpassages = 10
    custom_session = aiohttp.ClientSession()
    r = ShapefileReader(LOOP, custom_session, client_id, client_secret)

    print(await r.get_line_info(line_id))
    print(await r.get_stop_info("scherdemael"))

    await custom_session.close()



import asyncio

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_shapefile_reader())
LOOP.close()