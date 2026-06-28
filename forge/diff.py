from __future__ import annotations

from collections import Counter
from typing import Any


class DiffReport:
    def __init__(self):
        self.only_left = 0
        self.only_right = 0
        self.common = 0
        self.changed: list[dict] = []
        self.schema_changes: list[str] = []
        self.distribution_shifts: list[str] = []

    @property
    def total_changes(self) -> int:
        return self.only_left + self.only_right + len(self.changed)

    def summary(self) -> dict:
        return {
            "rows_only_a": self.only_left,
            "rows_only_b": self.only_right,
            "rows_common": self.common,
            "rows_changed": len(self.changed),
            "schema_changes": self.schema_changes,
            "distribution_shifts": self.distribution_shifts,
        }


def diff_datasets(
    a: list[dict],
    b: list[dict],
    key: str | None = None,
    threshold: float = 0.05,
) -> DiffReport:
    report = DiffReport()

    if not a and not b:
        return report

    if not a:
        report.only_right = len(b)
        report.schema_changes.append("Dataset A is empty")
        return report

    if not b:
        report.only_left = len(a)
        report.schema_changes.append("Dataset B is empty")
        return report

    cols_a = set(a[0].keys()) if a else set()
    cols_b = set(b[0].keys()) if b else set()

    added = cols_b - cols_a
    removed = cols_a - cols_b
    if added:
        report.schema_changes.append(f"Columns added: {', '.join(sorted(added))}")
    if removed:
        report.schema_changes.append(f"Columns removed: {', '.join(sorted(removed))}")

    for col in sorted(cols_a & cols_b):
        av = [r.get(col) for r in a if r.get(col) is not None]
        bv = [r.get(col) for r in b if r.get(col) is not None]
        if not av or not bv:
            continue
        a_strs = [str(v) for v in av]
        b_strs = [str(v) for v in bv]
        a_unique = len(set(a_strs)) / max(len(a_strs), 1)
        b_unique = len(set(b_strs)) / max(len(b_strs), 1)
        if abs(a_unique - b_unique) > threshold:
            report.distribution_shifts.append(
                f"{col}: unique ratio {a_unique:.2f} → {b_unique:.2f}"
            )
        if isinstance(av[0], (int, float)) and isinstance(bv[0], (int, float)):
            import statistics
            try:
                am, bm = statistics.mean(av), statistics.mean(bv)
                if abs(am - bm) / max(abs(am), 1) > threshold:
                    report.distribution_shifts.append(
                        f"{col}: mean {am:.2f} → {bm:.2f}"
                    )
            except statistics.StatisticsError:
                pass

    if key:
        a_map = {str(r.get(key)): r for r in a}
        b_map = {str(r.get(key)): r for r in b}
        a_keys = set(a_map.keys())
        b_keys = set(b_map.keys())
        report.only_left = len(a_keys - b_keys)
        report.only_right = len(b_keys - a_keys)
        report.common = len(a_keys & b_keys)
        for k in sorted(a_keys & b_keys)[:100]:
            ra, rb = a_map[k], b_map[k]
            for col in cols_a & cols_b:
                if str(ra.get(col)) != str(rb.get(col)):
                    report.changed.append({
                        "key": k, "column": col,
                        "a": ra.get(col), "b": rb.get(col),
                    })
    else:
        n = min(len(a), len(b))
        report.common = n
        report.only_left = max(0, len(a) - n)
        report.only_right = max(0, len(b) - n)
        for i in range(n):
            ra, rb = a[i], b[i]
            for col in cols_a & cols_b:
                if str(ra.get(col)) != str(rb.get(col)):
                    report.changed.append({
                        "row": i, "column": col,
                        "a": ra.get(col), "b": rb.get(col),
                    })

    return report
