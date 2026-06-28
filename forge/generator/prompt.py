from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from forge.generator.inference import FIELD_HINTS

NL_SCHEMA_PROMPT = """Given this natural language description of a dataset, output a JSON array of column definitions.

Description: "{prompt}"

Rules:
- Each column: {{"name": "...", "type": "string|integer|float|boolean"}}
- Infer types from the description (names→string, ages→integer, prices→float)
- Include 5-15 columns that make sense for this dataset
- Use realistic column names (snake_case)
- Output ONLY the JSON array, no other text

Example for "e-commerce customers":
[{{"name":"id","type":"integer"},{"name":"name","type":"string"},{"name":"email","type":"string"},{"name":"age","type":"integer"},{"name":"city","type":"string"},{"name":"signup_date","type":"string"},{"name":"lifetime_value","type":"float"}}]

Generate columns for: "{prompt}":"""


DEFAULT_COLUMNS: dict[str, list[dict]] = {
    "user": [
        {"name": "id", "type": "integer"}, {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}, {"name": "age", "type": "integer"},
        {"name": "city", "type": "string"}, {"name": "country", "type": "string"},
        {"name": "phone", "type": "string"}, {"name": "created_at", "type": "string"},
    ],
    "customer": [
        {"name": "id", "type": "integer"}, {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}, {"name": "company", "type": "string"},
        {"name": "industry", "type": "string"}, {"name": "revenue", "type": "float"},
        {"name": "status", "type": "string"}, {"name": "since", "type": "string"},
    ],
    "product": [
        {"name": "id", "type": "integer"}, {"name": "name", "type": "string"},
        {"name": "description", "type": "string"}, {"name": "price", "type": "float"},
        {"name": "category", "type": "string"}, {"name": "in_stock", "type": "boolean"},
        {"name": "sku", "type": "string"}, {"name": "rating", "type": "float"},
    ],
    "order": [
        {"name": "id", "type": "integer"}, {"name": "user_id", "type": "integer"},
        {"name": "product", "type": "string"}, {"name": "quantity", "type": "integer"},
        {"name": "total", "type": "float"}, {"name": "status", "type": "string"},
        {"name": "shipping_address", "type": "string"}, {"name": "created_at", "type": "string"},
    ],
    "employee": [
        {"name": "id", "type": "integer"}, {"name": "name", "type": "string"},
        {"name": "email", "type": "string"}, {"name": "department", "type": "string"},
        {"name": "title", "type": "string"}, {"name": "salary", "type": "float"},
        {"name": "start_date", "type": "string"}, {"name": "manager", "type": "string"},
    ],
    "transaction": [
        {"name": "id", "type": "integer"}, {"name": "amount", "type": "float"},
        {"name": "currency", "type": "string"}, {"name": "status", "type": "string"},
        {"name": "merchant", "type": "string"}, {"name": "timestamp", "type": "string"},
        {"name": "payment_method", "type": "string"}, {"name": "country", "type": "string"},
    ],
    "blog": [
        {"name": "id", "type": "integer"}, {"name": "title", "type": "string"},
        {"name": "content", "type": "string"}, {"name": "author", "type": "string"},
        {"name": "tags", "type": "string"}, {"name": "published_at", "type": "string"},
        {"name": "views", "type": "integer"}, {"name": "status", "type": "string"},
    ],
    "event": [
        {"name": "id", "type": "integer"}, {"name": "name", "type": "string"},
        {"name": "description", "type": "string"}, {"name": "date", "type": "string"},
        {"name": "location", "type": "string"}, {"name": "capacity", "type": "integer"},
        {"name": "organizer", "type": "string"}, {"name": "ticket_price", "type": "float"},
    ],
}


def infer_columns_from_prompt(prompt: str, use_llm: bool = False,
                                model_path: str | None = None) -> list[dict]:
    lower = prompt.lower()

    for key, cols in DEFAULT_COLUMNS.items():
        if key in lower:
            return cols

    if use_llm:
        try:
            prompt_text = NL_SCHEMA_PROMPT.format(prompt=prompt)
            if model_path:
                result = subprocess.run(
                    [model_path, "--prompt", prompt_text, "--temp", "0.3", "--n-predict", "1024"],
                    capture_output=True, text=True, timeout=60,
                )
            else:
                result = subprocess.run(
                    ["ollama", "run", "llama3.2:3b"],
                    input=prompt_text, capture_output=True, text=True, timeout=60,
                )
            out = result.stdout.strip()
            if "```json" in out:
                out = out.split("```json")[1].split("```")[0].strip()
            elif "```" in out:
                out = out.split("```")[1].split("```")[0].strip()
            cols = json.loads(out)
            if isinstance(cols, list):
                return cols
        except Exception:
            pass

    words = re.sub(r"[^\w\s]", " ", lower).split()
    keywords = ["name", "email", "age", "city", "country", "phone", "address",
                 "company", "price", "amount", "date", "id", "status", "type",
                 "description", "title", "category", "salary", "quantity"]
    found = [w for w in words if w in keywords]

    cols = [{"name": "id", "type": "integer"}]
    for kw in dict.fromkeys(found):
        t = "string"
        if kw in ("age", "id", "quantity", "count"):
            t = "integer"
        elif kw in ("price", "amount", "salary", "revenue", "total"):
            t = "float"
        cols.append({"name": kw, "type": t})
    if not cols[1:]:
        cols.extend(DEFAULT_COLUMNS.get("user", []))
    return cols
