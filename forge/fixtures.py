from __future__ import annotations

from typing import Any


def export_pytest_fixtures(records: list[dict], variable_name: str = "test_data") -> str:
    lines = ["import pytest", ""]
    lines.append(f"@pytest.fixture")
    lines.append(f"def {variable_name}():")
    lines.append("    return [")
    for r in records:
        lines.append(f"        {repr(r)},")
    lines.append("    ]")
    lines.append("")
    return "\n".join(lines)


def export_factory_boy(records: list[dict], factory_name: str = "RecordFactory",
                        model_name: str = "Record") -> str:
    lines = [
        "import factory",
        "",
    ]
    if records:
        cols = list(records[0].keys())
        lines.append(f"class {model_name}:")
        lines.append("    def __init__(self, **kwargs):")
        for c in cols:
            lines.append(f"        self.{c} = kwargs.get('{c}')")
        lines.append("")
        lines.append(f"class {factory_name}(factory.Factory):")
        lines.append(f"    class Meta:")
        lines.append(f"        model = {model_name}")
        lines.append("")
        for c in cols:
            val = records[0].get(c)
            if isinstance(val, str):
                lines.append(f"    {c} = factory.Faker('word')")
            elif isinstance(val, (int, float)):
                lines.append(f"    {c} = factory.Faker('random_int')")
            elif isinstance(val, bool):
                lines.append(f"    {c} = factory.Faker('boolean')")
            else:
                lines.append(f"    {c} = None")
    return "\n".join(lines)


def export_json_fixtures(records: list[dict]) -> str:
    import json
    return json.dumps(records, indent=2, default=str)


def export_typescript(records: list[dict], type_name: str = "Record") -> str:
    if not records:
        return f"export interface {type_name} {{}}\n"
    cols = list(records[0].keys())
    lines = [f"export interface {type_name} {{"]
    for c in cols:
        val = records[0].get(c)
        if isinstance(val, bool):
            ts_type = "boolean"
        elif isinstance(val, int):
            ts_type = "number"
        elif isinstance(val, float):
            ts_type = "number"
        elif val is None:
            ts_type = "any"
        else:
            ts_type = "string"
        lines.append(f"  {c}: {ts_type};")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def export_fixtures(records: list[dict], fmt: str = "pytest", **kwargs) -> str:
    exporters = {
        "pytest": export_pytest_fixtures,
        "factory_boy": export_factory_boy,
        "json": export_json_fixtures,
        "typescript": export_typescript,
    }
    exporter = exporters.get(fmt)
    if not exporter:
        raise ValueError(f"Unknown fixture format: {fmt}. Choose from: {', '.join(exporters.keys())}")
    return exporter(records, **kwargs)
