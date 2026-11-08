# pydelijn

[![Build Status](https://github.com/bollewolle/pydelijn/actions/workflows/ci.yml/badge.svg)](https://github.com/bollewolle/pydelijn/actions/workflows/ci.yml)

An async, fully typed Python client for the De Lijn (Flemish public
transport) open data API. It retrieves stops, lines, and realtime/scheduled
passages.

Its primary purpose is to feed the De Lijn integration in Home Assistant.

**Important**: a developer account at https://data.delijn.be is required to
generate a subscription key for the Core and Search open data APIs.

> **v2 is a breaking rewrite.** The old dict-based `pydelijn.api.Passages`
> API is gone, replaced by `DeLijnClient` with typed models and exceptions.
> Docs for v1 are available in the git history.

## Install

```bash
pip install pydelijn
```

## Usage

```python
import asyncio

from pydelijn import DeLijnClient
from pydelijn.exceptions import DeLijnError


async def main() -> None:
    api_key = "<your data.delijn.be subscription key>"

    async with DeLijnClient(api_key) as client:
        stops = await client.search_stops("Antwerpen Rooseveltplaats")
        stop = stops[0]

        passages = await client.get_passages(stop.number, max_passages=5)
        for passage in passages:
            print(
                f"Line {passage.line.public_number} to {passage.destination}: "
                f"due at {passage.due_at} (realtime={passage.is_realtime})"
            )


asyncio.run(main())
```

Errors are raised as typed exceptions (`DeLijnConnectionError`,
`DeLijnAuthError`, `DeLijnNotFoundError`, `DeLijnResponseError`, all
subclasses of `DeLijnError`) rather than logged and swallowed, so callers
(e.g. a Home Assistant `DataUpdateCoordinator`) can react to failures.

You may pass in your own `aiohttp.ClientSession`; if you don't, one is
created lazily and closed by `client.close()` (or on exiting `async with`).

## Development

Install test dependencies:

```bash
pip install -e '.[test]'
```

Run checks:

```bash
ruff check .
ruff format --check .
mypy pydelijn/ tests/ scripts/
pytest tests/ -q
```

Type checking runs with `mypy --strict` across the package, tests, and
scripts. The `aiohttp<3.14` pin in the test dependencies exists because
aioresponses 0.7.9 mocks `aiohttp.ClientResponse.__init__()` and breaks
against aiohttp 3.14+, which added a required `stream_writer` kwarg. The
runtime dependency stays unbounded.

### Live check

`scripts/live_check.py` smoke-tests the client against the real API. Set
`DELIJN_API_KEY` in the environment first:

```bash
DELIJN_API_KEY=<subscription key> python scripts/live_check.py [stop_number]
```
