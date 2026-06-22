from __future__ import annotations

import random
from typing import Any

from forge.core.plugin import Mode, Registry


@Registry.register_mode
class CompressMode(Mode):
    name = "compress"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        if not records:
            return records
        target = kwargs.get("count", kwargs.get("target", max(1, len(records) // 10)))
        if target >= len(records):
            return records
        sampled = random.sample(records, target)
        return sampled
