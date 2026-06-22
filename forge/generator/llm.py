from __future__ import annotations

import json
import subprocess
from typing import Any


LLM_PROMPT = """You are a data generation engine. Given the schema below, generate exactly {count} realistic JSON records.

Schema:
{columns}

Rules:
- Output ONLY a valid JSON array of objects, no other text
- Each object must have all columns shown in the schema
- Values must be realistic and varied
- Preserve any patterns visible in sample values if provided
- Use appropriate types (strings, numbers, booleans, nulls)

Sample data (if any):
{sample}

Generate {count} records:"""


def generate_with_llm(
    columns: list[dict],
    count: int,
    model_path: str | None = None,
    sample: list[dict] | None = None,
) -> list[dict] | None:
    if model_path:
        return _generate_llamacpp(columns, count, model_path, sample)
    try:
        return _generate_ollama(columns, count, sample)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def _generate_ollama(
    columns: list[dict], count: int, sample: list[dict] | None = None
) -> list[dict] | None:
    prompt = LLM_PROMPT.format(
        count=min(count, 50),
        columns=json.dumps(columns, indent=2),
        sample=json.dumps(sample[:5] if sample else [], indent=2),
    )
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3.2:3b"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = result.stdout.strip()
        if "```json" in out:
            out = out.split("```json")[1].split("```")[0].strip()
        elif "```" in out:
            out = out.split("```")[1].split("```")[0].strip()
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return data[:count] if isinstance(data, list) else None
    except Exception:
        return None


def _generate_llamacpp(
    columns: list[dict], count: int, model_path: str, sample: list[dict] | None = None
) -> list[dict] | None:
    prompt = LLM_PROMPT.format(
        count=min(count, 20),
        columns=json.dumps(columns, indent=2),
        sample=json.dumps(sample[:3] if sample else [], indent=2),
    )
    try:
        result = subprocess.run(
            [model_path, "--prompt", prompt, "--temp", "0.8", "--n-predict", "2048"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = result.stdout.strip()
        if "```json" in out:
            out = out.split("```json")[1].split("```")[0].strip()
        elif "```" in out:
            out = out.split("```")[1].split("```")[0].strip()
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return data[:count] if isinstance(data, list) else None
    except Exception:
        return None



def generate_single_field(field_name: str, field_type: str,
                           context: dict | None = None,
                           model_path: str | None = None) -> Any | None:
    if context:
        sample_str = None
    else:
        sample_str = None

    prompt = (
        f"Generate exactly one realistic value for '{field_name}' (type: {field_type})."
    )
    if sample_str:
        prompt += f" Sample values: {sample_str}."
    prompt += " Output ONLY the value, no explanation."

    try:
        if model_path:
            cmd = [model_path, "--prompt", prompt, "--temp", "0.8", "--n-predict", "64"]
        else:
            cmd = ["ollama", "run", "llama3.2:3b"]
        result = subprocess.run(
            cmd, input=prompt if not model_path else None,
            capture_output=True, text=True, timeout=30,
        )
        out = result.stdout.strip().split("\n")[0].strip()
        return out
    except Exception:
        return None
