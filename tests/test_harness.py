import os
import sqlite3
import sys
import gc
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from seeder.schema import SchemaInspector
from seeder.topo_sort import topological_sort_tables
from seeder.generator import LLMRowGenerator, generate_sql_inserts


def setup_db(db_path: str, ddl_path: str):
    gc.collect()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall():
        if not row[0].startswith("sqlite_"):
            cursor.execute(f"DROP TABLE IF EXISTS {row[0]};")
    conn.commit()

    with open(ddl_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


def run_seeder_test(schema_name: str, db_file: str, ddl_file: str, rows_per_table: int = 5):
    print(f"\n=======================================================")
    print(f" TESTING UN-SEEN SCHEMA (Day 1.5): {schema_name.upper()}")
    print(f"=======================================================")

    root_dir = Path(__file__).parent.parent
    db_path = str(root_dir / db_file)
    ddl_path = str(root_dir / ddl_file)
    db_url = f"sqlite:///{db_path}"

    setup_db(db_path, ddl_path)

    inspector = SchemaInspector(db_url)
    schemas = inspector.inspect_database()

    print(f"1. Introspected Tables: {list(schemas.keys())}")

    sorted_tables = topological_sort_tables(schemas)
    print(f"2. Topological Sort Order: {sorted_tables}")

    generator = LLMRowGenerator()
    generated_parent_ids = {}
    all_sqls = []

    print(f"\n3. Generating Rows & SQL Inserts (rows per table = {rows_per_table}):\n")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for tname in sorted_tables:
        schema = schemas[tname]
        rows = generator.generate_rows_for_table(schema, count=rows_per_table, available_parent_ids=generated_parent_ids)

        sql_inserts = generate_sql_inserts(tname, rows)
        all_sqls.extend(sql_inserts)

        print(f"--- Table: {tname} (Parents: {schema.parent_tables}) ---")
        for s in sql_inserts:
            print(s)
            cursor.execute(s)
        conn.commit()

        # Capture generated PK IDs for child table FK resolution
        pk_col = next((c.name for c in schema.columns if c.is_pk), None)
        if pk_col:
            fetched_ids = [r[0] for r in cursor.execute(f"SELECT {pk_col} FROM {tname}").fetchall()]
            generated_parent_ids[tname] = {pk_col: fetched_ids}

        print()

    conn.close()
    print(f"[PASS] All {len(all_sqls)} INSERT statements executed successfully against DB with ZERO errors!")


if __name__ == "__main__":
    run_seeder_test("Support Tickets", "test_tickets.db", "tests/test_tickets_schema.sql", rows_per_table=5)
