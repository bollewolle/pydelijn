from pystibmvib.ShapefileService import ShapefileService
import asyncio
import unittest

from tests.pystibmvib import MockAPIClient


class TestShapefileReader(unittest.TestCase):
    def setUp(self):
        self.LOOP = asyncio.get_event_loop()

    def tearDown(self):
        self.LOOP.close()

    def test_filtered_out(self):
        async def go(LOOP):

            APIClient = MockAPIClient()

            sf_reader = ShapefileService(APIClient)

            print(await sf_reader.get_stop_infos("Scherdemael"))
            print(await sf_reader.get_stop_infos("Scherdemaal"))

        self.LOOP.run_until_complete(go(self.LOOP))

if __name__ == '__main__':
    unittest.main()
