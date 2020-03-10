"""Example usage of pystibmvib."""
import asyncio
import unittest

import aiohttp

from pystibmvib.STIBAPIClient import STIBAPIClient
from pystibmvib.STIBService import STIBService
from tests.pystibmvib import MockAPIClient

# CLIENT_ID = 'Wirff1HT1tTH7mLX1dMQAbOEHDoa'
# CLIENT_SECRET = 'tYKqSKbmjw3hKsoNtaaKKtXXP0sa'


class TestPassages(unittest.TestCase):
    def setUp(self):
        self.LOOP = asyncio.get_event_loop()

    def tearDown(self):
        self.LOOP.close()

    def test_filtered_out(self):
        async def go(LOOP):
            stop_name = "scherdemael"
            filtered_out_stop_ids = ['3713']
            custom_session = aiohttp.ClientSession()

            APIClient = MockAPIClient()

            service = STIBService(APIClient)
            print(await service.getPassages(stop_name, [(46, "Glibert")]))

            await custom_session.close()

        self.LOOP.run_until_complete(go(self.LOOP))

if __name__ == '__main__':
    unittest.main()



