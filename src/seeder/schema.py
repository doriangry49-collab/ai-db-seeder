from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, inspect


@dataclass
class ColumnInfo:
    name: str
    type_name: str
    nullable: bool = True
    default: Optional[str] = None
    is_pk: bool = False
    is_fk: bool = False
    fk_target_table: Optional[str] = None
    fk_target_column: Optional[str] = None


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnInfo] = field(default_factory=list)
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    parent_tables: List[str] = field(default_factory=list)


class SchemaInspector:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.engine = create_engine(db_url)
        self.inspector = inspect(self.engine)

    def get_all_tables(self) -> List[str]:
        return self.inspector.get_table_names()

    def get_table_schema(self, table_name: str) -> TableSchema:
        raw_cols = self.inspector.get_columns(table_name)
        pk_constraint = self.inspector.get_pk_constraint(table_name)
        pk_cols = set(pk_constraint.get("constrained_columns", []))
        fk_list = self.inspector.get_foreign_keys(table_name)

        fk_map: Dict[str, Dict[str, str]] = {}
        parent_tables: set = set()

        for fk in fk_list:
            target_table = fk.get("referred_table")
            if target_table:
                parent_tables.add(target_table)
            constrained_cols = fk.get("constrained_columns", [])
            referred_cols = fk.get("referred_columns", [])
            for c_col, r_col in zip(constrained_cols, referred_cols):
                fk_map[c_col] = {
                    "target_table": target_table,
                    "target_column": r_col,
                }

        columns: List[ColumnInfo] = []
        for c in raw_cols:
            col_name = c["name"]
            is_pk = col_name in pk_cols
            is_fk = col_name in fk_map
            fk_target_table = fk_map[col_name]["target_table"] if is_fk else None
            fk_target_column = fk_map[col_name]["target_column"] if is_fk else None

            columns.append(
                ColumnInfo(
                    name=col_name,
                    type_name=str(c["type"]),
                    nullable=c.get("nullable", True),
                    default=str(c.get("default")) if c.get("default") is not None else None,
                    is_pk=is_pk,
                    is_fk=is_fk,
                    fk_target_table=fk_target_table,
                    fk_target_column=fk_target_column,
                )
            )

        return TableSchema(
            name=table_name,
            columns=columns,
            foreign_keys=fk_list,
            parent_tables=list(parent_tables),
        )

    def inspect_database(self) -> Dict[str, TableSchema]:
        schemas = {}
        for t in self.get_all_tables():
            schemas[t] = self.get_table_schema(t)
        return schemas
