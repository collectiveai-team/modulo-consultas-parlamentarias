"""SQLModel definitions for parliamentary legislators (legisladores)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Field, SQLModel, func, text


class DBLegisladorBase(SQLModel):
    """Base model shared by all legislators tables."""

    # Index and primary key
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    # Legislator information
    nombre: str = Field(..., nullable=False, index=True)
    distrito: str = Field(..., nullable=False, index=True)
    sexo: str | None = Field(None, nullable=True)
    imagen: str | None = Field(None, nullable=True)

    # Timestamps
    created_at: datetime = Field(
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now()},
    )

    @field_validator("nombre", "sexo", "distrito", "imagen", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """
        Validate and clean text fields.

        Args:
            value (Any): The input value to validate.

        Returns:
            str | None: The cleaned string or None if input is empty.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return str(value).strip()


class DBLegisladorDiputados(DBLegisladorBase, table=True):
    """Database model for deputies (diputados)."""

    __tablename__ = "legisladores_diputados"

    # Field specific to diputados
    diputado_id: int = Field(
        ...,
        alias="diputadoId",
        nullable=False,
        index=True,
        unique=True,
    )


class DBLegisladorSenadores(DBLegisladorBase, table=True):
    """Database model for senators (senadores)."""

    __tablename__ = "legisladores_senadores"

    # Field specific to senadores
    senador_id: int = Field(
        ...,
        alias="senadorId",
        nullable=False,
        index=True,
        unique=True,
    )


class DBLegisladorPublicBase(BaseModel):
    """Base public model shared between deputies and senators."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    nombre: str
    distrito: str
    sexo: str | None = None
    imagen: str | None = None


class DBLegisladorDiputadosPublic(DBLegisladorPublicBase):
    """Public model for deputies (diputados)."""

    diputado_id: int


class DBLegisladorSenadoresPublic(DBLegisladorPublicBase):
    """Public model for senators (senadores)."""

    senador_id: int
