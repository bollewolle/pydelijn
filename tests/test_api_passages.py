import aiohttp

from pystibmvib.api import Passages


async def test_shapefile_reader():
    """Example usage of pystibmvib."""
    subscriptionkey = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'  # '<put your opendata.stib-mivb.be subscription key here>'

    client_id = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
    client_secret = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'

    maxpassages = 10
    custom_session = aiohttp.ClientSession()

    r = Passages(LOOP, "scherdemael", maxpassages, client_id, client_secret, ['3755'], session=custom_session)

    await r.get_passages()
    print(r.passages)

    await custom_session.close()



import asyncio

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(test_shapefile_reader())
LOOP.close()