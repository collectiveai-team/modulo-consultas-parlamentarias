"""Database management CLI script."""

import argparse
import sys
from pathlib import Path

from modulo_consultas_parlamentarias.db.engine import create_db_and_tables
from modulo_consultas_parlamentarias.logger import get_logger
from scripts.populate_db import TABLE_CHOICES, populate_from_csv

logger = get_logger(__name__)


def create_tables():
    """Create database tables."""
    try:
        create_db_and_tables()
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def populate_data(
    csv_dir: str | None = None, table: str | None = None
) -> bool:
    """
    Populate database with CSV data.

    Args:
        csv_dir (str | None): Path to CSV directory. If None, uses default path
        table (str | None): Specific table to populate. If None, populates all tables.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        csv_path = Path(csv_dir) if csv_dir else Path("resources/data/tables")

        if not csv_path.exists():
            logger.error(f"CSV directory not found: {csv_path}")
            return False

        results = populate_from_csv(csv_path, table)
        logger.info(f"Data population completed: {results}")
        return True
    except Exception as e:
        logger.error(f"Failed to populate data: {e}")
        return False


def init_database(csv_dir: str | None = None) -> bool:
    """
    Initialize database with tables and data.

    Args:
        csv_dir (str | None): Path to CSV directory. If None, uses default path.

    Returns:
        bool: True if successful, False otherwise.
    """
    logger.info("Initializing database...")

    # Create tables first
    if not create_tables():
        return False

    # Then populate with data
    if not populate_data(csv_dir):
        return False

    logger.info("Database initialization completed successfully")
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Database management CLI")
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands"
    )

    # Create tables command
    subparsers.add_parser("create-tables", help="Create database tables")

    # Populate data command
    populate_parser = subparsers.add_parser(
        "populate", help="Populate database with CSV data"
    )
    populate_parser.add_argument(
        "--csv-dir",
        type=str,
        help="Path to CSV directory (default: resources/data/tables)",
    )
    populate_parser.add_argument(
        "--table",
        type=str,
        choices=TABLE_CHOICES,
        default="all",
        help="Which table to populate (default: all)",
    )

    # Initialize database command
    init_parser = subparsers.add_parser(
        "init", help="Initialize database (create tables + populate data)"
    )
    init_parser.add_argument(
        "--csv-dir",
        type=str,
        help="Path to CSV directory (default: resources/data/tables)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    success = False

    if args.command == "create-tables":
        success = create_tables()
    elif args.command == "populate":
        success = populate_data(args.csv_dir, args.table)
    elif args.command == "init":
        success = init_database(args.csv_dir)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
