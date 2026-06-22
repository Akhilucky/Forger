import sys
import click

from forge.core.pipeline import Pipeline
from forge.core.plugin import Registry


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="forge")
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("source")
@click.argument("destination")
@click.option("-m", "--mode", help="Transformation mode to apply")
@click.option("-f", "--from-format", "from_fmt", help="Source format override")
@click.option("-t", "--to-format", "to_fmt", help="Destination format override")
@click.option("--count", type=int, help="Row count (synthesize/scale/compress)")
@click.option("--columns", help="Comma-separated columns (anonymize)")
@click.option("--table", help="Table name (SQLite/SQL)")
@click.option("--pretty/--no-pretty", default=True, help="Pretty print JSON")
@click.option("--progress/--no-progress", default=False, help="Show progress")
@click.option("--duplicates", type=int, help="Duplicates to inject (stress)")
def run(source, destination, mode, from_fmt, to_fmt, count, columns, table, pretty, progress, duplicates):
    """Compile SOURCE into DESTINATION [--mode MODE]."""
    kwargs = {}
    if count:
        kwargs["count"] = count
    if columns:
        kwargs["columns"] = [c.strip() for c in columns.split(",")]
    if table:
        kwargs["table"] = table
    if duplicates:
        kwargs["duplicates"] = duplicates

    try:
        records = Pipeline.go(
            source=source,
            destination=destination,
            mode=mode,
            source_format=from_fmt,
            dest_format=to_fmt,
            **kwargs,
        )
        click.echo(f"✓ Compiled {len(records)} records → {destination}")
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("source")
@click.option("-f", "--format", "fmt", help="Source format")
@click.option("--head", type=int, default=5, help="Rows to show")
def inspect(source, fmt, head):
    """Show schema and preview of SOURCE."""
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


@cli.command()
@click.argument("source")
@click.option("-f", "--format", "fmt", help="Source format")
@click.option("--count", type=int, default=10, help="Records to synthesize")
def synthesize(source, fmt, count):
    """Synthesize new data from SOURCE schema."""
    try:
        records = Pipeline().read(source, fmt).apply("synthesize", count=count).run()
        for r in records:
            click.echo(r)
    except Exception as e:
        click.echo(f"✗ {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("-o", "--output", default=None, help="Output file (optional)")
@click.option("--format", "fmt", default="json", help="Output format (json, csv, yaml)")
@click.option("--count", type=int, default=10, help="Number of records to generate")
@click.option("--columns", "cols", required=True,
              help="Column spec: 'name:type,name:type,...' or 'name,name,...'")
@click.option("--sample", type=click.Path(exists=True),
              help="Sample file to learn patterns from")
@click.option("--iterations", type=int, default=1,
              help="Self-iteration rounds for quality improvement")
@click.option("--llm", is_flag=True, default=False,
              help="Use tiny local LLM (ollama/llama.cpp) for generation")
@click.option("--model", help="Path to llama.cpp model (requires --llm)")
@click.option("--show", is_flag=True, default=False, help="Print generated records")
def generate(output, fmt, count, cols, sample, iterations, llm, model, show):
    """Generate datasets from column specifications."""
    from forge.generator.engine import Engine

    columns = []
    for col_spec in cols.split(","):
        col_spec = col_spec.strip()
        if ":" in col_spec:
            name, typ = col_spec.split(":", 1)
            columns.append({"name": name.strip(), "type": typ.strip()})
        else:
            columns.append({"name": col_spec, "type": "string"})

    engine = Engine()
    sample_records = []
    if sample:
        sample_records = Pipeline().read(sample).run()
        engine.learn(sample_records)
        click.echo(f"✓ Learned from {len(sample_records)} sample records", err=True)

    kwargs = {"count": count, "llm": llm, "model": model, "iterations": iterations}
    records = engine.generate_from_spec(columns, count, llm, model)

    if iterations > 1 and sample_records:
        engine.learn(sample_records)
        best = engine.self_iterate(count, iterations, llm, model)
        if best:
            records = best
        click.echo(f"✓ Self-iterated {iterations}x for quality", err=True)

    if output:
        dest_pipe = Pipeline()
        dest_pipe._records = records
        writer = Registry.get_writer(fmt or "json")
        if writer:
            writer().write(records, output)
            click.echo(f"✓ Generated {len(records)} records → {output}")
    elif show or not output:
        import json as j
        click.echo(j.dumps(records, indent=2, default=str))
    else:
        click.echo(f"✓ Generated {len(records)} records")

    return records


if __name__ == "__main__":
    cli()
