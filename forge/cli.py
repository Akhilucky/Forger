import sys
import os
import click

from forge.core.pipeline import Pipeline
from forge.core.plugin import Registry


@click.group(invoke_without_command=True)
@click.version_option(version="0.4.0", prog_name="forge")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _parse_columns(cols_str: str | None) -> list[dict] | None:
    if not cols_str:
        return None
    result = []
    for s in cols_str.split(","):
        s = s.strip()
        if ":" in s:
            n, t = s.split(":", 1)
            result.append({"name": n.strip(), "type": t.strip()})
        else:
            result.append({"name": s, "type": "string"})
    return result


# ── run ────────────────────────────────────────────────────────────────
@cli.command()
@click.argument("config", required=False)
@click.argument("destination", required=False)
@click.option("-m", "--mode")
@click.option("-f", "--from-format", "from_fmt")
@click.option("-t", "--to-format", "to_fmt")
@click.option("--count", type=int)
@click.option("--columns")
@click.option("--table")
@click.option("--duplicates", type=int)
def run(config, destination, mode, from_fmt, to_fmt, count, columns, table, duplicates):
    """Compile data or run a pipeline config file.

    Pass SOURCE DESTINATION for one-shot conversion, or PIPELINE.yaml for multi-step.
    """
    if config and os.path.exists(config) and config.endswith((".yaml", ".yml", ".json")):
        from forge.pipeline_runner import run_pipeline
        click.echo(f"Running pipeline: {config}")
        records = run_pipeline(config)
        click.echo(f"✓ Pipeline complete ({len(records)} records)")
        return

    if not config or not destination:
        click.echo("Usage: forge run SOURCE DESTINATION [options]")
        click.echo("   or: forge run PIPELINE.yaml")
        return

    kwargs = {}
    if count: kwargs["count"] = count
    if columns: kwargs["columns"] = [c.strip() for c in columns.split(",")]
    if table: kwargs["table"] = table
    if duplicates: kwargs["duplicates"] = duplicates

    try:
        records = Pipeline.go(
            source=config, destination=destination,
            mode=mode, source_format=from_fmt, dest_format=to_fmt, **kwargs,
        )
        click.echo(f"✓ Compiled {len(records)} records → {destination}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── generate ───────────────────────────────────────────────────────────
@cli.command()
@click.option("-o", "--output", help="Output file")
@click.option("--format", "fmt", default="json",
              help="Output format (json, csv, yaml, ndjson, sql)")
@click.option("--count", type=int, default=10)
@click.option("--columns", "cols",
              help="Column spec: 'name:type,name:type,...' or 'name,name,...'")
@click.option("--prompt",
              help="Natural language description of the dataset (overrides --columns)")
@click.option("--sample", type=click.Path(exists=True))
@click.option("--iterations", type=int, default=1)
@click.option("--llm", is_flag=True, default=False)
@click.option("--model")
@click.option("--show", is_flag=True, default=False)
@click.option("--size", help="Target file size (e.g. '100MB', '10GB')")
@click.option("--progress/--no-progress", default=True)
@click.option("--fixture",
              help="Export as test fixture: pytest, factory_boy, typescript, json")
def generate(output, fmt, count, cols, prompt, sample, iterations, llm, model, show, size, progress, fixture):
    """Generate datasets from column specs, prompts, or samples.

    Examples:

        forge generate --columns "name,email,age" --count 100

        forge generate --prompt "e-commerce users with orders" --count 500

        forge generate --columns "name,email,age" --size 1GB -o big.csv --format csv

        forge generate --columns "name,email" --count 5 --fixture pytest -o test_fixtures.py
    """
    from forge.generator.engine import Engine

    if prompt and not cols:
        from forge.generator.prompt import infer_columns_from_prompt
        cols_list = infer_columns_from_prompt(prompt, llm, model)
        click.echo(f"✓ Inferred {len(cols_list)} columns from prompt", err=True)
    elif cols:
        cols_list = _parse_columns(cols)
    else:
        click.echo("Specify --columns or --prompt", err=True)
        sys.exit(1)

    engine = Engine()
    sample_records = []
    if sample:
        sample_records = Pipeline().read(sample).run()
        engine.learn(sample_records)
        click.echo(f"✓ Learned from {len(sample_records)} sample records", err=True)

    if size:
        from forge.generator.stream import generate_huge
        if not output:
            click.echo("--output required with --size", err=True)
            sys.exit(1)
        generate_huge(cols_list, output, size, fmt, sample_records, progress)
        return

    records = engine.generate_from_spec(cols_list, count, llm, model)
    if iterations > 1 and sample_records:
        best = engine.self_iterate(count, iterations, llm, model)
        if best: records = best

    if fixture:
        from forge.fixtures import export_fixtures
        fname = fixture if os.path.splitext(fixture)[1] else fixture
        fixture_fmt = os.path.splitext(fname)[0] if os.path.splitext(fname)[1] else fname
        fmt_map = {".py": "pytest", ".ts": "typescript", ".json": "json"}
        fixture_type = fmt_map.get(os.path.splitext(fname)[1].lower(), fname)
        code = export_fixtures(records, fmt=fixture_type)
        if output:
            with open(output, "w") as f:
                f.write(code)
            click.echo(f"✓ {fixture_type} fixtures → {output}")
        else:
            click.echo(code)
        return

    if output:
        writer = Registry.get_writer(fmt)
        if writer:
            writer().write(records, output)
            click.echo(f"✓ Generated {len(records)} records → {output}")
        else:
            click.echo(f"✗ No writer for format: {fmt}", err=True)
            sys.exit(1)
    elif show or not output:
        import json as j
        click.echo(j.dumps(records, indent=2, default=str))
    else:
        click.echo(f"✓ Generated {len(records)} records")


# ── inspect ────────────────────────────────────────────────────────────
@cli.command()
@click.argument("source")
@click.option("-f", "--format", "fmt")
@click.option("--head", type=int, default=5)
def inspect(source, fmt, head):
    """Show schema and preview of a dataset."""
    try:
        records = Pipeline().read(source, fmt).run()
        if not records:
            click.echo("(empty)")
            return
        schema = records[0].keys()
        click.echo(f"Records: {len(records)}")
        click.echo(f"Columns: {len(schema)}")
        click.echo(f"Schema:  {', '.join(schema)}")
        click.echo("")
        click.echo("Preview:")
        for i, r in enumerate(records[:head]):
            click.echo(f"  [{i}] {r}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── profile ────────────────────────────────────────────────────────────
@cli.command()
@click.argument("source")
@click.option("-f", "--format", "fmt")
@click.option("-o", "--output", default="profile.html")
@click.option("--title", default="Dataset Profile")
def profile(source, fmt, output, title):
    """Generate an HTML data profile report."""
    try:
        records = Pipeline().read(source, fmt).run()
        from forge.profile import generate_profile
        html = generate_profile(records, title)
        with open(output, "w") as f:
            f.write(html)
        click.echo(f"✓ Profile → {output} ({len(records)} records)")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── diff ───────────────────────────────────────────────────────────────
@cli.command()
@click.argument("source_a")
@click.argument("source_b")
@click.option("-f", "--format", "fmt")
@click.option("--key", help="Key column for row matching")
def diff(source_a, source_b, fmt, key):
    """Compare two datasets structurally."""
    try:
        a = Pipeline().read(source_a, fmt).run()
        b = Pipeline().read(source_b, fmt).run()
        from forge.diff import diff_datasets
        report = diff_datasets(a, b, key=key)
        s = report.summary()
        click.echo(f"  Rows only in A: {s['rows_only_a']}")
        click.echo(f"  Rows only in B: {s['rows_only_b']}")
        click.echo(f"  Rows common:    {s['rows_common']}")
        click.echo(f"  Changed cells:  {s['rows_changed']}")
        for sc in s["schema_changes"]:
            click.echo(f"  Schema: {sc}")
        for ds in s["distribution_shifts"]:
            click.echo(f"  Shift:  {ds}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── validate ───────────────────────────────────────────────────────────
@cli.command()
@click.argument("source")
@click.argument("rules", required=False)
@click.option("-f", "--format", "fmt")
@click.option("--schema", type=click.Path(exists=True),
              help="YAML validation rules file")
@click.option("--required", help="Comma-separated required columns")
@click.option("--unique", help="Comma-separated unique columns")
def validate(source, rules, fmt, schema, required, unique):
    """Validate a dataset against rules."""
    try:
        records = Pipeline().read(source, fmt).run()
        from forge.validate import validate_dataset

        rule_list = []
        if schema:
            from forge.validate import validate_from_yaml
            errors = validate_from_yaml(schema, records)
        else:
            if required:
                for c in required.split(","):
                    rule_list.append({"column": c.strip(), "required": True})
            if unique:
                for c in unique.split(","):
                    rule_list.append({"column": c.strip(), "unique": True})
            if not rule_list:
                click.echo("No rules specified. Use --required, --unique, or --schema", err=True)
                return
            errors = validate_dataset(records, rule_list)

        total = sum(len(v) for v in errors.values())
        if errors:
            click.echo(f"✗ {total} validation errors:")
            for col, errs in errors.items():
                for e in errs[:5]:
                    click.echo(f"  • {e}")
                if len(errs) > 5:
                    click.echo(f"  ... and {len(errs)-5} more")
        else:
            click.echo("✓ All validations passed")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── formats ────────────────────────────────────────────────────────────
@cli.command()
def formats():
    """List all supported formats."""
    click.echo("Readers:")
    for r in sorted(Registry.list_readers()):
        click.echo(f"  • {r}")
    click.echo("")
    click.echo("Writers:")
    for w in sorted(Registry.list_writers()):
        click.echo(f"  • {w}")


# ── mock ───────────────────────────────────────────────────────────────
@cli.command()
@click.option("-p", "--port", default=8000, type=int)
@click.option("--columns", "cols")
@click.option("--schema", type=click.Path(exists=True))
@click.option("--count", type=int, default=10)
def mock(port, cols, schema, count):
    """Start a mock API server with auto-generated endpoints."""
    from forge.server import start_mock_server

    column_list = _parse_columns(cols)
    start_mock_server(port=port, columns=column_list, schema_file=schema)


# ── synthesize ─────────────────────────────────────────────────────────
@cli.command()
@click.argument("source")
@click.option("-f", "--format", "fmt")
@click.option("--count", type=int, default=10)
def synthesize(source, fmt, count):
    """Synthesize new data from a source schema."""
    try:
        records = Pipeline().read(source, fmt).apply("synthesize", count=count).run()
        for r in records:
            click.echo(r)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


# ── watch ──────────────────────────────────────────────────────────────
@cli.command()
@click.argument("source")
@click.argument("destination")
@click.option("-m", "--mode")
@click.option("--interval", type=float, default=5.0)
def watch(source, destination, mode, interval):
    """Watch a file and re-process on every change."""
    from forge.watch import watch_and_process
    click.echo(f"👀 Watching {source} → {destination} (every {interval}s)")
    watch_and_process(source, destination, mode, interval)


# ── shell ──────────────────────────────────────────────────────────────
@cli.command()
def shell():
    """Start an interactive Forge REPL."""
    from forge.repl import start_repl
    start_repl()


# ── stream ─────────────────────────────────────────────────────────────
@cli.command()
@click.option("-p", "--port", default=8765, type=int)
@click.option("--columns", "cols")
@click.option("--interval", type=float, default=1.0)
def stream(port, cols, interval):
    """Start a WebSocket server that streams generated records."""
    from forge.ws_server import start_ws_server
    column_list = _parse_columns(cols)
    click.echo(f"Starting WebSocket stream on ws://0.0.0.0:{port}")
    start_ws_server(port=port, columns=column_list, interval=interval)


if __name__ == "__main__":
    cli()
