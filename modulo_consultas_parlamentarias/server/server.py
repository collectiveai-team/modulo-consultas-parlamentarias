from functools import lru_cache
from typing import Any, Literal

from fastmcp import FastMCP
from langchain_openai import OpenAIEmbeddings
from sqlmodel import Session, text

from modulo_consultas_parlamentarias.db.engine import get_engine
from modulo_consultas_parlamentarias.db.models import (
    DBAsuntoDiputados,
    DBAsuntoSenadores,
    DBBloqueDiputados,
    DBBloqueSenadores,
    DBLegisladorDiputados,
    DBLegisladorSenadores,
    DBVotacionDiputados,
    DBVotacionSenadores,
)
from modulo_consultas_parlamentarias.retriever import Retriever
from modulo_consultas_parlamentarias.server.helper import (
    get_table_info_sqlmodel,
)

# Create server
mcp = FastMCP("Módulo de Consultas Parlamentarias")


@lru_cache()
def get_retriever() -> Retriever:
    """
    Initialize and return a cached instance of the Retriever.

    Returns:
        Retriever: The vector search retriever instance
    """
    # Initialize OpenAI embeddings
    dense_embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large",
        dimensions=256,
    )

    # Initialize the retriever
    return Retriever(dense_embeddings=dense_embeddings)


# Define valid collections for search
COLLECTIONS = [
    "legisladores-diputados",
    "legisladores-senadores",
    "bloques-diputados",
    "bloques-senadores",
    "asuntos-diputados",
    "asuntos-senadores",
]

TABLES_MAP = {
    "asuntos_diputados": DBAsuntoDiputados,
    "asuntos_senadores": DBAsuntoSenadores,
    "bloques_diputados": DBBloqueDiputados,
    "bloques_senadores": DBBloqueSenadores,
    "legisladores_diputados": DBLegisladorDiputados,
    "legisladores_senadores": DBLegisladorSenadores,
    "votaciones_diputados": DBVotacionDiputados,
    "votaciones_senadores": DBVotacionSenadores,
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

    Returns:
        list[dict[str, Any]]: A JSON-serializable list with names and basic metadata.
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

    Args:
        table_name (str): The name of the table.

    Returns:
        dict[str, Any]: A dictionary containing table metadata.
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

    Args:
        table_name (str): The name of the table.
        limit (int): The maximum number of rows to return. Default is 50.

    Returns:
        list[dict[str, Any]]: A list of rows represented as dictionaries.
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
def run_select(
    sql_query: str, limit: int | None = 100
) -> list[dict[str, Any]]:
    """
    Run a read-only SELECT with an optional LIMIT guard. Rejects non-SELECT statements for safety.

    Args:
        sql_query (str): The SQL SELECT query to execute.
        limit (int | None): Optional limit to apply if the query does not already have one.
                           If None, no limit is applied. Default is 100.

    Returns:
        list[dict[str, Any]]: A list of rows represented as dictionaries.
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
                (
                    {"value": row}
                    if not isinstance(row, (list, tuple))
                    else {"values": list(row)}
                )
                for row in result
            ]
    return []


@mcp.tool(
    name="search_collection",
    description="Search for relevant documents in a collection using hybrid search (dense embeddings + sparse BM25).",
    tags=["Search"],
)
async def search_collection(
    query: str,
    collection_name: str,
    k: int = 10,
    search_type: Literal["hybrid", "dense"] = "hybrid",
) -> list[dict[str, Any]]:
    """
    Search for relevant documents in a collection using hybrid search.

    Args:
        query (str): The search query or term to retrieve.
        collection_name (str): Name of the collection to query. Examples: "legisladores-diputados",
                              "legisladores-senadores", "bloques-diputados", "bloques-senadores",
                              "asuntos-diputados", "asuntos-senadores".
        k (int, optional): Maximum number of results to return. Defaults to 10.
        search_type (str, optional): Type of search to perform. Options: "hybrid", "dense". Defaults to "hybrid".

    Returns:
        list[dict[str, Any]]: List of documents with metadata and relevance scores.
    """
    if collection_name not in COLLECTIONS:
        raise ValueError(
            f"Collection '{collection_name}' not found. Valid collections: {', '.join(COLLECTIONS)}"
        )

    retriever = get_retriever()

    if search_type == "hybrid":
        results = await retriever.hybrid_search(
            collection_name=collection_name,
            query=query,
            k=k,
        )
    else:
        results = await retriever.dense_search(
            collection_name=collection_name,
            query=query,
            k=k,
        )

    # Convert Pydantic models to dictionaries
    return [result.model_dump() for result in results]


@mcp.tool(
    name="list_collections",
    description="List all available collections for search.",
    tags=["Search"],
)
def list_collections() -> list[str]:
    """
    List all available collections for searching.

    Returns:
        list[str]: List of collection names available for search.
    """
    return COLLECTIONS


@mcp.tool(
    name="list_tools",
    description="List all available tools.",
    tags=["Utility"],
)
async def list_tools() -> list[dict[str, Any]]:
    """
    List all available tools.

    Returns:
        list[dict[str, Any]]: List of tool names and descriptions available for use.
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "tags": tool.tags,
        }
        for tool in await mcp.list_tools()
    ]


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
