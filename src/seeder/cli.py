from typing import Annotated, Any, Dict, List
import sys
import typer
from rich.console import Console
from rich.table import Table
from seeder.schema import SchemaInspector
from seeder.topo_sort import topological_sort_tables
from seeder.generator import LLMRowGenerator, generate_sql_inserts
from sqlalchemy import create_engine, text

app = typer.Typer(help="AI-Native Relational Database Seeder CLI")
console = Console()


@app.callback()
def callback():
    """AI-Native Relational Database Seeder CLI"""
    pass


@app.command("generate")
def generate(
    db_url: Annotated[str, typer.Option("--db-url", help="Database connection URL (Postgres or SQLite)")],
    rows: Annotated[int, typer.Option("--rows", "-n", help="Number of rows to generate per table")] = 5,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Print SQL statements without executing against DB")] = True,
):
    """Inspect database schema, perform topological sorting, and generate realistic synthetic seed data."""
    console.print(f"[bold blue]AI-Native Database Seeder v0.1.0[/bold blue]")
    console.print(f"Connecting to database: [cyan]{db_url}[/cyan]...")

    # Step 1: Introspect Database Schema
    inspector = SchemaInspector(db_url)
    schemas = inspector.inspect_database()

    if not schemas:
        console.print("[bold red]Error:[/bold red] No tables found in database.")
        raise typer.Exit(code=1)

    console.print(f"Found [green]{len(schemas)}[/green] tables.")

    # Step 2: Topological Sorting (Parent tables first)
    sorted_table_names = topological_sort_tables(schemas)

    console.print("\n[bold yellow]Topological Table Order (FK Dependencies Resolved):[/bold yellow]")
    topo_table = Table(show_header=True, header_style="bold magenta")
    topo_table.add_column("Order", style="dim", width=6)
    topo_table.add_column("Table Name")
    topo_table.add_column("Parent Tables (FK References)")

    for idx, name in enumerate(sorted_table_names, 1):
        parents = ", ".join(schemas[name].parent_tables) or "None (Root Table)"
        topo_table.add_row(str(idx), name, parents)

    console.print(topo_table)

    # Step 3: LLM Seed Generation per Table in Topological Order
    generator = LLMRowGenerator()
    generated_parent_ids: Dict[str, Dict[str, List[Any]]] = {}
    all_sql_statements: List[str] = []

    console.print(f"\n[bold green]Generating {rows} rows per table with Cross-Column Cohesion...[/bold green]\n")

    for table_name in sorted_table_names:
        schema = schemas[table_name]
        console.print(f"Generating rows for [bold cyan]{table_name}[/bold cyan]...")

        rows_data = generator.generate_rows_for_table(schema, count=rows, available_parent_ids=generated_parent_ids)

        # Store generated IDs for FK resolution in child tables
        generated_parent_ids[table_name] = {}
        for col in schema.columns:
            col_vals = [r[col.name] for r in rows_data if col.name in r and r[col.name] is not None]
            if col_vals:
                generated_parent_ids[table_name][col.name] = col_vals

        # Build SQL INSERT Statements
        sql_list = generate_sql_inserts(table_name, rows_data)
        all_sql_statements.extend(sql_list)

    # Step 4: Output / Execute
    if dry_run:
        console.print("\n[bold yellow]=== DRY RUN: Generated SQL Seed Script ===[/bold yellow]\n")
        for stmt in all_sql_statements:
            console.print(stmt)
        console.print("\n[bold green][OK] Dry-run completed successfully. Zero changes committed to DB.[/bold green]")
    else:
        console.print("\n[bold blue]Executing SQL INSERT statements against DB...[/bold blue]")
        engine = create_engine(db_url)
        with engine.begin() as conn:
            for stmt in all_sql_statements:
                conn.execute(text(stmt))
        console.print(f"[bold green][OK] Successfully inserted {len(all_sql_statements)} rows across {len(schemas)} tables![/bold green]")


def main():
    app()


if __name__ == "__main__":
    main()
