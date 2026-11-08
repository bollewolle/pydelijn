"""Tests for HTTP-status and transport-failure mapping to typed exceptions."""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from pydelijn import DeLijnClient
from pydelijn.exceptions import (
    DeLijnAuthError,
    DeLijnConnectionError,
    DeLijnNotFoundError,
    DeLijnResponseError,
)
from tests.conftest import HALTE_URL, STOP


async def test_401_raises_auth_error() -> None:
    """A 401 response raises DeLijnAuthError, not a generic error."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, status=401)
        async with DeLijnClient("bad-key") as client:
            with pytest.raises(DeLijnAuthError) as exc_info:
                await client.get_stop(STOP)

    message = str(exc_info.value)
    assert "bad-key" not in message


async def test_403_raises_auth_error() -> None:
    """A 403 response also raises DeLijnAuthError."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, status=403)
        async with DeLijnClient("bad-key") as client:
            with pytest.raises(DeLijnAuthError):
                await client.get_stop(STOP)


async def test_404_raises_not_found_error() -> None:
    """A 404 response raises DeLijnNotFoundError for an unknown stop."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, status=404)
        async with DeLijnClient("fake-key") as client:
            with pytest.raises(DeLijnNotFoundError):
                await client.get_stop(STOP)


async def test_unexpected_status_raises_response_error() -> None:
    """Any other non-200 status raises DeLijnResponseError."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, status=500)
        async with DeLijnClient("fake-key") as client:
            with pytest.raises(DeLijnResponseError):
                await client.get_stop(STOP)


async def test_timeout_raises_connection_error() -> None:
    """A timeout while calling the API raises DeLijnConnectionError."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, exception=TimeoutError())
        async with DeLijnClient("fake-key") as client:
            with pytest.raises(DeLijnConnectionError):
                await client.get_stop(STOP)


async def test_client_error_raises_connection_error() -> None:
    """An aiohttp.ClientError while calling the API raises DeLijnConnectionError."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, exception=aiohttp.ClientConnectionError("boom"))
        async with DeLijnClient("fake-key") as client:
            with pytest.raises(DeLijnConnectionError):
                await client.get_stop(STOP)


async def test_malformed_json_raises_response_error() -> None:
    """A non-JSON response body raises DeLijnResponseError."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, body="not json at all", status=200)
        async with DeLijnClient("fake-key") as client:
            with pytest.raises(DeLijnResponseError):
                await client.get_stop(STOP)


async def test_no_secrets_in_exception_messages() -> None:
    """Exception messages never contain the URL or the subscription key."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, status=401)
        async with DeLijnClient("super-secret-key") as client:
            with pytest.raises(DeLijnAuthError) as exc_info:
                await client.get_stop(STOP)

    message = str(exc_info.value)
    assert "super-secret-key" not in message
    assert "Ocp-Apim-Subscription-Key" not in message
    assert HALTE_URL not in message
