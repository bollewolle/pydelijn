"""Common attributes and functions."""
import asyncio
import base64
import logging
import time
from abc import ABC, abstractmethod

import aiohttp
import async_timeout

LOGGER = logging.getLogger(__name__)

API_BASE_URL = 'https://opendata-api.stib-mivb.be'


class OAuthTokenManager(object):
    def __init__(
            self,
            loop,
            session,
            client_id,
            client_secret,
            url,
            *,
            renew_pad_secs=60,
            **parameters
    ):
        self.session = session
        self.client_secret = client_secret
        self.client_id = client_id
        self.loop = loop
        self.url = url
        self.parameters = parameters
        self.renew_pad_secs = renew_pad_secs

        self._token = None
        self._exp = None

    async def login(self):
        headers = {}
        headers[
            'Authorization'] = f'Basic {str(base64.b64encode((self.client_id + ":" + self.client_secret).encode("utf-8")), "utf-8")}'
        try:
            async with async_timeout.timeout(5, loop=self.loop):
                response = await self.session.post(data={"grant_type": "client_credentials"},
                                                   url=self.url,
                                                   headers=headers)
                body = {}
                if response.content_type == "application/json":
                    body = await response.json()
                else:
                    raise aiohttp.ClientError("Unexpected content type: got " + response.content_type)
                self._token = body['access_token']
                self._exp = time.time() + body['expires_in'] - self.renew_pad_secs
        except aiohttp.ClientError as error:
            LOGGER.error("Error fetching token for STIB/MVIB : %s", error)
        except asyncio.TimeoutError as error:
            LOGGER.debug("Timeout connecting to STIB/MVIB API: %s", error)

    def is_token_valid(self):
        return self._token and self._exp and time.time() < self._exp

    @property
    def token(self):
        return self._token


class AbstractSTIBAPIClient(ABC):
    @abstractmethod
    async def api_call(self, endpoint_suffix: str, additional_headers=None):
        pass


class STIBAPIClient(AbstractSTIBAPIClient):
    """A class for common functions."""

    def __init__(self,
                 loop: asyncio.events.AbstractEventLoop,
                 session: aiohttp.ClientSession,
                 client_id: str,
                 client_secret: str):
        """Initialize the class."""
        self.loop = loop
        self.session = session
        if self.session is None:
            self.session = aiohttp.ClientSession()
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_manager = OAuthTokenManager(self.loop, self.session,
                                               self.client_id, self.client_secret,
                                               API_BASE_URL + '/token', )

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        if self.token_manager.is_token_valid():
            return self.token_manager.token

        await self.token_manager.login()

        return self.token_manager.token

    async def api_call(self, endpoint_suffix: str, additional_headers=None):
        if additional_headers is None:
            additional_headers = {}

        """Call the API."""
        headers = {'Authorization': "Bearer " + await self.async_get_access_token()}
        headers.update(additional_headers)
        data = None
        try:
            async with async_timeout.timeout(5, loop=self.loop):
                LOGGER.debug("Endpoint URL: %s", str(endpoint_suffix))
                response = await self.session.get(url=API_BASE_URL + endpoint_suffix, headers=headers)
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
