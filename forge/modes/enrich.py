from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from forge.core.plugin import Mode, Registry


@Registry.register_mode
class EnrichMode(Mode):
    name = "enrich"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        for record in records:
            record["_id"] = self._make_id(record)
            record["_updated_at"] = datetime.now(timezone.utc).isoformat()
            record["_checksum"] = self._checksum(record)
        return records

    def _make_id(self, record: dict) -> str:
        vals = [str(v) for v in record.values() if v is not None]
        key = "".join(vals) if vals else str(datetime.now(timezone.utc).timestamp())
        return hashlib.md5(key.encode()).hexdigest()

    def _checksum(self, record: dict) -> str:
        return hashlib.sha256(str(record).encode()).hexdigest()[:16]
