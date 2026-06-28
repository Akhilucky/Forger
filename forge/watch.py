from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

from forge.core.pipeline import Pipeline


def watch_file(
    source: str,
    callback: Callable,
    interval: float = 5.0,
    once: bool = False,
):
    path = Path(source)
    if not path.exists():
        print(f"✗ File not found: {source}")
        return

    last_mtime = path.stat().st_mtime

    if once:
        callback()
        return

    print(f"👀 Watching {source} (every {interval}s)... Ctrl+C to stop")
    try:
        while True:
            time.sleep(interval)
            if path.exists():
                mtime = path.stat().st_mtime
                if mtime != last_mtime:
                    last_mtime = mtime
                    print(f"⚡ {path.name} changed, processing...")
                    callback()
    except KeyboardInterrupt:
        print("\n✗ Stopped")


def watch_and_process(
    source: str,
    destination: str,
    mode: str | None = None,
    interval: float = 5.0,
):
    def process():
        try:
            pipe = Pipeline()
            pipe.read(str(source))
            if mode:
                pipe.apply(mode)
            pipe.write(str(destination))
            print(f"  ✓ → {destination}")
        except Exception as e:
            print(f"  ✗ {e}")

    watch_file(source, process, interval)
