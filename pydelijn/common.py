"""Common attributes and functions."""
import logging
import asyncio
import async_timeout
import aiohttp

LOGGER = logging.getLogger(__name__)
BASE_URL = 'https://api.delijn.be/DLKernOpenData/v1/beta/'


class CommonFunctions():
    """A class for common functions."""

    def __init__(self, loop, session, subscriptionkey):
        """Initialize the class."""
        self.loop = loop
        self.session = session
        self.subscriptionkey = subscriptionkey

    async def api_call(self, endpoint):
        """Call the API."""
        headers = {'Ocp-Apim-Subscription-Key': self.subscriptionkey}
        data = None
        if self.session is None:
            self.session = aiohttp.ClientSession()
        try:
            async with async_timeout.timeout(5, loop=self.loop):
                LOGGER.debug("Endpoint URL: %s", str(endpoint))
                response = await self.session.get(url=endpoint,
                                                  headers=headers)
                data = await response.json()
        except aiohttp.ClientError as error:
            LOGGER.error("Error connecting to De Lijn API: %s", error)
        except asyncio.TimeoutError as error:
            LOGGER.debug("Timeout connecting to De Lijn API: %s", error)
        return data

    async def close(self):
        """Close the session."""
        await self.session.close()
