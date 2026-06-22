from __future__ import annotations

import re
import uuid
import hashlib
from typing import Any

from forge.core.plugin import Mode, Registry
from forge.core.schema import DataType, Schema, infer_type


EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
PHONE_RE = re.compile(r"\+?[\d\s\-().]{7,20}")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
IP_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


@Registry.register_mode
class AnonymizeMode(Mode):
    name = "anonymize"

    def __init__(self):
        self._memo: dict[str, str] = {}

    def run(self, records: list[dict], **kwargs) -> list[dict]:
        columns = kwargs.get("columns")
        for record in records:
            for key in list(record.keys()):
                val = record[key]
                if val is None or not isinstance(val, str):
                    continue
                if columns and key not in columns:
                    continue
                record[key] = self._anonymize_value(val)
        return records

    def _anonymize_value(self, val: str) -> str:
        val = SSN_RE.sub(lambda m: self._token(m.group()), val)
        val = EMAIL_RE.sub(lambda m: self._anon_email(m.group()), val)
        val = PHONE_RE.sub(lambda m: self._token(m.group()), val)
        val = IP_RE.sub(lambda m: self._token(m.group()), val)
        return val

    def _anon_email(self, email: str) -> str:
        local, domain = email.split("@", 1)
        return f"{self._hash(local)}@{domain}"

    def _token(self, s: str) -> str:
        if s not in self._memo:
            self._memo[s] = str(uuid.uuid4())[:8]
        return self._memo[s]

    def _hash(self, s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()[:12]
