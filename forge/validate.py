from __future__ import annotations

import re
from typing import Any

from forge.core.schema import Schema, DataType


class ValidationRule:
    def __init__(self, column: str, **kwargs):
        self.column = column
        self.rules = kwargs

    def check(self, records: list[dict]) -> list[str]:
        errors = []
        for i, r in enumerate(records):
            val = r.get(self.column)
            for rule, expected in self.rules.items():
                if rule == "required" and expected and val is None:
                    errors.append(f"row[{i}].{self.column}: required but null")
                elif rule == "type" and val is not None:
                    t = infer_type(val)
                    if t.value != expected and not (expected == "numeric" and t in (DataType.INTEGER, DataType.FLOAT)):
                        errors.append(f"row[{i}].{self.column}: expected {expected}, got {t.value}")
                elif rule == "min" and val is not None:
                    try:
                        if float(val) < expected:
                            errors.append(f"row[{i}].{self.column}: {val} < min {expected}")
                    except (ValueError, TypeError):
                        pass
                elif rule == "max" and val is not None:
                    try:
                        if float(val) > expected:
                            errors.append(f"row[{i}].{self.column}: {val} > max {expected}")
                    except (ValueError, TypeError):
                        pass
                elif rule == "pattern" and val is not None:
                    if not re.search(expected, str(val)):
                        errors.append(f"row[{i}].{self.column}: does not match pattern /{expected}/")
                elif rule == "unique" and expected and val is not None:
                    for j in range(i):
                        if records[j].get(self.column) == val:
                            errors.append(f"row[{i}].{self.column}: duplicates row[{j}]")
                            break
                elif rule == "in" and val is not None:
                    if val not in expected:
                        errors.append(f"row[{i}].{self.column}: {val} not in {expected}")
        return errors


def validate_dataset(records: list[dict], rules: list[dict]) -> dict:
    all_errors = {}
    for rule_spec in rules:
        column = rule_spec.pop("column")
        rule = ValidationRule(column, **rule_spec)
        errors = rule.check(records)
        if errors:
            all_errors[column] = errors
    return all_errors


def validate_from_yaml(path: str, records: list[dict]) -> dict:
    try:
        import yaml
    except ImportError:
        raise ImportError("pyyaml required. pip install forge[yaml]")
    with open(path) as f:
        config = yaml.safe_load(f)
    rules = config if isinstance(config, list) else config.get("rules", [])
    return validate_dataset(records, rules)


def infer_type(val):
    from forge.core.schema import infer_type as it
    return it(val)
