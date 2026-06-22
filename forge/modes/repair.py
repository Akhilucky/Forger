from __future__ import annotations

from typing import Any

from forge.core.plugin import Mode, Registry
from forge.core.schema import Schema, DataType


@Registry.register_mode
class RepairMode(Mode):
    name = "repair"

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        schema = Schema.infer(records)
        col_map = {c.name: c for c in schema.columns}
        for record in records:
            for key in list(record.keys()):
                val = record.get(key)
                col = col_map.get(key)
                if col:
                    if val is None or (isinstance(val, str) and val.strip() == ""):
                        record[key] = self._default_for_type(col.dtype)
                    elif isinstance(val, str):
                        record[key] = self._coerce(val, col.dtype)
                elif val is None:
                    record[key] = self._default_for_type(DataType.UNKNOWN)
        return records

    def _default_for_type(self, dtype: DataType) -> Any:
        defaults = {
            DataType.STRING: "",
            DataType.INTEGER: 0,
            DataType.FLOAT: 0.0,
            DataType.BOOLEAN: False,
            DataType.DATE: "1970-01-01",
            DataType.DATETIME: "1970-01-01T00:00:00",
            DataType.EMAIL: "",
            DataType.PHONE: "",
            DataType.URL: "",
            DataType.UUID: "00000000-0000-0000-0000-000000000000",
        }
        return defaults.get(dtype, "")

    def _coerce(self, val: str, dtype: DataType) -> Any:
        try:
            if dtype == DataType.INTEGER:
                return int(val)
            if dtype == DataType.FLOAT:
                return float(val)
            if dtype == DataType.BOOLEAN:
                return val.lower() in ("true", "1", "yes", "y")
        except (ValueError, TypeError):
            pass
        val = val.strip().strip("\"'")
        return val
