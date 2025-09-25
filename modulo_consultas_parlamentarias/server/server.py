from sqlmodel import Session, text
from typing import Any

from fastmcp import FastMCP
from modulo_consultas_parlamentarias.db.engine import get_engine
from modulo_consultas_parlamentarias.db.models import (
    DBAsuntoDiputado,
    DBBloqueDiputado,
    DBLegisladorDiputado,
    DBVotacionDiputado,
)
from modulo_consultas_parlamentarias.server.helper import get_table_info_sqlmodel

# Create server - dependencies are now in fastmcp.json
mcp = FastMCP("Screenshot Demo")

TABLES_MAP = {
    "asuntos_diputados": DBAsuntoDiputado,
    "bloques_diputados": DBBloqueDiputado,
    "legisladores_diputados": DBLegisladorDiputado,
    "votaciones_diputados": DBVotacionDiputado,
}


# @mcp.resource(
#     uri="db://tables",
#     description="List available tables.",
#     annotations={"audience": ["assistant"], "priority": 1.0},
#     tags=["Database"],
# )
@mcp.tool(
    name="list_tables",
    description="List available tables.",
    tags=["Database"],
)
def list_tables() -> list[dict[str, Any]]:
    """
    List available tables.
    Returns a JSON-serializable list with names and basic metadata.
    """
    tables = []
    for t in TABLES_MAP:
        tables.append(
            {
                "table": t,
                "uri": f"db://schema/{t}",
                "preview": f"db://preview/{t}?limit=50",
            }
        )
    return tables  # FastMCP will package this as a resource with JSON text


# @mcp.resource(
#     uri="db://schema/{table_name}",
#     description="Return detailed schema for a table like 'public.users' or 'users' (defaults to first match).",
#     annotations={"audience": ["assistant"], "priority": 1.0},
#     tags=["Database"],
# )
@mcp.tool(
    name="table_schema",
    description="Return detailed schema for a table like 'public.users' or 'users' (defaults to first match).",
    tags=["Database"],
)
def table_schema(table_name: str) -> dict[str, Any]:
    """
    Return detailed schema for a table like 'public.users' or 'users' (defaults to first match).
    Includes columns, PK, FKs, indexes.
    """
    sql_model = TABLES_MAP.get(table_name)
    if not sql_model:
        raise ValueError(f"Table {table_name} not found.")

    return get_table_info_sqlmodel(sql_model)


# @mcp.resource(
#     uri="db://preview/{table_name}",
#     description="Return first rows of a table. Supports ?limit= in the URI.",
#     annotations={"audience": ["assistant"], "priority": 1.0},
#     tags=["Database"],
# )
@mcp.tool(
    name="table_preview",
    description="Return first rows of a table. Supports ?limit= in the URI.",
    tags=["Database"],
)
def table_preview(table_name: str, limit: int = 50) -> list[dict[str, Any]]:
    """
    Return first rows of a table. Supports ?limit= in the URI.
    """
    sql_model = TABLES_MAP.get(table_name)
    if not sql_model:
        raise ValueError(f"Table {table_name} not found.")

    with Session(get_engine()) as session:
        result = session.exec(sql_model.select().limit(limit)).all()
    return [dict(r) for r in result]


@mcp.tool(
    name="run_select",
    description="Run a read-only SELECT with an optional LIMIT guard. Rejects non-SELECT statements for safety.",
    tags=["Database"],
)
def run_select(sql_query: str, limit: int | None = 100) -> list[dict[str, Any]]:
    """
    Run a read-only SELECT with an optional LIMIT guard.
    Rejects non-SELECT statements for safety.
    """
    q = sql_query.strip().rstrip(";")
    if not q.lower().startswith("select"):
        raise ValueError("Only SELECT statements are permitted.")
    if " limit " not in q.lower() and limit:
        q = f"{q} LIMIT {int(limit)}"

    with Session(get_engine()) as session:
        result = session.exec(text(q)).all()

    # Convert result rows to dictionaries
    # For raw SQL queries, we need to handle the result differently
    if result:
        # Get column names from the first row
        first_row = result[0]
        if hasattr(first_row, "_mapping"):
            # SQLAlchemy Row object with _mapping
            return [dict(row._mapping) for row in result]
        elif hasattr(first_row, "__dict__"):
            # SQLModel object
            return [dict(row) for row in result]
        else:
            # Scalar values or tuples - convert to list of values
            return [
                {"value": row}
                if not isinstance(row, (list, tuple))
                else {"values": list(row)}
                for row in result
            ]
    return []


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
