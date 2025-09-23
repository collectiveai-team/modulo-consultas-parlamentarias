"""Data population script for loading CSV data into the database."""

import argparse
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
from sqlmodel import Session, select

from modulo_consultas_parlamentarias.db.engine import get_engine
from modulo_consultas_parlamentarias.db.models.asuntos import DBAsuntoDiputado
from modulo_consultas_parlamentarias.db.models.bloques import DBBloqueDiputado
from modulo_consultas_parlamentarias.db.models.legisladores import DBLegisladorDiputado
from modulo_consultas_parlamentarias.db.models.votaciones import DBVotacionDiputado
from modulo_consultas_parlamentarias.logger import get_logger

logger = get_logger(__name__)

# Default CSV data directory
DEFAULT_CSV_DIR = Path("resources/data/DecadaVotadaCSV")


class CSVDataPopulator:
    """Handles population of database from CSV files."""

    def __init__(self, csv_dir: Path | str = DEFAULT_CSV_DIR):
        self.csv_dir = Path(csv_dir)
        self.engine = get_engine()

    def _read_csv_safely(self, filepath: Path, separator: str = ";") -> pd.DataFrame:
        """Read CSV file safely with error handling."""
        try:
            df = pd.read_csv(filepath, sep=separator, encoding="utf-8")
            logger.info(f"Successfully read {len(df)} rows from {filepath}")
            return df
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, sep=separator, encoding="latin-1")
                logger.info(
                    f"Successfully read {len(df)} rows from {filepath} with latin-1 encoding"
                )
                return df
            except Exception as e:
                logger.error(f"Failed to read {filepath} with latin-1 encoding: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise

    def populate_asuntos_diputados(self) -> int:
        """Populate asuntos_diputados table from CSV."""
        csv_file = self.csv_dir / "asuntos-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names (remove spaces, convert to lowercase)
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "asuntoid": "asunto_id",
            "asunto": "asunto",
            "titulo": "titulo",
            "sumario": "sumario",
            "fecha": "fecha",
            "sesion": "sesion",
            "reunion": "reunion",
            "numeroreunion": "numero_reunion",
        }

        # Rename columns according to mapping
        df = df.rename(columns=column_mapping)

        # Drop rows with missing essential data
        df = df.dropna(subset=["asunto_id", "asunto"])

        # Convert to records
        records = df.to_dict("records")

        with Session(self.engine) as session:
            # Check existing records to avoid duplicates
            existing_ids = set(session.exec(select(DBAsuntoDiputado.asunto_id)).all())

            new_records = []
            for record in records:
                if record["asunto_id"] not in existing_ids:
                    # Create model instance
                    asunto = DBAsuntoDiputado(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBAsuntoDiputado.model_fields and pd.notna(v)
                        }
                    )
                    new_records.append(asunto)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(f"Added {len(new_records)} new asuntos_diputados records")
            else:
                logger.info("No new asuntos_diputados records to add")

        return len(new_records)

    def populate_bloques_diputados(self) -> int:
        """Populate bloques_diputados table from CSV."""
        csv_file = self.csv_dir / "bloques-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "bloqueid": "bloque_id",
            "bloque": "bloque",
        }

        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=["bloque_id", "bloque"])

        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(session.exec(select(DBBloqueDiputado.bloque_id)).all())

            new_records = []
            for record in records:
                if record["bloque_id"] not in existing_ids:
                    bloque = DBBloqueDiputado(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBBloqueDiputado.model_fields and pd.notna(v)
                        }
                    )
                    new_records.append(bloque)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(f"Added {len(new_records)} new bloques_diputados records")
            else:
                logger.info("No new bloques_diputados records to add")

        return len(new_records)

    def populate_legisladores_diputados(self) -> int:
        """Populate legisladores_diputados table from CSV."""
        csv_file = self.csv_dir / "diputados-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "diputadoid": "diputado_id",
            "nombre": "nombre",
            "apellido": "apellido",
            "nombrecompleto": "nombre_completo",
            "genero": "genero",
            "fechanacimiento": "fecha_nacimiento",
            "lugarnacimiento": "lugar_nacimiento",
            "partido": "partido",
            "bloqueid": "bloque_id",
            "distrito": "distrito",
            "email": "email",
            "telefono": "telefono",
            "imagen": "imagen",
        }

        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=["diputado_id", "nombre"])

        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBLegisladorDiputado.diputado_id)).all()
            )

            new_records = []
            for record in records:
                if record["diputado_id"] not in existing_ids:
                    legislador = DBLegisladorDiputado(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBLegisladorDiputado.model_fields and pd.notna(v)
                        }
                    )
                    new_records.append(legislador)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new legisladores_diputados records"
                )
            else:
                logger.info("No new legisladores_diputados records to add")

        return len(new_records)

    def populate_votaciones_diputados(self) -> int:
        """Populate votaciones_diputados table from CSV."""
        csv_file = self.csv_dir / "votaciones-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "asuntoid": "asunto_id",
            "diputadoid": "diputado_id",
            "bloqueid": "bloque_id",
            "voto": "voto",
            "fechavotacion": "fecha_votacion",
            "sesion": "sesion",
            "reunion": "reunion",
        }

        df = df.rename(columns=column_mapping)
        df = df.dropna(subset=["asunto_id", "diputado_id", "voto"])

        records = df.to_dict("records")

        with Session(self.engine) as session:
            # For votaciones, we'll check for duplicates based on combination of fields
            # since there's no unique ID in the CSV

            new_records = []
            for record in records:
                try:
                    # Check if this exact vote already exists
                    existing = session.exec(
                        select(DBVotacionDiputado).where(
                            DBVotacionDiputado.asunto_id == record["asunto_id"],
                            DBVotacionDiputado.diputado_id == record["diputado_id"],
                            DBVotacionDiputado.voto == record["voto"],
                        )
                    ).first()

                    if not existing:
                        votacion = DBVotacionDiputado(
                            **{
                                k: v
                                for k, v in record.items()
                                if k in DBVotacionDiputado.model_fields and pd.notna(v)
                            }
                        )
                        new_records.append(votacion)

                except Exception as e:
                    logger.warning(f"Error processing vote record {record}: {e}")
                    continue

            if new_records:
                # Process in batches to avoid memory issues
                batch_size = 100000
                total_added = 0

                for i in range(0, len(new_records), batch_size):
                    batch = new_records[i : i + batch_size]
                    session.add_all(batch)
                    session.commit()
                    total_added += len(batch)
                    logger.info(
                        f"Added batch of {len(batch)} votaciones_diputados records"
                    )

                logger.info(
                    f"Added {total_added} new votaciones_diputados records total"
                )
                return total_added
            else:
                logger.info("No new votaciones_diputados records to add")
                return 0

    def populate_all(self) -> Dict[str, int]:
        """Populate all tables from CSV files."""
        logger.info("Starting data population from CSV files")

        results = {}

        # Order matters due to potential foreign key relationships
        results["asuntos"] = self.populate_asuntos_diputados()
        results["bloques"] = self.populate_bloques_diputados()
        results["legisladores"] = self.populate_legisladores_diputados()
        results["votaciones"] = self.populate_votaciones_diputados()

        logger.info(f"Data population completed: {results}")
        return results


def populate_from_csv(csv_dir: Path | str = DEFAULT_CSV_DIR) -> Dict[str, int]:
    """Convenience function to populate database from CSV files."""
    populator = CSVDataPopulator(csv_dir)
    return populator.populate_all()


def main():
    """Main CLI entry point for population script."""
    parser = argparse.ArgumentParser(description="Populate database with CSV data")
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=str(DEFAULT_CSV_DIR),
        help="Path to CSV directory (default: resources/data/DecadaVotadaCSV)",
    )
    parser.add_argument(
        "--table",
        type=str,
        choices=["asuntos", "bloques", "legisladores", "votaciones", "all"],
        default="all",
        help="Which table to populate (default: all)",
    )

    args = parser.parse_args()

    try:
        csv_path = Path(args.csv_dir)

        if not csv_path.exists():
            logger.error(f"CSV directory not found: {csv_path}")
            sys.exit(1)

        populator = CSVDataPopulator(csv_path)

        if args.table == "all":
            results = populator.populate_all()
        elif args.table == "asuntos":
            results = {"asuntos": populator.populate_asuntos_diputados()}
        elif args.table == "bloques":
            results = {"bloques": populator.populate_bloques_diputados()}
        elif args.table == "legisladores":
            results = {"legisladores": populator.populate_legisladores_diputados()}
        elif args.table == "votaciones":
            results = {"votaciones": populator.populate_votaciones_diputados()}

        logger.info(f"Population completed: {results}")
        print(f"Population results: {results}")

    except Exception as e:
        logger.error(f"Failed to populate data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
