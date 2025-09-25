#!/usr/bin/env python
"""
Script to create Qdrant collections for parliamentary data.

Creates collections for:
- Legislators (Diputados and Senadores)
- Issues/Matters (Asuntos) for both chambers
- Political Blocks (Bloques) for both chambers
"""

import argparse
import sqlite3
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

from modulo_consultas_parlamentarias.logger import get_logger
from modulo_consultas_parlamentarias.retriever import Retriever
from modulo_consultas_parlamentarias.retriever.retriever import TextChunk

logger = get_logger(__name__)


# Load environment variables from .env file if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)


@lru_cache()
def get_openai_embeddings(
    model: str = "text-embedding-3-large",
    dimensions: int = 256,
) -> OpenAIEmbeddings:
    """
    Get OpenAI embeddings model.

    Args:
        model (str): The OpenAI model to use for embeddings. Default is "text-embedding-3-large".
        dimensions (int): The dimensionality of the embeddings. Default is 256.

    Returns:
        OpenAIEmbeddings: An instance of OpenAIEmbeddings with the specified model and dimensions
    """  # noqa: E501
    return OpenAIEmbeddings(model=model, dimensions=dimensions)


def row_to_text_chunk_legislador(row: pd.Series) -> TextChunk:
    """
    Convert legislator row to a TextChunk.

    Args:
        row (pd.Series): A pandas Series representing a legislator.

    Returns:
        TextChunk: A TextChunk with the legislator's name as text and other details as metadata.
    """  # noqa: E501
    metadata = row.to_dict()
    text = metadata.pop("nombre")

    return TextChunk(text=text, metadata=metadata)


def row_to_text_chunk_asunto(row: pd.Series) -> TextChunk:
    """
    Convert asunto row to a TextChunk.

    Args:
        row (pd.Series): A pandas Series representing an asunto.

    Returns:
        TextChunk: A TextChunk with the asunto's title as text and other details as metadata.
    """  # noqa: E501
    text = " - ".join([row[col] or "" for col in ["asunto", "titulo"]])
    metadata = row.to_dict()

    return TextChunk(text=text, metadata=metadata)


def row_to_text_chunk_bloque(row: pd.Series) -> TextChunk:
    """
    Convert bloque row to a TextChunk.

    Args:
        row (pd.Series): A pandas Series representing un bloque.

    Returns:
        TextChunk: A TextChunk with the bloque's name as text and other details as metadata.
    """  # noqa: E501
    metadata = row.to_dict()
    text = metadata.pop("bloque")

    return TextChunk(text=text, metadata=metadata)


def create_collection_from_table(
    retriever: Retriever,
    conn: sqlite3.Connection,
    table_name: str,
    collection_name: str,
    converter_func,
    force: bool = False,
) -> None:
    """
    Create and populate a collection from a database table.

    Args:
        retriever (Retriever): The Retriever instance to use for collection operations.
        conn (sqlite3.Connection): SQLite database connection.
        table_name (str): The name of the database table to read data from.
        collection_name (str): The name of the collection to create.
        converter_func (callable): Function to convert a row to a TextChunk.
        force (bool): If True, delete the collection if it exists before creating a new one.
                      If False, skip creation if the collection already exists.
                      Default is False.
    """
    logger.info(f"Creating collection: {collection_name}...")

    # If force is True, delete the collection if it exists
    if force and retriever.qadrant_client.collection_exists(collection_name):
        logger.info(f"Deleting existing collection {collection_name}...")
        retriever.qadrant_client.delete_collection(collection_name)

    # Skip if collection exists and force is False
    if (
        retriever.qadrant_client.collection_exists(collection_name)
        and not force
    ):
        logger.info(f"Collection {collection_name} already exists. Skipping.")
        return

    # Read data from table
    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
    logger.info(f"Read {len(df)} rows from {table_name}")

    # Convert rows to TextChunks
    documents = [converter_func(row) for _, row in df.iterrows()]

    # Create and populate collection
    retriever.create_collection(collection_name=collection_name)
    retriever.insert_text_chunks(
        collection_name=collection_name,
        text_chunks=documents,
    )

    logger.info(
        f"Successfully created collection {collection_name} with {len(documents)} documents"
    )


def main(db_path: str, force: bool = False) -> None:
    """
    Main function to create all collections.

    Args:
        db_path (str): Path to the SQLite database file.
        force (bool): If True, force recreation of collections if they already exist.
                      Default is False.
    """
    # Initialize embeddings and retriever
    dense_embeddings = get_openai_embeddings()
    retriever = Retriever(dense_embeddings=dense_embeddings)

    # Connect to database
    conn = sqlite3.connect(db_path)

    # Create collections for legisladores
    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="legisladores_diputados",
        collection_name="legisladores-diputados",
        converter_func=row_to_text_chunk_legislador,
        force=force,
    )

    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="legisladores_senadores",
        collection_name="legisladores-senadores",
        converter_func=row_to_text_chunk_legislador,
        force=force,
    )

    # Create collections for asuntos
    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="asuntos_diputados",
        collection_name="asuntos-diputados",
        converter_func=row_to_text_chunk_asunto,
        force=force,
    )

    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="asuntos_senadores",
        collection_name="asuntos-senadores",
        converter_func=row_to_text_chunk_asunto,
        force=force,
    )

    # Create collections for bloques
    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="bloques_diputados",
        collection_name="bloques-diputados",
        converter_func=row_to_text_chunk_bloque,
        force=force,
    )

    create_collection_from_table(
        retriever=retriever,
        conn=conn,
        table_name="bloques_senadores",
        collection_name="bloques-senadores",
        converter_func=row_to_text_chunk_bloque,
        force=force,
    )

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Qdrant collections for parliamentary data"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="resources/db/data.db",
        help="Path to the SQLite database file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of collections if they already exist",
    )

    args = parser.parse_args()
    main(db_path=args.db_path, force=args.force)
