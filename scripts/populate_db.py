"""Data population script for loading CSV data into the database."""

import argparse
import sys
from datetime import datetime, time
from pathlib import Path

import pandas as pd
from sqlmodel import Session, select

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
from modulo_consultas_parlamentarias.logger import get_logger

logger = get_logger(__name__)

# Default CSV data directory
DEFAULT_CSV_DIR = Path("resources/data/DecadaVotadaCSV")

DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")
TIME_FORMATS = ("%H:%M:%S",)
TABLE_CHOICES = [
    "asuntos_diputados",
    "asuntos_senadores",
    "bloques_diputados",
    "bloques_senadores",
    "legisladores_diputados",
    "legisladores_senadores",
    "votaciones_diputados",
    "votaciones_senadores",
    "all",
]


class CSVDataPopulator:
    """Handles population of database from CSV files."""

    def __init__(self, csv_dir: Path | str = DEFAULT_CSV_DIR):
        self.csv_dir = Path(csv_dir)
        self.engine = get_engine()

    def _read_csv_safely(
        self, filepath: Path, separator: str = ";"
    ) -> pd.DataFrame:
        """
        Read CSV file safely with error handling.

        Args:
            filepath (Path): Path to the CSV file.
            separator (str): CSV separator character. Defaults to ';'.

        Returns:
            pd.DataFrame: Loaded DataFrame.
        """
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
                logger.error(
                    f"Failed to read {filepath} with latin-1 encoding: {e}"
                )
                raise
        except Exception as e:
            logger.error(f"Failed to read {filepath}: {e}")
            raise

    @staticmethod
    def _normalize_optional_text(value: object) -> str | None:
        """
        Strip string values and return None when empty.

        Args:
            value (object): The input value to normalize.

        Returns:
            str | None: The stripped string or None if empty.
        """
        if value is None:
            return None
        if isinstance(value, float) and pd.isna(value):
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_required_text(
        value: object, *, field: str, dataset: str
    ) -> str:
        """
        Normalize text values ensuring presence.

        Args:
            value (object): The input value to normalize.
            field (str): The name of the field being processed.
            dataset (str): The name of the dataset for error context.

        Returns:
            str: The stripped string.
        """
        text = CSVDataPopulator._normalize_optional_text(value)
        if text is None:
            raise ValueError(f"Missing required field '{field}' in {dataset}")
        return text

    @staticmethod
    def _parse_int(value: object, *, field: str, dataset: str) -> int:
        """
        Parse integers from diverse CSV representations.

        Args:
            value (object): The input value to parse.
            field (str): The name of the field being processed.
            dataset (str): The name of the dataset for error context.

        Returns:
            int: The parsed integer value.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            raise ValueError(
                f"Missing required numeric field '{field}' in {dataset}"
            )

        if isinstance(value, (int,)):
            return int(value)

        if isinstance(value, float) and not pd.isna(value):
            return int(value)

        text = str(value).strip().replace(",", ".")
        if not text:
            raise ValueError(
                f"Missing required numeric field '{field}' in {dataset}"
            )

        try:
            return int(float(text))
        except ValueError as exc:  # noqa: BLE001
            raise ValueError(
                f"Invalid integer value for '{field}' in {dataset}: {value!r}"
            ) from exc

    @staticmethod
    def _parse_optional_float(value: object) -> float | None:
        """
        Parse optional float values from CSV data.

        Args:
            value (object): The input value to parse.

        Returns:
            float | None: The parsed float value or None if not present.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        text = str(value).strip().replace(",", ".")
        if not text:
            return None

        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _parse_date(value: object, *, dataset: str) -> datetime:
        """
        Parse date strings into datetime objects.

        Args:
            value (object): The input value to parse.
            dataset (str): The name of the dataset for error context.

        Returns:
            datetime: The parsed datetime object.
        """
        if isinstance(value, datetime):
            return value

        text = CSVDataPopulator._normalize_optional_text(value)
        if text is None:
            raise ValueError(f"Missing required field 'fecha' in {dataset}")

        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        raise ValueError(
            f"Unsupported date format '{text}' for 'fecha' in {dataset}"
        )

    @staticmethod
    def _parse_time(value: object) -> time | None:
        """
        Parse optional time strings into time objects.

        Args:
            value (object): The input value to parse.

        Returns:
            time | None: The parsed time object or None if not present.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None

        if isinstance(value, time):
            return value

        text = str(value).strip()
        if not text:
            return None

        for fmt in TIME_FORMATS:
            try:
                return datetime.strptime(text, fmt).time()
            except ValueError:
                continue

        logger.warning(
            "Unable to parse time value %r; defaulting to None", value
        )
        return None

    @staticmethod
    def _build_asunto_payload(record: dict, dataset: str) -> dict:
        """
        Normalize a CSV record into model-friendly payload.

        Args:
            record (dict): The CSV record as a dictionary.
            dataset (str): The name of the dataset for error context.

        Returns:
            dict: The normalized payload dictionary.
        """
        payload: dict[str, object] = {}

        payload["asunto_id"] = CSVDataPopulator._parse_int(
            record.get("asunto_id"), field="asunto_id", dataset=dataset
        )
        payload["sesion"] = CSVDataPopulator._normalize_required_text(
            record.get("sesion"), field="sesion", dataset=dataset
        )
        payload["asunto"] = CSVDataPopulator._normalize_required_text(
            record.get("asunto"), field="asunto", dataset=dataset
        )
        payload["titulo"] = CSVDataPopulator._normalize_optional_text(
            record.get("titulo")
        )
        payload["fecha"] = CSVDataPopulator._parse_date(
            record.get("fecha"), dataset=dataset
        )

        year_value = record.get("año", record.get("ano"))
        payload["año"] = CSVDataPopulator._parse_int(
            year_value, field="ano", dataset=dataset
        )

        payload["hora"] = CSVDataPopulator._parse_time(record.get("hora"))
        payload["base"] = CSVDataPopulator._normalize_optional_text(
            record.get("base")
        )
        payload["mayoria"] = CSVDataPopulator._normalize_optional_text(
            record.get("mayoria")
        )
        payload["resultado"] = CSVDataPopulator._normalize_optional_text(
            record.get("resultado")
        )
        payload["presidente"] = CSVDataPopulator._normalize_required_text(
            record.get("presidente"), field="presidente", dataset=dataset
        )

        for numeric_field in (
            "presentes",
            "ausentes",
            "abstenciones",
            "afirmativos",
            "negativos",
        ):
            payload[numeric_field] = CSVDataPopulator._parse_int(
                record.get(numeric_field),
                field=numeric_field,
                dataset=dataset,
            )

        voto_presidente = CSVDataPopulator._parse_optional_float(
            record.get("votopresidente")
        )
        if voto_presidente is not None:
            payload["votopresidente"] = voto_presidente

        auditoria = CSVDataPopulator._normalize_optional_text(
            record.get("auditoria")
        )
        if auditoria is not None:
            payload["auditoria"] = auditoria

        return payload

    def populate_asuntos_diputados(self) -> int:
        """
        Populate asuntos_diputados table from CSV.

        Returns:
            int: Number of new records added.
        """
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
            "ano": "año",
            "votopresidente": "voto_presidente",
        }

        # Rename columns according to mapping
        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            # Check existing records to avoid duplicates
            existing_ids = set(
                session.exec(select(DBAsuntoDiputados.asunto_id)).all()
            )

            new_records = []
            for record in records:
                try:
                    payload = self._build_asunto_payload(
                        record, dataset="asuntos_diputados"
                    )
                except ValueError as exc:
                    logger.warning(
                        "Skipping diputado asunto due to data issue: %s", exc
                    )
                    continue

                asunto_id = payload["asunto_id"]
                if asunto_id in existing_ids:
                    continue

                try:
                    asunto = DBAsuntoDiputados(
                        **{
                            key: value
                            for key, value in payload.items()
                            if key in DBAsuntoDiputados.model_fields
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Skipping diputado asunto %s due to validation error: %s",
                        asunto_id,
                        exc,
                    )
                    continue

                new_records.append(asunto)
                existing_ids.add(asunto_id)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new asuntos_diputados records"
                )
            else:
                logger.info("No new asuntos_diputados records to add")

        return len(new_records)

    def populate_asuntos_senadores(self) -> int:
        """
        Populate asuntos_senadores table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "asuntos-senadores.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file, separator="\t")
        df = df.dropna(axis=1, how="all")

        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "asuntoid": "asunto_id",
            "ano": "año",
            "votopresidente": "voto_presidente",
        }

        # Rename columns according to mapping
        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBAsuntoSenadores.asunto_id)).all()
            )

            new_records = []
            for record in records:
                try:
                    payload = self._build_asunto_payload(
                        record, dataset="asuntos_senadores"
                    )
                except ValueError as exc:
                    logger.warning(
                        "Skipping senador asunto due to data issue: %s", exc
                    )
                    continue

                asunto_id = payload["asunto_id"]
                if asunto_id in existing_ids:
                    continue

                try:
                    asunto = DBAsuntoSenadores(
                        **{
                            key: value
                            for key, value in payload.items()
                            if key in DBAsuntoSenadores.model_fields
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Skipping senador asunto %s due to validation error: %s",
                        asunto_id,
                        exc,
                    )
                    continue

                new_records.append(asunto)
                existing_ids.add(asunto_id)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new asuntos_senadores records"
                )
            else:
                logger.info("No new asuntos_senadores records to add")

        return len(new_records)

    def populate_bloques_diputados(self) -> int:
        """
        Populate bloques_diputados table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "bloques-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {"bloqueid": "bloque_id"}

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBBloqueDiputados.bloque_id)).all()
            )

            new_records = []
            for record in records:
                if record["bloque_id"] not in existing_ids:
                    bloque = DBBloqueDiputados(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBBloqueDiputados.model_fields
                            and pd.notna(v)
                        }
                    )
                    new_records.append(bloque)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new bloques_diputados records"
                )
            else:
                logger.info("No new bloques_diputados records to add")

        return len(new_records)

    def populate_bloques_senadores(self) -> int:
        """
        Populate bloques_senadores table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "bloques-senadores.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {"bloqueid": "bloque_id"}

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBBloqueSenadores.bloque_id)).all()
            )

            new_records = []
            for record in records:
                if record["bloque_id"] not in existing_ids:
                    bloque = DBBloqueSenadores(
                        bloque_id=record["bloque_id"],
                        bloque=record["bloque"],
                    )
                    new_records.append(bloque)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new bloques_senadores records"
                )
            else:
                logger.info("No new bloques_senadores records to add")

        return len(new_records)

    def populate_legisladores_diputados(self) -> int:
        """
        Populate legisladores_diputados table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "diputados-diputados.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file)

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {"diputadoid": "diputado_id"}

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBLegisladorDiputados.diputado_id)).all()
            )

            new_records = []
            for record in records:
                if record["diputado_id"] not in existing_ids:
                    legislador = DBLegisladorDiputados(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBLegisladorDiputados.model_fields
                            and pd.notna(v)
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

    def populate_legisladores_senadores(self) -> int:
        """
        Populate legisladores_senadores table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "senadores-senadores.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file, separator=",")

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {"senadorid": "senador_id"}

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            existing_ids = set(
                session.exec(select(DBLegisladorSenadores.senador_id)).all()
            )

            new_records = []
            for record in records:
                if record["senador_id"] not in existing_ids:
                    legislador = DBLegisladorSenadores(
                        **{
                            k: v
                            for k, v in record.items()
                            if k in DBLegisladorSenadores.model_fields
                            and pd.notna(v)
                        }
                    )
                    new_records.append(legislador)

            if new_records:
                session.add_all(new_records)
                session.commit()
                logger.info(
                    f"Added {len(new_records)} new legisladores_senadores records"
                )
            else:
                logger.info("No new legisladores_senadores records to add")

        return len(new_records)

    def populate_votaciones_diputados(self) -> int:
        """
        Populate votaciones_diputados table from CSV.

        Returns:
            int: Number of new records added.
        """
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
        }

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            # For votaciones, we'll check for duplicates based on combination of fields
            # since there's no unique ID in the CSV

            new_records = []
            for record in records:
                try:
                    # Check if this exact vote already exists
                    existing = session.exec(
                        select(DBVotacionDiputados).where(
                            DBVotacionDiputados.asunto_id
                            == record["asunto_id"],
                            DBVotacionDiputados.diputado_id
                            == record["diputado_id"],
                            DBVotacionDiputados.voto == record["voto"],
                        )
                    ).first()

                    if not existing:
                        votacion = DBVotacionDiputados(
                            **{
                                k: v
                                for k, v in record.items()
                                if k in DBVotacionDiputados.model_fields
                                and pd.notna(v)
                            }
                        )
                        new_records.append(votacion)

                except Exception as e:
                    logger.warning(
                        f"Error processing vote record {record}: {e}"
                    )
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

    def populate_votaciones_senadores(self) -> int:
        """
        Populate votaciones_senadores table from CSV.

        Returns:
            int: Number of new records added.
        """
        csv_file = self.csv_dir / "votaciones-senadores.csv"
        if not csv_file.exists():
            logger.warning(f"CSV file not found: {csv_file}")
            return 0

        df = self._read_csv_safely(csv_file, separator=",")

        # Clean column names
        df.columns = df.columns.str.strip().str.lower()

        # Map CSV columns to model fields
        column_mapping = {
            "asuntoid": "asunto_id",
            "senadorid": "senador_id",
            "bloqueid": "bloque_id",
        }

        df = df.rename(columns=column_mapping)
        records = df.to_dict("records")

        with Session(self.engine) as session:
            # For votaciones, we'll check for duplicates based on combination of fields
            # since there's no unique ID in the CSV

            new_records = []
            for record in records:
                try:
                    # Check if this exact vote already exists
                    existing = session.exec(
                        select(DBVotacionSenadores).where(
                            DBVotacionSenadores.asunto_id
                            == record["asunto_id"],
                            DBVotacionSenadores.senador_id
                            == record["senador_id"],
                            DBVotacionSenadores.voto == record["voto"],
                        )
                    ).first()

                    if not existing:
                        # Rename keys to match model field names
                        record_copy = record.copy()
                        if "asunto_id" in record_copy:
                            record_copy["asunto_id"] = record_copy.pop(
                                "asunto_id"
                            )
                        if "senador_id" in record_copy:
                            record_copy["senador_id"] = record_copy.pop(
                                "senador_id"
                            )
                        if "bloque_id" in record_copy:
                            record_copy["bloque_id"] = record_copy.pop(
                                "bloque_id"
                            )

                        votacion = DBVotacionSenadores(
                            **{
                                k: v
                                for k, v in record_copy.items()
                                if k in DBVotacionSenadores.model_fields
                                and pd.notna(v)
                            }
                        )
                        new_records.append(votacion)

                except Exception as e:
                    logger.warning(
                        f"Error processing vote record {record}: {e}"
                    )
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
                        f"Added batch of {len(batch)} votaciones_senadores records"
                    )

                logger.info(
                    f"Added {total_added} new votaciones_senadores records total"
                )
                return total_added
            else:
                logger.info("No new votaciones_senadores records to add")
                return 0

    def populate_all(self) -> dict[str, int]:
        """
        Populate all tables from CSV files.

        Returns:
            dict[str, int]: Summary of records added per table.
        """
        logger.info("Starting data population from CSV files")

        results = {}

        # Order matters due to potential foreign key relationships
        results["asuntos_diputados"] = self.populate_asuntos_diputados()
        results["asuntos_senadores"] = self.populate_asuntos_senadores()
        results["bloques_diputados"] = self.populate_bloques_diputados()
        results["bloques_senadores"] = self.populate_bloques_senadores()
        results["legisladores_diputados"] = (
            self.populate_legisladores_diputados()
        )
        results["legisladores_senadores"] = (
            self.populate_legisladores_senadores()
        )
        results["votaciones_diputados"] = self.populate_votaciones_diputados()
        results["votaciones_senadores"] = self.populate_votaciones_senadores()

        logger.info(f"Data population completed: {results}")
        return results


def populate_from_csv(
    csv_dir: Path | str = DEFAULT_CSV_DIR, table: str | None = None
) -> dict[str, int]:
    """
    Populate database tables from CSV files.

    Args:
        csv_dir (Path | str): Directory containing the CSV exports.
        table (str | None): Optional selector matching the CLI ``--table`` choices.

    Returns:
        dict[str, int]: Summary of records added per table.
    """
    populator = CSVDataPopulator(csv_dir)
    target = (table or "all").lower()

    if target == "all":
        return populator.populate_all()
    if target == "asuntos":
        return {
            "asuntos_diputados": populator.populate_asuntos_diputados(),
            "asuntos_senadores": populator.populate_asuntos_senadores(),
        }
    if target == "asuntos_diputados":
        return {"asuntos_diputados": populator.populate_asuntos_diputados()}
    if target == "asuntos_senadores":
        return {"asuntos_senadores": populator.populate_asuntos_senadores()}
    if target == "bloques":
        return {
            "bloques_diputados": populator.populate_bloques_diputados(),
            "bloques_senadores": populator.populate_bloques_senadores(),
        }
    if target == "legisladores":
        return {
            "legisladores_diputados": populator.populate_legisladores_diputados(),
            "legisladores_senadores": populator.populate_legisladores_senadores(),
        }
    if target == "votaciones":
        return {
            "votaciones_diputados": populator.populate_votaciones_diputados(),
            "votaciones_senadores": populator.populate_votaciones_senadores(),
        }

    raise ValueError(f"Unsupported table selection: {table}")


def main():
    """Main CLI entry point for population script."""
    parser = argparse.ArgumentParser(
        description="Populate database with CSV data"
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        default=str(DEFAULT_CSV_DIR),
        help="Path to CSV directory (default: resources/data/DecadaVotadaCSV)",
    )
    parser.add_argument(
        "--table",
        type=str,
        choices=TABLE_CHOICES,
        default="all",
        help="Which table to populate (default: all)",
    )

    args = parser.parse_args()

    try:
        csv_path = Path(args.csv_dir)

        if not csv_path.exists():
            logger.error(f"CSV directory not found: {csv_path}")
            sys.exit(1)

        results = populate_from_csv(csv_path, args.table)

        logger.info(f"Population completed: {results}")
        print(f"Population results: {results}")

    except Exception as e:
        logger.error(f"Failed to populate data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
