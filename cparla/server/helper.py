from typing import Any

from sqlalchemy import ForeignKeyConstraint, Table
from sqlalchemy.sql.schema import Column as SAColumn
from sqlmodel import SQLModel

ModelOrTableOrName = type[SQLModel] | Table | str


def get_table_info_sqlmodel(obj: ModelOrTableOrName) -> dict[str, Any]:
    """
    Return table metadata (columns, PK, FKs, indexes) using SQLModel/SQLAlchemy Table objects,
    mirroring the structure produced by Inspector.

    Args:
        obj (ModelOrTableOrName): A SQLModel class, a SQLAlchemy Table, or a string in the form 'schema.table' or 'table'.

    Returns:
        dict[str, Any]: A dictionary containing table metadata.
    """  # noqa: E501
    table, table_name = _resolve_table(obj)

    # --- columns ---
    columns_info: list[dict[str, Any]] = []
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
    fk_info: list[dict[str, Any]] = []
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
    idx_info: list[dict[str, Any]] = []
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


def _resolve_table(obj: ModelOrTableOrName) -> tuple[Table, str]:
    """
    Accept a SQLModel class, a Table, or 'schema.table'/'table' string and return (Table, printable_name).

    Args:
        obj (ModelOrTableOrName): A SQLModel class, a SQLAlchemy Table, or a string in the form 'schema.table' or 'table'.

    Returns:
        tuple[Table, str]: A tuple containing the SQLAlchemy Table object and a printable table
    """  # noqa: E501
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


def _split_schema_table(s: str) -> tuple[str | None, str]:
    """
    Split 'schema.table' or 'table' into (schema, table).

    Args:
        s (str): The input string.

    Returns:
        tuple[str | None, str]: A tuple containing the schema (or None) and the table name.
    """  # noqa: E501
    return (s.split(".", 1)[0], s.split(".", 1)[1]) if "." in s else (None, s)


def _stringify_default(col: SAColumn) -> str | None:
    """
    Convert Python-side or server-side defaults to a string similar to Inspector.get_columns()['default'].
    Preference: server_default (DDL) > default (Python).

    Args:
        col (SAColumn): The SQLAlchemy Column object.

    Returns:
        str | None: A string representation of the default value, or None if no default is set.
    """  # noqa: E501
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
