from __future__ import annotations

import csv
import json
import os
import time
from typing import Any, Iterator

from forge.generator.engine import Engine
from forge.generator.inference import ColumnProfile, guess_field_type
from forge.generator.fields import generate as gen_field


def estimate_row_size(columns: list[dict], sample: list[dict] | None = None) -> int:
    engine = Engine()
    if sample:
        engine.learn(sample)
    row = {}
    for col in columns:
        name = col["name"]
        profile = next((p for p in engine.profiles if p.name == name), None)
        if profile:
            row[name] = gen_field(profile.pattern, profile.hint, profile.distribution, name)
        else:
            hint = guess_field_type(name)
            row[name] = gen_field(None, hint, None, name)
    total = sum(len(str(v)) + 2 for v in row.values())
    return max(total, 50)


def stream_rows(columns: list[dict], count: int,
                 sample: list[dict] | None = None) -> Iterator[dict]:
    engine = Engine()
    if sample:
        engine.learn(sample)
    profile_map = {p.name: p for p in engine.profiles}
    for _ in range(count):
        row = {}
        for col in columns:
            name = col["name"]
            if name in profile_map:
                p = profile_map[name]
                row[name] = gen_field(p.pattern, p.hint, p.distribution, name)
            else:
                hint = guess_field_type(name)
                row[name] = gen_field(None, hint, None, name)
        yield row


def stream_to_csv(columns: list[dict], destination: str, count: int,
                   sample: list[dict] | None = None,
                   progress: bool = False) -> int:
    written = 0
    with open(destination, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([c["name"] for c in columns])
        for row in stream_rows(columns, count, sample):
            writer.writerow([row.get(c["name"], "") for c in columns])
            written += 1
            if progress and written % 100000 == 0:
                size_mb = os.path.getsize(destination) / (1024 * 1024)
                print(f"  {written:,} rows ({size_mb:.1f} MB)", flush=True)
    return written


def stream_to_ndjson(columns: list[dict], destination: str, count: int,
                      sample: list[dict] | None = None,
                      progress: bool = False) -> int:
    written = 0
    with open(destination, "w") as f:
        for row in stream_rows(columns, count, sample):
            f.write(json.dumps(row, default=str) + "\n")
            written += 1
            if progress and written % 100000 == 0:
                size_mb = os.path.getsize(destination) / (1024 * 1024)
                print(f"  {written:,} rows ({size_mb:.1f} MB)", flush=True)
    return written


def stream_to_sql(columns: list[dict], destination: str, count: int,
                   sample: list[dict] | None = None,
                   table: str = "data",
                   progress: bool = False) -> int:
    written = 0
    col_names = [c["name"] for c in columns]
    with open(destination, "w") as f:
        f.write(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_names)});\n")
        for row in stream_rows(columns, count, sample):
            vals = []
            for c in col_names:
                v = row.get(c)
                if v is None:
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                else:
                    vals.append("'" + str(v).replace("'", "''") + "'")
            f.write(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({', '.join(vals)});\n")
            written += 1
            if progress and written % 10000 == 0:
                size_mb = os.path.getsize(destination) / (1024 * 1024)
                print(f"  {written:,} rows ({size_mb:.1f} MB)", flush=True)
    return written


def stream_to_format(columns: list[dict], destination: str, count: int,
                      fmt: str = "csv",
                      sample: list[dict] | None = None,
                      progress: bool = False) -> int:
    fmt = fmt.lower()
    if fmt == "csv":
        return stream_to_csv(columns, destination, count, sample, progress)
    elif fmt == "ndjson":
        return stream_to_ndjson(columns, destination, count, sample, progress)
    elif fmt == "sql":
        return stream_to_sql(columns, destination, count, sample, progress=progress)
    else:
        raise ValueError(f"Streaming not supported for format: {fmt}. Use csv, ndjson, or sql.")


def generate_huge(columns: list[dict], destination: str,
                   target_size: str = "1GB",
                   fmt: str = "csv",
                   sample: list[dict] | None = None,
                   progress: bool = True) -> int:
    size_units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    target_size = target_size.upper().strip()
    if target_size[-2:] in size_units:
        size_num = float(target_size[:-2])
        size_unit = target_size[-2:]
    elif target_size[-1] in size_units:
        size_num = float(target_size[:-1])
        size_unit = target_size[-1:]
    else:
        size_num = float(target_size)
        size_unit = "B"
    target_bytes = int(size_num * size_units[size_unit])

    est = estimate_row_size(columns, sample)
    est_count = max(1, target_bytes // est)

    if progress:
        print(f"Target: {target_size} ≈ {est_count:,} rows (est. {est} bytes/row)", flush=True)

    start = time.time()
    written = stream_to_format(columns, destination, est_count, fmt, sample, progress)
    elapsed = time.time() - start
    final_size = os.path.getsize(destination)
    actual = final_size / (1024 * 1024)

    if progress:
        print(f"\n✓ {written:,} rows, {actual:.1f} MB in {elapsed:.1f}s", flush=True)
        print(f"  {written/elapsed:.0f} rows/s", flush=True)

    return written
