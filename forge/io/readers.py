from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from forge.core.plugin import Reader, Registry


@Registry.register_reader
class CSVReader(Reader):
    formats = ["csv"]

    def read(self, source: str, **kwargs) -> list[dict]:
        with open(source, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f, **kwargs))


@Registry.register_reader
class JSONReader(Reader):
    formats = ["json", "jsonl", "ndjson"]

    def read(self, source: str, **kwargs) -> list[dict]:
        with open(source, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [data]
        return data


@Registry.register_reader
class NDJSONReader(Reader):
    formats = ["ndjson"]

    def read(self, source: str, **kwargs) -> list[dict]:
        records = []
        with open(source, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records


@Registry.register_reader
class XLSXReader(Reader):
    formats = ["xlsx", "xls"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import openpyxl
        except ImportError:
            raise ImportError("openpyxl required for XLSX. Install: pip install forge[xlsx]")
        wb = openpyxl.load_workbook(source, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows[0])]
        return [dict(zip(headers, row)) for row in rows[1:] if any(c is not None for c in row)]


@Registry.register_reader
class YAMLReader(Reader):
    formats = ["yaml", "yml"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import yaml
        except ImportError:
            raise ImportError("pyyaml required for YAML. Install: pip install forge[yaml]")
        with open(source, "r") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [d if isinstance(d, dict) else {"value": d} for d in data]
        return []


@Registry.register_reader
class XMLReader(Reader):
    formats = ["xml"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import lxml.etree as ET
        except ImportError:
            raise ImportError("lxml required for XML. Install: pip install forge[xml]")
        tree = ET.parse(source)
        root = tree.getroot()
        return [self._element_to_dict(root)]

    def _element_to_dict(self, el) -> dict:
        d = {}
        for child in el:
            tag = child.tag
            if len(child) > 0:
                val = self._element_to_dict(child)
            else:
                val = child.text or ""
            if tag in d:
                if not isinstance(d[tag], list):
                    d[tag] = [d[tag]]
                d[tag].append(val)
            else:
                d[tag] = val
        return d


@Registry.register_reader
class MarkdownReader(Reader):
    formats = ["md", "markdown"]

    def read(self, source: str, **kwargs) -> list[dict]:
        import re

        with open(source, "r") as f:
            text = f.read()
        tables = re.findall(r"\|(.+)\|\n\|[-| ]+\|\n((?:\|.+\|\n?)+)", text)
        results = []
        for header_line, body in tables:
            headers = [h.strip() for h in header_line.split("|") if h.strip()]
            rows = []
            for line in body.strip().split("\n"):
                cells = [c.strip() for c in line.split("|") if c.strip()]
                if len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
            results.extend(rows)
        if not results:
            results.append({"content": text.strip()})
        return results


@Registry.register_reader
class SQLiteReader(Reader):
    formats = ["db", "sqlite", "sqlite3"]

    def read(self, source: str, **kwargs) -> list[dict]:
        table = kwargs.get("table")
        conn = sqlite3.connect(source)
        conn.row_factory = sqlite3.Row
        if table:
            query = f"SELECT * FROM [{table}]"
        else:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            if not tables:
                conn.close()
                return []
            query = f"SELECT * FROM [{tables[0]}]"
        cur = conn.execute(query)
        results = [dict(row) for row in cur.fetchall()]
        conn.close()
        return results


@Registry.register_reader
class ParquetReader(Reader):
    formats = ["parquet"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow required for Parquet. Install: pip install forge[parquet]")
        table = pq.read_table(source)
        return table.to_pandas().to_dict(orient="records")


@Registry.register_reader
class HTMLReader(Reader):
    formats = ["html", "htm"]

    def read(self, source: str, **kwargs) -> list[dict]:
        try:
            from lxml import html as lh
        except ImportError:
            raise ImportError("lxml required for HTML. Install: pip install forge[xml]")
        with open(source, "r") as f:
            tree = lh.fromstring(f.read())
        tables = tree.findall(".//table")
        results = []
        for table in tables:
            rows = table.findall(".//tr")
            headers = []
            data_rows = rows
            for th in rows[0].findall(".//th"):
                headers.append(th.text_content().strip())
            if headers:
                data_rows = rows[1:]
            for tr in data_rows:
                cells = tr.findall(".//td")
                if headers:
                    results.append(
                        dict(zip(headers, [c.text_content().strip() for c in cells]))
                    )
                else:
                    results.append(
                        {f"col_{i}": c.text_content().strip() for i, c in enumerate(cells)}
                    )
        return results


@Registry.register_reader
class PlainTextReader(Reader):
    formats = ["txt", "log", "text"]

    def read(self, source: str, **kwargs) -> list[dict]:
        with open(source, "r") as f:
            lines = f.readlines()
        return [{"line": line.rstrip("\n"), "number": i + 1} for i, line in enumerate(lines)]
