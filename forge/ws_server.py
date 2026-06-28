from __future__ import annotations

import asyncio
import json
from typing import Any

from forge.generator.engine import Engine


_engine = Engine()
_columns: list[dict] = []


def _parse_cols(cols_str: str | None) -> list[dict]:
    if not cols_str:
        return [{"name": "id", "type": "integer"}, {"name": "value", "type": "string"}]
    result = []
    for s in cols_str.split(","):
        s = s.strip()
        if ":" in s:
            n, t = s.split(":", 1)
            result.append({"name": n.strip(), "type": t.strip()})
        else:
            result.append({"name": s, "type": "string"})
    return result


async def stream_websocket(websocket, path: str = "/", interval: float = 1.0,
                            columns: list[dict] | None = None):
    global _engine, _columns
    if columns:
        _columns = columns
    if not _columns:
        _columns = _parse_cols(None)

    try:
        while True:
            records = _engine.generate_from_spec(_columns, 1)
            data = {"event": "data", "record": records[0] if records else {},
                    "timestamp": __import__("datetime").datetime.now().isoformat()}
            await websocket.send(json.dumps(data, default=str))
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


def start_ws_server(host: str = "0.0.0.0", port: int = 8765,
                     columns: list[dict] | None = None,
                     interval: float = 1.0):
    try:
        import websockets
    except ImportError:
        raise ImportError("websockets required. pip install websockets")

    global _columns
    if columns:
        _columns = columns

    async def handler(websocket):
        await stream_websocket(websocket, interval=interval, columns=_columns)

    print(f"⚡ Forge WebSocket stream on ws://{host}:{port}")
    print(f"   Streams 1 record every {interval}s")
    print(f"   Press Ctrl+C to stop")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        websockets.serve(handler, host, port)
    )
    loop.run_forever()
