from __future__ import annotations

import random
from typing import Any

from forge.core.plugin import Mode, Registry


@Registry.register_mode
class ScaleMode(Mode):
    name = "scale"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        if not records:
            return records
        target = kwargs.get("count", kwargs.get("target", len(records) * 10))
        if target <= len(records):
            return records[:target]
        result = list(records)
        while len(result) < target:
            row = random.choice(records)
            new_row = dict(row)
            for k, v in row.items():
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    noise = v * random.uniform(-0.05, 0.05)
                    new_row[k] = v + noise
            result.append(new_row)
        return result
