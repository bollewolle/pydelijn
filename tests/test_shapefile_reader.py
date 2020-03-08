import aiohttp

from pystibmvib.STIBAPIClient import STIBAPIClient
from pystibmvib.ShapefileService import ShapefileService


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    client_id = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
    client_secret = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'
    custom_session = aiohttp.ClientSession()

    APIClient = STIBAPIClient(LOOP, custom_session, client_id, client_secret)

    line_id = 46
    maxpassages = 10
    sf_reader = ShapefileService(APIClient)

    print(await sf_reader.get_stop_infos("Scherdemael"))
    print(await sf_reader.get_stop_infos("Scherdemaal"))

    await custom_session.close()



import asyncio

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_shapefile_reader())
LOOP.close()