"""Common attributes and functions."""
import logging
import asyncio
import async_timeout
import aiohttp
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

LOGGER = logging.getLogger(__name__)
BASE_URL = 'https://opendata-api.stib-mivb.be'

# curl -k -X GET --header "Accept: application/zip" --header "Authorization: Bearer b2ba6c7a35d667564ffa2765aec6ea07" -o ./gtfs.zip "https://opendata-api.stib-mivb.be/Files/2.0/Gtfs"
class CommonFunctions():
    """A class for common functions."""

    def __init__(self, loop, session, client_id, client_secret):
        """Initialize the class."""
        self.loop = loop
        self.session = session
        self.client_id = client_id
        self.client_secret = client_secret


    async def api_call(self, endpoint):
        token_url = BASE_URL+'/token'

        client = BackendApplicationClient(self.client_id)
        session = OAuth2Session(self.client_id, client=client)
        session.fetch_token(token_url, auth=(self.client_id, self.client_secret))

        """Call the API."""
        headers = {'Authorization': "Bearer "+str(session.access_token)}
        data = None
        if self.session is None:
            self.session = aiohttp.ClientSession()
        try:
            async with async_timeout.timeout(5, loop=self.loop):
                LOGGER.debug("Endpoint URL: %s", str(endpoint))
                response = await self.session.get(url=endpoint,
                                                  headers=headers)
                if response.content_type == "Application/json":
                    data = await response.json()
                elif response.content_type == "Application/zip":
                    data = await response.read()
                else:
                    data = await response.read()
        except aiohttp.ClientError as error:
            LOGGER.error("Error connecting to STIB/MVIB API: %s", error)
        except asyncio.TimeoutError as error:
            LOGGER.debug("Timeout connecting to STIB/MVIB API: %s", error)
        return data

    async def close(self):
        """Close the session."""
        await self.session.close()
