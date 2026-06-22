from __future__ import annotations

import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Any


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    UUID = "uuid"
    JSON = "json"
    UNKNOWN = "unknown"


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
URL_PATTERN = re.compile(r"^https?://\S+$")
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
PHONE_PATTERN = re.compile(r"^\+?[\d\s\-().]{7,20}$")


def infer_type(value: Any) -> DataType:
    if value is None:
        return DataType.UNKNOWN
    if isinstance(value, bool):
        return DataType.BOOLEAN
    if isinstance(value, int):
        return DataType.INTEGER
    if isinstance(value, float):
        return DataType.FLOAT
    if isinstance(value, datetime):
        return DataType.DATETIME
    if isinstance(value, dict | list):
        return DataType.JSON
    s = str(value)
    if UUID_PATTERN.match(s):
        return DataType.UUID
    if EMAIL_PATTERN.match(s):
        return DataType.EMAIL
    if URL_PATTERN.match(s):
        return DataType.URL
    if PHONE_PATTERN.match(s):
        return DataType.PHONE
    try:
        int(s)
        return DataType.INTEGER
    except ValueError:
        pass
    try:
        float(s)
        return DataType.FLOAT
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            datetime.strptime(s[:10], fmt)
            return DataType.DATE
        except ValueError:
            pass
    return DataType.STRING


class ColumnSchema:
    def __init__(self, name: str, dtype: DataType, nullable: bool = True):
        self.name = name
        self.dtype = dtype
        self.nullable = nullable

    def to_dict(self) -> dict:
        return {"name": self.name, "type": self.dtype.value, "nullable": self.nullable}


class Schema:
    def __init__(self, columns: list[ColumnSchema] | None = None):
        self.columns = columns or []

    def add_column(self, col: ColumnSchema) -> None:
        self.columns.append(col)

    def to_dict(self) -> list[dict]:
        return [c.to_dict() for c in self.columns]

    @classmethod
    def infer(cls, records: list[dict]) -> Schema:
        schema = cls()
        if not records:
            return schema
        col_names = set()
        for r in records:
            col_names.update(r.keys())
        for name in col_names:
            types = [infer_type(r.get(name)) for r in records if r.get(name) is not None]
            nullable = any(name not in r or r[name] is None for r in records)
            dtype = _dominant_type(types) if types else DataType.UNKNOWN
            schema.add_column(ColumnSchema(name, dtype, nullable))
        return schema


def _dominant_type(types: list[DataType]) -> DataType:
    type_score = {
        DataType.EMAIL: 10,
        DataType.URL: 9,
        DataType.PHONE: 8,
        DataType.UUID: 7,
        DataType.DATETIME: 6,
        DataType.DATE: 5,
        DataType.BOOLEAN: 4,
        DataType.INTEGER: 3,
        DataType.FLOAT: 2,
        DataType.STRING: 1,
        DataType.JSON: 0,
        DataType.UNKNOWN: -1,
    }
    return max(set(types), key=lambda t: (sum(1 for x in types if x == t), type_score.get(t, 0)))
