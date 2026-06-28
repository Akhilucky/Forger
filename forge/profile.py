from __future__ import annotations

import statistics
from collections import Counter
from datetime import datetime
from typing import Any

from forge.core.schema import Schema, DataType, infer_type


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Forge Profile — {title}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       background:#f5f7fa; color:#1a1a2e; padding:2rem; }}
h1 {{ font-size:1.8rem; margin-bottom:.5rem; }}
.meta {{ color:#666; font-size:.9rem; margin-bottom:2rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(380px,1fr)); gap:1.5rem; }}
.card {{ background:#fff; border-radius:12px; padding:1.5rem; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
.card h2 {{ font-size:1rem; margin-bottom:.75rem; color:#555; }}
.stat {{ display:flex; justify-content:space-between; padding:.25rem 0; font-size:.85rem; }}
.stat .label {{ color:#888; }} .stat .val {{ font-weight:600; color:#1a1a2e; }}
.bar {{ height:6px; background:#e8ecf1; border-radius:3px; margin-top:.5rem; overflow:hidden; }}
.bar-fill {{ height:100%; background:#4361ee; border-radius:3px; }}
.dist {{ margin-top:.5rem; }}
.dist-item {{ display:flex; justify-content:space-between; font-size:.8rem; padding:.15rem 0; }}
.dist-item .k {{ color:#555; }} .dist-item .v {{ color:#888; }}
table {{ width:100%; border-collapse:collapse; font-size:.85rem; }}
th,td {{ text-align:left; padding:.4rem .5rem; border-bottom:1px solid #eee; }}
th {{ color:#888; font-weight:500; }}
tr:hover {{ background:#f8f9fb; }}
.badge {{ display:inline-block; padding:.15rem .5rem; border-radius:4px; font-size:.75rem; font-weight:500; }}
.badge-string {{ background:#e3f2fd; color:#1565c0; }}
.badge-int {{ background:#f3e5f5; color:#7b1fa2; }}
.badge-float {{ background:#e8f5e9; color:#2e7d32; }}
.badge-bool {{ background:#fff3e0; color:#e65100; }}
.badge-date {{ background:#fce4ec; color:#c62828; }}
.badge-email {{ background:#e0f7fa; color:#00695c; }}
.badge-uuid {{ background:#efebe9; color:#4e342e; }}
</style>
</head>
<body>
<h1>📊 {title}</h1>
<p class="meta">{n_records:,} records · {n_cols} columns · {ts}</p>
<div class="grid">
{cards}
</div>
</body>
</html>"""


def _type_badge(dtype: DataType) -> str:
    m = {
        DataType.STRING: "string", DataType.INTEGER: "int",
        DataType.FLOAT: "float", DataType.BOOLEAN: "bool",
        DataType.DATE: "date", DataType.DATETIME: "datetime",
        DataType.EMAIL: "email", DataType.UUID: "uuid",
        DataType.PHONE: "phone", DataType.URL: "url",
    }
    cls = m.get(dtype, "string")
    return f'<span class="badge badge-{cls}">{dtype.value}</span>'


def _card_html(name: str, vals: list[Any], dtype: DataType) -> str:
    non_null = [v for v in vals if v is not None]
    n = len(non_null)
    nulls = len(vals) - n
    pct = round(nulls / max(len(vals), 1) * 100, 1)

    stats = f"""
    <div class="stat"><span class="label">Type</span><span class="val">{_type_badge(dtype)}</span></div>
    <div class="stat"><span class="label">Non-null</span><span class="val">{n:,} / {len(vals):,}</span></div>
    <div class="stat"><span class="label">Nulls</span><span class="val">{nulls:,} ({pct}%)</span></div>
    <div class="bar"><div class="bar-fill" style="width:{100-pct}%"></div></div>
    """

    if nulls:
        stats += f'<div class="stat"><span class="label">Null ratio</span><span class="val">{pct}%</span></div>'

    if dtype in (DataType.INTEGER, DataType.FLOAT) and n:
        nums = [v for v in non_null if isinstance(v, (int, float))]
        if nums:
            mn, mx = min(nums), max(nums)
            mu = statistics.mean(nums)
            stats += f"""
            <div class="stat"><span class="label">Min</span><span class="val">{mn}</span></div>
            <div class="stat"><span class="label">Max</span><span class="val">{mx}</span></div>
            <div class="stat"><span class="label">Mean</span><span class="val">{mu:.2f}</span></div>"""
            if len(nums) > 1:
                sd = statistics.pstdev(nums)
                stats += f'<div class="stat"><span class="label">Std dev</span><span class="val">{sd:.2f}</span></div>'

    if dtype == DataType.STRING and n:
        strs = [str(v) for v in non_null]
        lens = [len(s) for s in strs]
        unique = len(set(strs))
        stats += f"""
        <div class="stat"><span class="label">Unique</span><span class="val">{unique:,} / {n:,}</span></div>
        <div class="stat"><span class="label">Min length</span><span class="val">{min(lens)}</span></div>
        <div class="stat"><span class="label">Max length</span><span class="val">{max(lens)}</span></div>"""
        if unique / max(n, 1) < 0.3 and n > 5:
            c = Counter(strs)
            top = c.most_common(5)
            dist = "".join(
                f'<div class="dist-item"><span class="k">{k}</span><span class="v">{v} ({round(v/n*100)}%)</span></div>'
                for k, v in top
            )
            stats += f'<div class="dist"><strong style="font-size:.8rem;color:#888;">Top values</strong>{dist}</div>'

    return f'<div class="card"><h2>{name}</h2>{stats}</div>'


def generate_profile(records: list[dict], title: str = "Dataset Profile") -> str:
    if not records:
        return HTML_TEMPLATE.format(title=title, n_records=0, n_cols=0,
                                    ts=datetime.now().isoformat()[:19], cards="<p>No records</p>")

    schema = Schema.infer(records)
    col_map = {c.name: c for c in schema.columns}
    cards = []
    for name in list(records[0].keys()):
        vals = [r.get(name) for r in records]
        col = col_map.get(name)
        dtype = col.dtype if col else DataType.UNKNOWN
        cards.append(_card_html(name, vals, dtype))

    return HTML_TEMPLATE.format(
        title=title,
        n_records=len(records),
        n_cols=len(schema.columns),
        ts=datetime.now().isoformat()[:19].replace("T", " "),
        cards="\n".join(cards),
    )
