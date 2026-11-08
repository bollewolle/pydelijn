"""Shared pytest fixtures for the pydelijn test suite."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

KERN_BASE_URL = "https://api.delijn.be/DLKernOpenData/api/v1"
ZOEK_BASE_URL = "https://api.delijn.be/DLZoekOpenData/v1"

STOP = "200552"
ENTITY = "2"
LINE = "335"

HALTE_URL = f"{KERN_BASE_URL}/haltes/{ENTITY}/{STOP}"
REALTIME_URL = (
    f"{KERN_BASE_URL}/haltes/{ENTITY}/{STOP}/real-time?maxAantalDoorkomsten=10"
)
LIJN_URL = f"{KERN_BASE_URL}/lijnen/{ENTITY}/{LINE}"
LIJNKLEUREN_URL = f"{KERN_BASE_URL}/lijnen/{ENTITY}/{LINE}/lijnkleuren"
KLEUREN_URL = f"{KERN_BASE_URL}/kleuren"
ZOEK_HALTES_URL = f"{ZOEK_BASE_URL}/zoek/haltes/Heizijde?maxAantalHits=10"
INDEBUURT_URL = (
    f"{KERN_BASE_URL}/haltes/indebuurt/51.054302,3.717425?maxAantalHaltes=10"
)


def load_fixture(name: str) -> dict[str, Any]:
    """Load and deep-copy a JSON fixture from tests/fixtures/<name>.json."""
    data = json.loads((FIXTURES_DIR / f"{name}.json").read_text())
    return cast("dict[str, Any]", copy.deepcopy(data))


@pytest.fixture
def halte() -> dict[str, Any]:
    """Core API Halte payload for stop 200552."""
    return load_fixture("halte")


@pytest.fixture
def halte_realtime() -> dict[str, Any]:
    """Core API HalteDoorkomsten payload: one realtime passage on line 335."""
    return load_fixture("halte_realtime")


@pytest.fixture
def lijn() -> dict[str, Any]:
    """Core API Lijn payload for line 335."""
    return load_fixture("lijn")


@pytest.fixture
def lijnkleuren() -> dict[str, Any]:
    """Core API LijnkleurCodes payload for line 335."""
    return load_fixture("lijnkleuren")


@pytest.fixture
def kleuren() -> dict[str, Any]:
    """Core API Lijnkleuren (colour code -> hex) payload."""
    return load_fixture("kleuren")


@pytest.fixture
def zoek_haltes() -> dict[str, Any]:
    """Search API HaltesHits payload."""
    return load_fixture("zoek_haltes")


@pytest.fixture
def haltes_indebuurt() -> dict[str, Any]:
    """Core API Punten payload (haltes/indebuurt)."""
    return load_fixture("haltes_indebuurt")
