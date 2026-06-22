from __future__ import annotations

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any

from forge.core.plugin import Mode, Registry
from forge.core.schema import DataType, Schema


@Registry.register_mode
class SynthesizeMode(Mode):
    name = "synthesize"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        schema = Schema.infer(records)
        count = kwargs.get("count", len(records))
        return [self._generate_row(schema) for _ in range(count)]

    def _generate_row(self, schema) -> dict:
        row = {}
        for col in schema.columns:
            if col.nullable and random.random() < 0.05:
                row[col.name] = None
            else:
                row[col.name] = self._gen_value(col.dtype)
        return row

    def _gen_value(self, dtype: DataType) -> Any:
        gen = {
            DataType.STRING: lambda: random.choice(
                ["alpha", "beta", "gamma", "delta", "omega", "zeta", "theta"]
            ),
            DataType.INTEGER: lambda: random.randint(0, 1000),
            DataType.FLOAT: lambda: round(random.uniform(0, 1000), 2),
            DataType.BOOLEAN: lambda: random.choice([True, False]),
            DataType.DATE: lambda: (
                datetime(2020, 1, 1) + timedelta(days=random.randint(0, 2000))
            ).strftime("%Y-%m-%d"),
            DataType.DATETIME: lambda: (
                datetime(2020, 1, 1) + timedelta(seconds=random.randint(0, 63072000))
            ).isoformat(),
            DataType.EMAIL: lambda: (
                f"{random.choice(string.ascii_lowercase)}"
                f"{random.randint(1,999)}@example.com"
            ),
            DataType.PHONE: lambda: f"+1-555-{random.randint(100,999)}-{random.randint(1000,9999)}",
            DataType.URL: lambda: (
                f"https://example.com/{random.choice(string.ascii_lowercase)}"
            ),
            DataType.UUID: lambda: str(uuid.uuid4()),
            DataType.JSON: lambda: {},
            DataType.UNKNOWN: lambda: None,
        }
        return gen.get(dtype, lambda: None)()
