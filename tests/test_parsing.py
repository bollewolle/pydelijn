"""Tests for doorkomst parsing edge cases."""

from __future__ import annotations

from typing import Any, cast

from aioresponses import aioresponses

from pydelijn import DeLijnClient
from tests.conftest import (
    ENTITY,
    KLEUREN_URL,
    LIJN_URL,
    LIJNKLEUREN_URL,
    LINE,
    REALTIME_URL,
    STOP,
)


def _doorkomst(halte_realtime: dict[str, Any]) -> dict[str, Any]:
    return cast(
        "dict[str, Any]",
        halte_realtime["halteDoorkomsten"][0]["doorkomsten"][0],
    )


async def test_doorkomst_timestamp_fallback_to_legacy_key(
    halte_realtime: dict[str, Any],
    lijn: dict[str, Any],
    lijnkleuren: dict[str, Any],
    kleuren: dict[str, Any],
) -> None:
    """DoorkomstTijdstip missing falls back to the legacy real-timeTijdstip key."""
    doorkomst = _doorkomst(halte_realtime)
    del doorkomst["doorkomstTijdstip"]
    doorkomst["real-timeTijdstip"] = "2026-08-06T14:07:00"

    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, payload=lijn)
        mocked.get(LIJNKLEUREN_URL, payload=lijnkleuren)
        mocked.get(KLEUREN_URL, payload=kleuren)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)

    assert passages[0].due_at_realtime is not None
    assert passages[0].due_at_realtime.hour == 14
    assert passages[0].due_at_realtime.minute == 7


async def test_geschrapt_status_marks_cancelled(
    halte_realtime: dict[str, Any],
    lijn: dict[str, Any],
    lijnkleuren: dict[str, Any],
    kleuren: dict[str, Any],
) -> None:
    """A GESCHRAPT prediction status marks the passage as cancelled."""
    doorkomst = _doorkomst(halte_realtime)
    doorkomst["predictionStatussen"] = ["GESCHRAPT"]
    doorkomst.pop("status", None)

    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, payload=lijn)
        mocked.get(LIJNKLEUREN_URL, payload=lijnkleuren)
        mocked.get(KLEUREN_URL, payload=kleuren)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)

    assert passages[0].cancelled is True


async def test_top_level_status_cancelled_marks_cancelled(
    halte_realtime: dict[str, Any],
    lijn: dict[str, Any],
    lijnkleuren: dict[str, Any],
    kleuren: dict[str, Any],
) -> None:
    """A top-level status of CANCELLED marks the passage as cancelled."""
    doorkomst = _doorkomst(halte_realtime)
    doorkomst["predictionStatussen"] = ["REALTIME"]
    doorkomst["status"] = "CANCELLED"

    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, payload=lijn)
        mocked.get(LIJNKLEUREN_URL, payload=lijnkleuren)
        mocked.get(KLEUREN_URL, payload=kleuren)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)

    assert passages[0].cancelled is True
    assert passages[0].is_realtime is True


async def test_geenrealtime_falls_back_to_schedule_time(
    halte_realtime: dict[str, Any],
    lijn: dict[str, Any],
    lijnkleuren: dict[str, Any],
    kleuren: dict[str, Any],
) -> None:
    """GEENREALTIME means is_realtime is False and due_at uses the schedule time."""
    doorkomst = _doorkomst(halte_realtime)
    doorkomst["predictionStatussen"] = ["GEENREALTIME"]
    doorkomst.pop("status", None)
    del doorkomst["doorkomstTijdstip"]

    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, payload=lijn)
        mocked.get(LIJNKLEUREN_URL, payload=lijnkleuren)
        mocked.get(KLEUREN_URL, payload=kleuren)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)

    passage = passages[0]
    assert passage.is_realtime is False
    assert passage.due_at_realtime is None
    assert passage.due_at == passage.due_at_schedule


async def test_line_lookup_404_returns_minimal_line(
    halte_realtime: dict[str, Any],
) -> None:
    """A 404 on the line lookup still returns the passage, with a bare Line."""
    with aioresponses() as mocked:
        mocked.get(REALTIME_URL, payload=halte_realtime)
        mocked.get(LIJN_URL, status=404)

        async with DeLijnClient("fake-key") as client:
            passages = await client.get_passages(STOP)

    assert len(passages) == 1
    line = passages[0].line
    assert line.entity_number == ENTITY
    assert line.number == LINE
    assert line.public_number is None
    assert line.description is None
    assert line.transport_type is None
    assert line.colour_front_hex is None
    assert line.colour_front_border_hex is None
    assert line.colour_back_hex is None
    assert line.colour_back_border_hex is None
