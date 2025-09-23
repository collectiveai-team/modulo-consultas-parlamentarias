"""SQLModel for Bloques Diputados (Parliamentary Blocks)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Column, DateTime, Field, SQLModel, func, text


class DBBloqueDiputado(SQLModel, table=True):
    """Database model for parliamentary blocks (bloques) from deputies."""
    
    __tablename__ = "bloques_diputados"

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
    bloque_id: int = Field(..., nullable=False, index=True, unique=True)
    bloque: str = Field(..., nullable=False, index=True)
    
    # Additional metadata
    descripcion: str | None = Field(None, nullable=True)
    activo: bool = Field(default=True, nullable=False)
    fecha_inicio: str | None = Field(None, nullable=True)
    fecha_fin: str | None = Field(None, nullable=True)
    
    @field_validator("bloque", "descripcion", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """Validate and clean text fields."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return str(value).strip() if value else None


class DBBloqueDiputadoPublic(BaseModel):
    """Public model for parliamentary blocks (bloques) from deputies."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    bloque_id: int
    bloque: str
    descripcion: str | None = None
    activo: bool = True
    fecha_inicio: str | None = None
    fecha_fin: str | None = None
