from typing import Any, Dict, List, Optional, Tuple, Union
from sqlmodel import SQLModel
from sqlalchemy import Table, ForeignKeyConstraint
from sqlalchemy.sql.schema import Column as SAColumn


ModelOrTableOrName = Union[type[SQLModel], Table, str]


def get_table_info_sqlmodel(obj: ModelOrTableOrName) -> Dict[str, Any]:
    """
    Return table metadata (columns, PK, FKs, indexes) using SQLModel/SQLAlchemy Table objects,
    mirroring the structure produced by Inspector.
    """
    table, table_name = _resolve_table(obj)

    # --- columns ---
    columns_info: List[Dict[str, Any]] = []
    for col in table.columns:  # type: ignore[attr-defined]
        columns_info.append(
            {
                "name": col.name,
                "type": str(col.type),
                "nullable": bool(col.nullable),
                "default": _stringify_default(col),
            }
        )

    # --- primary key ---
    primary_key = [col.name for col in table.primary_key.columns]  # type: ignore[attr-defined]

    # --- foreign keys (grouped by constraint) ---
    fk_info: List[Dict[str, Any]] = []
    for c in table.constraints:  # type: ignore[attr-defined]
        if isinstance(c, ForeignKeyConstraint):
            # Each FK constraint may have multiple column pairs
            constrained_cols = [elem.parent.name for elem in c.elements]
            referred_table = getattr(c.referred_table, "name", None)
            referred_schema = getattr(c.referred_table, "schema", None)
            referred_cols = [elem.column.name for elem in c.elements]
            fk_info.append(
                {
                    "constrained_columns": constrained_cols,
                    "referred_schema": referred_schema,
                    "referred_table": referred_table,
                    "referred_columns": referred_cols,
                    "name": c.name,
                }
            )

    # --- indexes ---
    idx_info: List[Dict[str, Any]] = []
    for ix in getattr(table, "indexes", set()):  # type: ignore[attr-defined]
        # Index.columns is a ColumnCollection; fall back to expressions for computed indexes
        col_names = list(ix.columns.keys()) if hasattr(ix, "columns") else []
        if not col_names and hasattr(ix, "expressions"):
            # Best-effort names from expressions (may be Column objects or SQL expressions)
            col_names = [getattr(expr, "name", str(expr)) for expr in ix.expressions]
        idx_info.append(
            {
                "name": ix.name,
                "unique": bool(getattr(ix, "unique", False)),
                "column_names": col_names,
            }
        )

    return {
        "table_name": table_name,
        "columns": columns_info,
        "primary_key": primary_key,
        "foreign_keys": fk_info,
        "indexes": idx_info,
    }


def _resolve_table(obj: ModelOrTableOrName) -> Tuple[Table, str]:
    """Accept a SQLModel class, a Table, or 'schema.table'/'table' string and return (Table, printable_name)."""
    if isinstance(obj, str):
        schema, name = _split_schema_table(obj)
        # SQLAlchemy stores keys in metadata.tables as 'schema.table' (with dot) if schema is present
        key = f"{schema}.{name}" if schema else name
        table = SQLModel.metadata.tables.get(key)
        if table is None:
            # Try without schema if user passed only the bare name
            table = SQLModel.metadata.tables.get(name)
        if table is None:
            raise KeyError(f"Table '{obj}' not found in SQLModel.metadata.tables")
        printable = f"{table.schema}.{table.name}" if table.schema else table.name
        return table, printable

    if isinstance(obj, Table):
        printable = f"{obj.schema}.{obj.name}" if obj.schema else obj.name
        return obj, printable

    # Assume SQLModel subclass
    if hasattr(obj, "__table__"):
        table: Table = obj.__table__  # type: ignore[assignment]
        printable = f"{table.schema}.{table.name}" if table.schema else table.name
        return table, printable

    raise TypeError("Expected SQLModel class, SQLAlchemy Table, or table-name string.")


def _split_schema_table(s: str) -> Tuple[Optional[str], str]:
    return (s.split(".", 1)[0], s.split(".", 1)[1]) if "." in s else (None, s)


def _stringify_default(col: SAColumn) -> Optional[str]:
    """
    Convert Python-side or server-side defaults to a string similar to Inspector.get_columns()['default'].
    Preference: server_default (DDL) > default (Python).
    """
    # server_default is a DefaultClause or textual clause; try to render it
    if col.server_default is not None:
        # Best effort string form (e.g., "nextval('seq'::regclass)" or "CURRENT_TIMESTAMP")
        try:
            txt = str(col.server_default.arg.text)  # type: ignore[attr-defined]
        except Exception:
            txt = str(getattr(col.server_default, "arg", col.server_default))
        return txt

    if col.default is not None:
        # Could be a Python callable or a scalar.
        arg = getattr(col.default, "arg", col.default)
        try:
            return repr(arg() if callable(arg) else arg)
        except Exception:
            return repr(arg)

    return None
