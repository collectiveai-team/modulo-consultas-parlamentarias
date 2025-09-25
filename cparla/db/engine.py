"""Database engine and session management."""

import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resources/db/data.db")

# Create engine with proper configuration for SQLite
engine = create_engine(
    DATABASE_URL,
    echo=bool(os.getenv("DB_ECHO", False)),
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)


def get_engine():
    """Get the database engine."""
    return engine


def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    """Create database and tables."""
    SQLModel.metadata.create_all(engine)
