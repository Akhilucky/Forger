from __future__ import annotations

from forge.core.plugin import Mode, Registry


@Registry.register_mode
class ConvertMode(Mode):
    name = "convert"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        return records
