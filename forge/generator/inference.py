from __future__ import annotations

import re
import statistics
from collections import Counter
from datetime import datetime
from typing import Any

from forge.core.schema import DataType, infer_type


FIELD_HINTS = {
    "name": r"\b(name|first.name|last.name|fullname|full_name|user|login)\b",
    "email": r"\b(email|e-mail|mail|contact)\b",
    "phone": r"\b(phone|telephone|mobile|cell|contact_no|phone_number)\b",
    "address": r"\b(address|street|location|venue|place)\b",
    "city": r"\b(city|town|municipality|locality)\b",
    "state": r"\b(state|province|region|territory)\b",
    "country": r"\b(country|nation)\b",
    "zip": r"\b(zip|postal|pincode|postcode|zipcode)\b",
    "company": r"\b(company|organization|org|business|firm|employer)\b",
    "job": r"\b(job|title|position|role|occupation|profession)\b",
    "id": r"\b(id|identifier|uuid|guid|key|pk|primary_key)\b",
    "url": r"\b(url|link|website|site|web)\b",
    "price": r"\b(price|cost|amount|fee|salary|revenue|total|charge)\b",
    "age": r"\b(age|years_old)\b",
    "date": r"\b(date|created_at|updated_at|timestamp|time|birth|dob)\b",
    "description": r"\b(description|comment|note|detail|summary|text|content|bio|about)\b",
    "category": r"\b(category|type|kind|class|group|status|tag|label)\b",
    "gender": r"\b(gender|sex)\b",
}


def guess_field_type(name: str) -> str | None:
    lower = name.lower().replace("_", " ").replace("-", " ")
    for field_type, pattern in FIELD_HINTS.items():
        if re.search(pattern, lower):
            return field_type
    return None


class ColumnProfile:
    def __init__(self, name: str, values: list[Any]):
        self.name = name
        self.dtype = infer_type(next((v for v in values if v is not None), None))
        self.nullable = any(v is None for v in values)
        self.hint = guess_field_type(name)
        non_null = [v for v in values if v is not None]
        self.distribution = self._fit_distribution(non_null)
        self.pattern = self._extract_pattern(non_null)
        self.unique_ratio = len(set(str(v) for v in non_null)) / max(len(non_null), 1)

    def _fit_distribution(self, values: list) -> dict:
        if not values:
            return {"kind": "uniform"}
        if self.dtype in (DataType.INTEGER, DataType.FLOAT):
            nums = [v for v in values if isinstance(v, (int, float))]
            if nums:
                mu = statistics.mean(nums)
                sigma = statistics.pstdev(nums) if len(nums) > 1 else 1
                return {
                    "kind": "normal",
                    "mu": mu,
                    "sigma": max(sigma, 0.01),
                    "min": min(nums),
                    "max": max(nums),
                }
        elif self.dtype == DataType.STRING:
            text_vals = [str(v) for v in values]
            if len(set(text_vals)) / max(len(text_vals), 1) <= 0.5:
                counter = Counter(text_vals)
                total = len(text_vals)
                return {
                    "kind": "categorical",
                    "categories": {
                        k: v / total for k, v in counter.most_common()
                    },
                }
            return {"kind": "text"}
        return {"kind": "uniform"}

    def _extract_pattern(self, values: list) -> dict | None:
        strings = [str(v) for v in values if isinstance(v, str) and len(v) < 200]
        if len(strings) < 2:
            return None
        if len(set(strings)) < 3:
            return None
        tokens = re.findall(r"[A-Za-z]+|\d+|[^A-Za-z0-9]", strings[0])
        if not tokens:
            return None
        pattern_parts = []
        for t in tokens:
            if t.isalpha():
                if t.isupper():
                    pattern_parts.append(("alpha_upper", len(t)))
                elif t[0].isupper() and t[1:].islower():
                    pattern_parts.append(("alpha_title", len(t)))
                else:
                    pattern_parts.append(("alpha_lower", len(t)))
            elif t.isdigit():
                pattern_parts.append(("digit", len(t)))
            else:
                pattern_parts.append(("literal", t))
        consistent = all(
            len(re.findall(r"[A-Za-z]+|\d+|[^A-Za-z0-9]", s)) == len(tokens)
            for s in strings[1:3]
        ) if len(strings) > 1 else False
        if not consistent:
            return None
        return {"parts": pattern_parts, "examples": strings[:3]}


def infer_correlations(records: list[dict]) -> dict[tuple[str, str], float]:
    cols = list(records[0].keys()) if records else []
    numeric_cols = []
    for c in cols:
        vals = [r[c] for r in records if isinstance(r.get(c), (int, float))]
        if len(vals) > 3:
            numeric_cols.append(c)
    corr = {}
    for i, a in enumerate(numeric_cols):
        for b in numeric_cols[i + 1 :]:
            av = [r[a] for r in records if isinstance(r.get(a), (int, float))]
            bv = [r[b] for r in records if isinstance(r.get(b), (int, float))]
            n = min(len(av), len(bv))
            if n < 3:
                continue
            av, bv = av[:n], bv[:n]
            try:
                c = statistics.correlation(
                    [(x, y) for x, y in zip(av, bv)], method="ranked"
                )
                corr[(a, b)] = c
            except (statistics.StatisticsError, AttributeError):
                pass
    return corr
