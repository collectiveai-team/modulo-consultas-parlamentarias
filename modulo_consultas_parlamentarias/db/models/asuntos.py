"""SQLModel definitions for parliamentary issues (asuntos)."""

import uuid
from datetime import datetime, time
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlmodel import Field, SQLModel, func, text

DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


class DBAsuntoBase(SQLModel):
    """Base model shared by parliamentary issues tables."""

    # Index and primary key
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    asunto_id: int = Field(
        ...,
        alias="asuntoId",
        unique=True,
        nullable=False,
        index=True,
    )

    # Session details
    sesion: str = Field(..., nullable=False)
    asunto: str = Field(..., nullable=False)
    titulo: str | None = Field(None, nullable=True)

    # Date and time fields
    fecha: datetime = Field(..., nullable=False)
    año: int = Field(
        ...,
        nullable=False,
        alias="ano",
    )
    hora: time | None = Field(None, nullable=True)

    # Voting details
    base: str | None = Field(None, nullable=True)
    mayoria: str | None = Field(None, nullable=True)
    resultado: str | None = Field(None, nullable=True)
    presidente: str = Field(..., nullable=False)
    presentes: int = Field(..., nullable=False)
    ausentes: int = Field(..., nullable=False)
    abstenciones: int = Field(..., nullable=False)
    afirmativos: int = Field(..., nullable=False)
    negativos: int = Field(..., nullable=False)
    voto_presidente: float | None = Field(
        None,
        alias="votopresidente",
        nullable=True,
    )
    auditoria: str | None = Field(None, nullable=True)

    # Timestamps
    created_at: datetime = Field(
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now()},
    )

    @staticmethod
    def _clean_text(value: Any) -> str | None:
        """
        Normalize text values, stripping blanks and empty strings.

        Args:
            value (Any): The input value to normalize.

        Returns:
            str | None: The cleaned string or None if input is empty.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip()

    @field_validator("asunto", "titulo", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """
        Apply common text normalization to text fields.

        Args:
            value (Any): The input value to validate.

        Returns:
            str | None: The cleaned string or None if input is empty.
        """
        return cls._clean_text(value)

    @field_validator("fecha", mode="before")
    def parse_fecha(cls, value: Any) -> datetime:
        """
        Parse and validate the 'fecha' field.

        Args:
            value (Any): The input value to parse.

        Returns:
            datetime: The parsed datetime object.
        """
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("'fecha' cannot be empty or blank")

            for fmt in DATE_FORMATS:
                try:
                    return datetime.strptime(stripped, fmt)
                except ValueError:
                    continue

        raise ValueError(f"Invalid date format: {value!r}")

    @field_validator("hora", mode="before")
    def validate_hora(cls, value: Any) -> time | None:
        """
        Validates and normalizes the 'hora' field.

        Args:
            value (Any): The input value to validate and normalize.

        Returns:
            time | None: The normalized time object or None if input is invalid or empty.
        """
        if value is None or isinstance(value, time):
            return value

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                # Parse as time and convert to datetime for consistency
                t = datetime.strptime(value, "%H:%M:%S").time()
                return t
            except ValueError:
                return None

        return None

    @model_validator(mode="after")
    def sync_year_with_fecha(self) -> "DBAsuntoBase":
        """
        Ensure the 'año' field matches the year extracted from 'fecha'.

        Returns:
            DBAsuntoBase: The validated instance with synchronized year.
        """
        if self.fecha and self.año != self.fecha.year:
            self.año = self.fecha.year
        return self


class DBAsuntoDiputados(DBAsuntoBase, table=True):
    """Database model for parliamentary issues (asuntos) from deputies."""

    __tablename__ = "asuntos_diputados"


class DBAsuntoSenadores(DBAsuntoBase, table=True):
    """Database model for parliamentary issues (asuntos) from senators."""

    __tablename__ = "asuntos_senadores"


class DBAsuntoPublicBase(BaseModel):
    """Base public model shared between deputies and senators asuntos."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    sesion: str
    asunto: str
    titulo: str | None = None

    fecha: datetime

    base: str | None = None
    mayoria: str | None = None
    resultado: str | None = None
    presidente: str
    presentes: int
    ausentes: int
    abstenciones: int
    afirmativos: int
    negativos: int
    votopresidente: float | None = None


class DBAsuntoDiputadosPublic(DBAsuntoPublicBase):
    """Public model for parliamentary issues (asuntos) from deputies."""

    pass


class DBAsuntoSenadoresPublic(DBAsuntoPublicBase):
    """Public model for parliamentary issues (asuntos) from senators."""

    pass
