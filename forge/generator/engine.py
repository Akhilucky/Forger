from __future__ import annotations

import random
from copy import deepcopy
from typing import Any

from forge.core.schema import DataType, Schema
from forge.generator.fields import generate as gen_field
from forge.generator.inference import ColumnProfile, guess_field_type, infer_correlations
from forge.generator.llm import generate_with_llm


class Engine:
    def __init__(self):
        self.profiles: list[ColumnProfile] = []
        self.correlations: dict[tuple[str, str], float] = {}
        self.records: list[dict] = []

    def learn(self, records: list[dict]) -> Engine:
        if not records:
            return self
        cols = list(records[0].keys())
        self.profiles = [ColumnProfile(c, [r.get(c) for r in records]) for c in cols]
        self.correlations = infer_correlations(records)
        self.records = records
        return self

    def generate(self, count: int = 10, use_llm: bool = False,
                 model_path: str | None = None) -> list[dict]:
        if use_llm and not self.records:
            schema = Schema.infer(self.records) if hasattr(self, 'records') and self.records else None
            cols = [{"name": p.name} for p in self.profiles] if self.profiles else []
            cols_data = []
            for p in self.profiles:
                ci = {"name": p.name, "type": p.dtype.value if p.dtype else "string", "nullable": p.nullable}
                if p.distribution and p.distribution.get("kind") == "categorical":
                    ci["categories"] = list(p.distribution["categories"].keys())
                cols_data.append(ci)
            llm_result = generate_with_llm(cols_data, count, model_path, self.records)
            if llm_result:
                return llm_result

        if not self.profiles:
            return [{} for _ in range(count)]

        records = []
        for _ in range(count):
            record = self._gen_row()
            records.append(record)

        if self.correlations:
            records = self._apply_correlations(records)

        return records

    def generate_from_spec(self, columns: list[dict], count: int = 10,
                           use_llm: bool = False,
                           model_path: str | None = None) -> list[dict]:
        if use_llm:
            llm_result = generate_with_llm(columns, count, model_path)
            if llm_result:
                return llm_result

        profile_map = {p.name: p for p in self.profiles}
        records = []
        for _ in range(count):
            record = {}
            for col in columns:
                name = col["name"]
                if name in profile_map:
                    p = profile_map[name]
                    record[name] = gen_field(p.pattern, p.hint, p.distribution, name)
                else:
                    dtype = col.get("type", "string")
                    hint = guess_field_type(name)
                    record[name] = gen_field(None, hint, None, name)
            records.append(record)
        return records

    def _gen_row(self) -> dict:
        row = {}
        for p in self.profiles:
            row[p.name] = gen_field(p.pattern, p.hint, p.distribution, p.name)
        return row

    def _apply_correlations(self, records: list[dict]) -> list[dict]:
        from statistics import stdev, mean

        for (a, b), corr_val in self.correlations.items():
            if abs(corr_val) < 0.3:
                continue
            av = [r[a] for r in records if isinstance(r.get(a), (int, float))]
            bv = [r[b] for r in records if isinstance(r.get(b), (int, float))]
            n = min(len(av), len(bv))
            if n < 4:
                continue
            av, bv = av[:n], bv[:n]
            sorted_a = sorted(range(len(av)), key=lambda i: av[i])
            sorted_b = sorted(range(len(bv)), key=lambda i: bv[i])
            if corr_val > 0:
                for src_i, tgt_i in zip(sorted_a, sorted_b):
                    records[tgt_i] = records[tgt_i].copy() if tgt_i < len(records) else records[-1].copy()
                    records[tgt_i][a] = av[src_i]
            elif corr_val < 0:
                for src_i, tgt_i in zip(sorted_a, reversed(sorted_b)):
                    if tgt_i < len(records):
                        records[tgt_i] = records[tgt_i].copy()
                        records[tgt_i][a] = av[src_i]
        return records

    def self_iterate(self, count: int = 10,
                     iterations: int = 3,
                     use_llm: bool = False,
                     model_path: str | None = None) -> list[dict]:
        best = self.generate(count, use_llm, model_path)
        for _ in range(iterations - 1):
            candidate = self.generate(count, use_llm, model_path)
            try:
                if self._score(candidate) > self._score(best):
                    best = candidate
            except Exception:
                pass
        return best

    def _score(self, records: list[dict]) -> float:
        if not records or not self.records:
            return 0.0
        score = 0.0
        for p in self.profiles:
            col_vals = [r.get(p.name) for r in records]
            non_null = [v for v in col_vals if v is not None]
            if not non_null:
                continue
            ratio = len(set(str(v) for v in non_null)) / max(len(non_null), 1)
            orig_non_null = [r.get(p.name) for r in self.records if r.get(p.name) is not None]
            if orig_non_null:
                orig_ratio = len(set(str(v) for v in orig_non_null)) / max(len(orig_non_null), 1)
                score -= abs(ratio - orig_ratio) * 10
        return score / max(len(self.profiles), 1)
