"""Common attributes and functions."""
import logging
import asyncio
import async_timeout
import aiohttp

LOGGER = logging.getLogger(__name__)
BASE_URL = "https://api.delijn.be/DLKernOpenData/v1/beta/"


class CommonFunctions:
    """A class for common functions."""

    def __init__(self, session, subscriptionkey):
        """Initialize the class."""
        self.session = session
        self.subscriptionkey = subscriptionkey

    async def api_call(self, endpoint):
        """Call the API."""
        headers = {"Ocp-Apim-Subscription-Key": self.subscriptionkey}
        data = None
        if self.session is None:
            self.session = aiohttp.ClientSession()
        try:
            async with async_timeout.timeout(5):
                LOGGER.debug("Endpoint URL: %s", str(endpoint))
                response = await self.session.get(url=endpoint, headers=headers)
                if response.status == 200:
                    try:
                        data = await response.json()
                    except ValueError as exception:
                        message = "Server gave incorrect data"
                        raise Exception(message) from exception

                elif response.status == 401:
                    message = "401: Acces token might be incorrect"
                    raise HttpException(message, await response.text(), response.status)

                elif response.status == 404:
                    message = "404: incorrect API request"
                    raise HttpException(message, await response.text(), response.status)

                else:
                    message = f"Unexpected status code {response.status}."
                    raise HttpException(message, await response.text(), response.status)

        except aiohttp.ClientError as error:
            LOGGER.error("Error connecting to De Lijn API: %s", error)
        except asyncio.TimeoutError as error:
            LOGGER.debug("Timeout connecting to De Lijn API: %s", error)
        return data

    async def close(self):
        """Close the session."""
        await self.session.close()


class HttpException(Exception):
    """HTTP exception class with message text, and status code."""

    def __init__(self, message, text, status_code):
        """Initialize the class."""
        super().__init__(message)

        self.status_code = status_code
        self.text = text
