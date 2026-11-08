"""Async client for the De Lijn Core (Kern) and Search (Zoek) open data APIs."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from types import TracebackType
from typing import Any, Final
from urllib.parse import quote
from zoneinfo import ZoneInfo

import aiohttp

from .exceptions import (
    DeLijnAuthError,
    DeLijnConnectionError,
    DeLijnNotFoundError,
    DeLijnResponseError,
)
from .models import Line, Passage, Stop

_LOGGER = logging.getLogger(__name__)

_KERN_BASE_URL: Final = "https://api.delijn.be/DLKernOpenData/api/v1"
_ZOEK_BASE_URL: Final = "https://api.delijn.be/DLZoekOpenData/v1"
_BRUSSELS_TZ: Final = ZoneInfo("Europe/Brussels")
_TIMESTAMP_FORMAT: Final = "%Y-%m-%dT%H:%M:%S"


def _entity_number(number: str) -> str:
    """Return the entity number: the first character of a stop/line number."""
    return str(number)[:1]


def _parse_timestamp(value: str | None) -> datetime | None:
    """Parse a De Lijn timestamp into an aware datetime.

    Timestamps normally arrive as naive local strings in Europe/Brussels
    (``%Y-%m-%dT%H:%M:%S``), but offset-aware ISO strings are tolerated too.
    """
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        try:
            parsed = datetime.strptime(value, _TIMESTAMP_FORMAT)
        except ValueError:
            _LOGGER.debug("Could not parse timestamp: %s", value)
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_BRUSSELS_TZ)
    return parsed


def _parse_geo_coordinate(
    value: dict[str, Any] | str | None,
) -> tuple[float | None, float | None]:
    """Parse a geoCoordinaat value.

    The spec schema models it as ``{"latitude": ..., "longitude": ...}`` but
    some example payloads (and the "in de buurt" endpoint) render it as the
    string ``"lat,lon"``. Handle both defensively.
    """
    if isinstance(value, dict):
        latitude = value.get("latitude")
        longitude = value.get("longitude")
        try:
            return (
                float(latitude) if latitude is not None else None,
                float(longitude) if longitude is not None else None,
            )
        except (TypeError, ValueError):
            return None, None
    if isinstance(value, str):
        parts = value.split(",")
        if len(parts) == 2:
            try:
                return float(parts[0]), float(parts[1])
            except ValueError:
                return None, None
    return None, None


def _parse_stop(data: dict[str, Any]) -> Stop:
    """Parse a Core/Search API ``Halte`` object into a Stop."""
    latitude, longitude = _parse_geo_coordinate(data.get("geoCoordinaat"))
    return Stop(
        entity_number=str(data.get("entiteitnummer") or ""),
        number=str(data.get("haltenummer") or ""),
        name=str(data.get("omschrijving") or ""),
        municipality=data.get("omschrijvingGemeente"),
        latitude=latitude,
        longitude=longitude,
    )


def _parse_nearby_stop(data: dict[str, Any]) -> Stop:
    """Parse a nearby-stop object (from haltes/indebuurt) into a Stop.

    The OpenAPI spec models these as ``Punt`` objects, but the live API
    (verified 2026-08) returns ``Halte``-like objects with ``id``, ``naam``
    and ``afstand`` (distance in meters).
    """
    stop_number = str(data.get("id") or "")
    latitude, longitude = _parse_geo_coordinate(data.get("geoCoordinaat"))
    distance = data.get("afstand")
    return Stop(
        entity_number=_entity_number(stop_number) if stop_number else "",
        number=stop_number,
        name=str(data.get("naam") or ""),
        municipality=None,
        latitude=latitude,
        longitude=longitude,
        distance=int(distance) if distance is not None else None,
    )


def _hex_for(
    colour_code: dict[str, Any] | None, colour_map: dict[str, str]
) -> str | None:
    """Resolve a ``{"code": ...}`` colour reference to a ``#RRGGBB`` hex string."""
    if not colour_code:
        return None
    code = colour_code.get("code")
    if code is None:
        return None
    hex_value = colour_map.get(str(code))
    if not hex_value:
        return None
    return hex_value if hex_value.startswith("#") else f"#{hex_value}"


class DeLijnClient:
    """Async client for the De Lijn open data APIs.

    Raises typed exceptions from :mod:`pydelijn.exceptions` on failure.
    It never logs-and-swallows an error.
    """

    def __init__(
        self,
        api_key: str,
        session: aiohttp.ClientSession | None = None,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the client.

        Args:
            api_key: The ``Ocp-Apim-Subscription-Key`` for the De Lijn APIs.
            session: An existing aiohttp session to reuse. If omitted, a
                session is created lazily and closed again by ``close()``.
            request_timeout: Per-request timeout in seconds.
        """
        self._api_key = api_key
        self._session = session
        self._session_is_owned = session is None
        self._request_timeout = request_timeout
        self._line_cache: dict[tuple[str, str], Line] = {}
        self._colour_map: dict[str, str] | None = None

    async def __aenter__(self) -> DeLijnClient:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the async context manager, closing any owned session."""
        await self.close()

    async def close(self) -> None:
        """Close the client's own session, if it created one.

        A session that was injected by the caller is never closed here.
        """
        if self._session_is_owned and self._session is not None:
            await self._session.close()

    def _ensure_session(self) -> aiohttp.ClientSession:
        """Return the active session, creating an owned one if needed."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._session_is_owned = True
        return self._session

    async def _request(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the decoded JSON body."""
        session = self._ensure_session()
        headers = {"Ocp-Apim-Subscription-Key": self._api_key}
        try:
            async with asyncio.timeout(self._request_timeout):
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        try:
                            return await response.json(content_type=None)
                        except (ValueError, aiohttp.ContentTypeError) as err:
                            raise DeLijnResponseError(
                                "De Lijn API returned a response that isn't valid JSON"
                            ) from err
                    if response.status in (401, 403):
                        raise DeLijnAuthError(
                            "De Lijn API rejected the subscription key "
                            f"(HTTP {response.status})"
                        )
                    if response.status == 404:
                        raise DeLijnNotFoundError(
                            "The requested De Lijn resource was not found"
                        )
                    raise DeLijnResponseError(
                        f"De Lijn API returned an unexpected status: {response.status}"
                    )
        except TimeoutError as err:
            raise DeLijnConnectionError(
                "Timed out while waiting for the De Lijn API"
            ) from err
        except aiohttp.ClientError as err:
            raise DeLijnConnectionError(
                f"Error connecting to the De Lijn API: {err}"
            ) from err

    async def get_stop(self, stop_number: str) -> Stop:
        """Get information about a single stop by its stop number."""
        entity = _entity_number(stop_number)
        url = f"{_KERN_BASE_URL}/haltes/{entity}/{stop_number}"
        data = await self._request(url)
        return _parse_stop(data)

    async def search_stops(self, query: str, max_results: int = 10) -> list[Stop]:
        """Search for stops matching a free-text query."""
        url = f"{_ZOEK_BASE_URL}/zoek/haltes/{quote(query, safe='')}"
        data = await self._request(url, params={"maxAantalHits": max_results})
        return [_parse_stop(item) for item in data.get("haltes") or []]

    async def get_stops_near(
        self, latitude: float, longitude: float, max_results: int = 10
    ) -> list[Stop]:
        """Get stops near a given coordinate, ordered by distance.

        The spec names the response array "punten". The live API sends
        "haltes". Both keys are accepted.
        """
        url = f"{_KERN_BASE_URL}/haltes/indebuurt/{latitude},{longitude}"
        data = await self._request(url, params={"maxAantalHaltes": max_results})
        # The spec names the array "punten"; the live API sends "haltes".
        items = data.get("haltes") or data.get("punten") or []
        return [_parse_nearby_stop(item) for item in items]

    async def get_passages(
        self, stop_number: str, max_passages: int = 10
    ) -> list[Passage]:
        """Get the upcoming (realtime or scheduled) passages for a stop."""
        entity = _entity_number(stop_number)
        url = f"{_KERN_BASE_URL}/haltes/{entity}/{stop_number}/real-time"
        data = await self._request(url, params={"maxAantalDoorkomsten": max_passages})
        passages = []
        for halte_doorkomst in data.get("halteDoorkomsten") or []:
            for doorkomst in halte_doorkomst.get("doorkomsten") or []:
                passages.append(await self._parse_doorkomst(doorkomst))
        return passages

    async def _parse_doorkomst(self, doorkomst: dict[str, Any]) -> Passage:
        """Parse a single ``Doorkomst`` object into a Passage.

        The OpenAPI spec documents "doorkomstTijdstip" for the realtime
        timestamp, but the live API sends "real-timeTijdstip". Both keys
        are accepted.
        """
        entity = str(doorkomst.get("entiteitnummer") or "")
        line_number = str(doorkomst.get("lijnnummer") or "")
        line = await self._get_line(entity, line_number)

        due_at_schedule = _parse_timestamp(doorkomst.get("dienstregelingTijdstip"))

        # The OpenAPI spec documents "doorkomstTijdstip", but the live API
        # (verified 2026-08) sends "real-timeTijdstip". Accept both.
        realtime_value = doorkomst.get("doorkomstTijdstip") or doorkomst.get(
            "real-timeTijdstip"
        )
        due_at_realtime = _parse_timestamp(realtime_value)

        is_realtime, cancelled = self._parse_prediction_statuses(
            doorkomst.get("predictionStatussen")
        )
        if doorkomst.get("status") == "CANCELLED":
            cancelled = True

        vias = doorkomst.get("vias")
        if isinstance(vias, list):
            vias = ", ".join(str(via) for via in vias) or None
        elif vias is not None:
            vias = str(vias)

        return Passage(
            line=line,
            direction=doorkomst.get("richting"),
            destination=doorkomst.get("bestemming"),
            vias=vias,
            due_at_schedule=due_at_schedule,
            due_at_realtime=due_at_realtime,
            is_realtime=is_realtime,
            cancelled=cancelled,
            ride_number=doorkomst.get("ritnummer"),
            vehicle_number=doorkomst.get("vrtnum"),
        )

    @staticmethod
    def _parse_prediction_statuses(
        statuses: list[str] | str | None,
    ) -> tuple[bool, bool]:
        """Translate ``predictionStatussen`` into ``(is_realtime, cancelled)``."""
        if isinstance(statuses, str):
            statuses = [statuses]
        is_realtime = False
        cancelled = False
        for status in statuses or []:
            if status == "REALTIME":
                is_realtime = True
            elif status == "GEENREALTIME":
                is_realtime = False
            elif status == "GESCHRAPT":
                cancelled = True
            elif status == "VERSTREKEN":
                pass
            else:
                _LOGGER.debug("Unknown prediction status: %s", status)
        return is_realtime, cancelled

    async def _get_line(self, entity: str, number: str) -> Line:
        """Resolve a Line (with colours), using the per-client cache."""
        cache_key = (entity, number)
        if cache_key in self._line_cache:
            return self._line_cache[cache_key]

        line = await self._fetch_line(entity, number)
        self._line_cache[cache_key] = line
        return line

    async def _fetch_line(self, entity: str, number: str) -> Line:
        """Fetch line info and colours from the API.

        If the line or its colours can't be found, fall back to a minimal
        Line with just the numbers instead of failing the whole passage.
        """
        minimal = Line(entity_number=entity, number=number)
        try:
            line_data = await self._request(
                f"{_KERN_BASE_URL}/lijnen/{entity}/{number}"
            )
            colour_codes = await self._request(
                f"{_KERN_BASE_URL}/lijnen/{entity}/{number}/lijnkleuren"
            )
            colour_map = await self._get_colour_map()
        except DeLijnNotFoundError:
            return minimal

        public_number = line_data.get("lijnnummerPubliek")
        transport_type = line_data.get("vervoertype")

        return Line(
            entity_number=entity,
            number=number,
            public_number=str(public_number) if public_number is not None else None,
            description=line_data.get("omschrijving"),
            transport_type=(
                transport_type.lower() if isinstance(transport_type, str) else None
            ),
            colour_front_hex=_hex_for(colour_codes.get("voorgrond"), colour_map),
            colour_front_border_hex=_hex_for(
                colour_codes.get("voorgrondRand"), colour_map
            ),
            colour_back_hex=_hex_for(colour_codes.get("achtergrond"), colour_map),
            colour_back_border_hex=_hex_for(
                colour_codes.get("achtergrondRand"), colour_map
            ),
        )

    async def _get_colour_map(self) -> dict[str, str]:
        """Fetch and cache the colour code to hex mapping (fetched once).

        The OpenAPI spec names the array "lijnkleuren", but the live API
        sends "kleuren". Both keys are accepted.
        """
        if self._colour_map is None:
            data = await self._request(f"{_KERN_BASE_URL}/kleuren")
            colour_map: dict[str, str] = {}
            # The OpenAPI spec names the array "lijnkleuren", but the live API
            # (verified 2026-08) sends "kleuren". Accept both.
            for entry in data.get("lijnkleuren") or data.get("kleuren") or []:
                code = entry.get("code")
                hex_value = entry.get("hex")
                if code is not None and hex_value is not None:
                    colour_map[str(code)] = str(hex_value)
            self._colour_map = colour_map
        return self._colour_map
