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


if __name__ == "__main__":
    cli()
