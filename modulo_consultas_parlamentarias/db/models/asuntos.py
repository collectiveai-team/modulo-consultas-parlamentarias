"""SQLModel for Asuntos Diputados (Parliamentary Issues)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Column, DateTime, Field, SQLModel, func, text


class DBAsuntoDiputado(SQLModel, table=True):
    """Database model for parliamentary issues (asuntos) from deputies."""

    __tablename__ = "asuntos_diputados"

    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    created_at: datetime = Field(
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    updated_at: datetime | None = Field(
        sa_column=Column(DateTime(), onupdate=func.now())
    )

    # Original CSV fields
    asunto_id: int = Field(..., nullable=False, index=True, unique=True)
    asunto: str = Field(..., nullable=False)
    titulo: str | None = Field(None, nullable=True)
    sumario: str | None = Field(None, nullable=True)
    fecha: str | None = Field(None, nullable=True)  # Original format from CSV
    sesion: str | None = Field(None, nullable=True)
    reunion: str | None = Field(None, nullable=True)
    numero_reunion: str | None = Field(None, nullable=True)

    # Additional metadata
    tipo_asunto: str | None = Field(None, nullable=True)
    estado: str | None = Field(None, nullable=True)

    @field_validator("asunto", "titulo", "sumario", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """Validate and clean text fields."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return str(value).strip() if value else None


class DBAsuntoDiputadoPublic(BaseModel):
    """Public model for parliamentary issues (asuntos) from deputies."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    asunto_id: int
    asunto: str
    titulo: str | None = None
    sumario: str | None = None
    fecha: str | None = None
    sesion: str | None = None
    reunion: str | None = None
    numero_reunion: str | None = None
    tipo_asunto: str | None = None
    estado: str | None = None
