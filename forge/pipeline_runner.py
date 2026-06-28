from __future__ import annotations

import os
from typing import Any

from forge.core.pipeline import Pipeline


def run_pipeline(path: str) -> list[dict]:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml required for YAML pipelines. pip install forge[yaml]")
        with open(path) as f:
            config = yaml.safe_load(f)
    else:
        import json as j
        with open(path) as f:
            config = j.load(f)

    if not config:
        raise ValueError(f"Empty pipeline config: {path}")

    steps = config if isinstance(config, list) else config.get("steps", [config])
    records = []
    final_dest = None

    for step in steps:
        source = step.get("source") or step.get("read")
        destination = step.get("destination") or step.get("write")
        mode = step.get("mode") or step.get("transform")
        source_fmt = step.get("from_format") or step.get("source_format")
        dest_fmt = step.get("to_format") or step.get("dest_format")
        kwargs = {k: v for k, v in step.items()
                  if k not in ("source", "read", "destination", "write",
                               "mode", "transform", "from_format", "to_format",
                               "source_format", "dest_format")}

        pipe = Pipeline()
        if records:
            pipe._records = records

        if source:
            pipe.read(source, source_fmt, **{k: v for k, v in kwargs.items()
                                             if k in ("table", "sheet")})

        if mode:
            pipe.apply(mode, **kwargs)

        if destination:
            pipe.write(destination, dest_fmt)
            final_dest = destination

        records = pipe.run()
        if source:
            click_echo(f"  read {source} ({len(records)} records)")
        if mode:
            click_echo(f"  apply {mode}")
        if destination:
            click_echo(f"  write → {destination}")

    return records


def click_echo(msg: str):
    try:
        import click
        click.echo(f"  {msg}")
    except ImportError:
        print(f"  {msg}")
