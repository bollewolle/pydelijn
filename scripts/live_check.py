"""Live smoke test against the real De Lijn API.

Usage:
    DELIJN_API_KEY=<subscription key> python scripts/live_check.py [stop_number]

Verifies the open questions from the v2 rewrite against reality:
which realtime timestamp key the API sends, the /kleuren array key,
and that search + nearby + passages round-trip cleanly.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydelijn import DeLijnClient

DEFAULT_STOP = "200552"


async def main() -> int:
    """Run the live checks. Return a process exit code."""
    api_key = os.environ.get("DELIJN_API_KEY")
    if not api_key:
        print("Set DELIJN_API_KEY in the environment first.")
        return 1
    stop_number: str = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STOP

    async with aiohttp.ClientSession() as session:
        client = DeLijnClient(api_key, session=session)

        raw_url = (
            "https://api.delijn.be/DLKernOpenData/api/v1/"
            f"haltes/{stop_number[:1]}/{stop_number}/real-time"
        )
        async with session.get(
            raw_url, headers={"Ocp-Apim-Subscription-Key": api_key}
        ) as resp:
            raw: dict[str, Any] = await resp.json()
        doorkomsten: list[dict[str, Any]] = [
            d
            for h in raw.get("halteDoorkomsten") or []
            for d in h.get("doorkomsten") or []
        ]
        if doorkomsten:
            keys: set[str] = set(doorkomsten[0])
            print(f"raw doorkomst keys: {sorted(keys)}")
            for candidate in ("doorkomstTijdstip", "real-timeTijdstip"):
                print(f"  {candidate}: {'PRESENT' if candidate in keys else 'absent'}")
        else:
            print("no doorkomsten right now (quiet stop or late hour)")
            print(f"  raw response keys: {sorted(raw)}")
            print(f"  raw response head: {str(raw)[:400]}")

        async with session.get(
            "https://api.delijn.be/DLKernOpenData/api/v1/kleuren",
            headers={"Ocp-Apim-Subscription-Key": api_key},
        ) as resp:
            kleuren_raw: dict[str, Any] = await resp.json()
        print(f"/kleuren top-level keys: {sorted(kleuren_raw)}")

        stop = await client.get_stop(stop_number)
        print(f"stop: {stop.name}, {stop.municipality} ({stop.number})")

        passages = await client.get_passages(stop_number, max_passages=5)
        for p in passages:
            rt: str = "realtime" if p.is_realtime else "schedule"
            flag: str = " CANCELLED" if p.cancelled else ""
            number: str = p.line.public_number or p.line.number
            print(
                f"  {p.line.transport_type or '?'} {number}"
                f" -> {p.destination}: {p.due_at:%H:%M} ({rt}){flag}"
            )

        results = await client.search_stops("Gent Sint-Pieters", max_results=3)
        found: list[str] = [f"{s.name} ({s.number})" for s in results]
        print(f"search 'Gent Sint-Pieters': {found}")

    print("live check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
