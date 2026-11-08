"""Tests for DeLijnClient: happy paths, caching, session lifecycle."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp
from aioresponses import aioresponses

from pydelijn import DeLijnClient
from tests.conftest import (
    ENTITY,
    HALTE_URL,
    INDEBUURT_URL,
    KLEUREN_URL,
    LIJN_URL,
    LIJNKLEUREN_URL,
    LINE,
    REALTIME_URL,
    STOP,
    ZOEK_HALTES_URL,
)

BRUSSELS = ZoneInfo("Europe/Brussels")


async def test_get_stop(halte: dict[str, Any]) -> None:
    """get_stop parses a Halte payload into a Stop."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, payload=halte)
        async with DeLijnClient("fake-key") as client:
            stop = await client.get_stop(STOP)

    assert stop.entity_number == ENTITY
    assert stop.number == STOP
    assert stop.name == "Heizijde"
    assert stop.municipality == "Gent"
    assert stop.latitude == 51.054302
    assert stop.longitude == 3.717425


async def test_get_passages_happy_path_and_caching(
    halte_realtime: dict[str, Any],
    lijn: dict[str, Any],
    lijnkleuren: dict[str, Any],
    kleuren: dict[str, Any],
) -> None:
    """Realtime and schedule times parse to aware datetimes. Line and colours resolve.

    The line, colour-code, and colour-map endpoints are each registered only
    once, while the real-time endpoint is registered twice: if the client
    fails to cache line/colour lookups across the two get_passages() calls,
    aioresponses raises a connection error for the unmatched third request.
    """
    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, payload=lijn)
        mocked.get(LIJNKLEUREN_URL, payload=lijnkleuren)
        mocked.get(KLEUREN_URL, payload=kleuren)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)
            assert len(passages) == 1
            passage = passages[0]

            assert passage.line.entity_number == ENTITY
            assert passage.line.number == LINE
            assert passage.line.public_number == "35"
            assert passage.line.description == "Gent - Wondelgem"
            assert passage.line.transport_type == "bus"
            assert passage.line.colour_front_hex == "#FFFFFF"
            assert passage.line.colour_back_hex == "#006464"
            assert passage.line.colour_front_border_hex == "#FFFFFF"
            assert passage.line.colour_back_border_hex == "#000000"

            assert passage.direction == "HEEN"
            assert passage.destination == "GENT STATION"
            assert passage.vias == "VIA WONDELGEM"
            assert passage.ride_number == "44"
            assert passage.vehicle_number == "521684"
            assert passage.is_realtime is True
            assert passage.cancelled is False

            assert passage.due_at_schedule == datetime(
                2026, 8, 6, 14, 5, 0, tzinfo=BRUSSELS
            )
            assert passage.due_at_realtime == datetime(
                2026, 8, 6, 14, 7, 0, tzinfo=BRUSSELS
            )
            assert passage.due_at == passage.due_at_realtime

            # Second call must reuse the cached Line (and not touch the
            # single-use line/colour mocks again).
            second_passages = await client.get_passages(STOP)
            assert second_passages[0].line == passage.line


async def test_search_stops(zoek_haltes: dict[str, Any]) -> None:
    """search_stops parses a HaltesHits payload into a list of Stops."""
    with aioresponses() as mocked:
        mocked.get(ZOEK_HALTES_URL, payload=zoek_haltes)
        async with DeLijnClient("fake-key") as client:
            stops = await client.search_stops("Heizijde")

    assert len(stops) == 1
    stop = stops[0]
    assert stop.number == STOP
    assert stop.entity_number == ENTITY
    assert stop.name == "Heizijde"
    assert stop.municipality == "Gent"
    # geoCoordinaat arrives as a "lat,lon" string from the search API.
    assert stop.latitude == 51.054302
    assert stop.longitude == 3.717425


async def test_get_stops_near(haltes_indebuurt: dict[str, Any]) -> None:
    """get_stops_near parses a live-style haltes payload into Stops."""
    with aioresponses() as mocked:
        mocked.get(INDEBUURT_URL, payload=haltes_indebuurt)
        async with DeLijnClient("fake-key") as client:
            stops = await client.get_stops_near(51.054302, 3.717425)

    assert len(stops) == 1
    stop = stops[0]
    assert stop.number == STOP
    assert stop.entity_number == ENTITY
    assert stop.name == "Gent Heizijde"
    assert stop.latitude == 51.054302
    assert stop.longitude == 3.717425
    assert stop.distance == 42


async def test_injected_session_is_not_closed(halte: dict[str, Any]) -> None:
    """close() must never close a session the caller injected."""
    session = aiohttp.ClientSession()
    try:
        with aioresponses() as mocked:
            mocked.get(HALTE_URL, payload=halte)
            client = DeLijnClient("fake-key", session=session)
            await client.get_stop(STOP)
            await client.close()
        assert session.closed is False
    finally:
        await session.close()


async def test_self_created_session_is_closed(halte: dict[str, Any]) -> None:
    """close() must close a session the client created for itself."""
    with aioresponses() as mocked:
        mocked.get(HALTE_URL, payload=halte)
        client = DeLijnClient("fake-key")
        await client.get_stop(STOP)
        await client.close()
        assert client._session is not None
        assert client._session.closed is True
