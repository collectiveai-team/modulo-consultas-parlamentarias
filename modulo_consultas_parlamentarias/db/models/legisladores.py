"""SQLModel for Legisladores Diputados (Deputies/Legislators)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Column, DateTime, Field, SQLModel, func, text


class DBLegisladorDiputado(SQLModel, table=True):
    """Database model for deputies/legislators (diputados)."""
    
    __tablename__ = "legisladores_diputados"

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
    diputado_id: int = Field(..., nullable=False, index=True, unique=True)
    nombre: str = Field(..., nullable=False, index=True)
    apellido: str | None = Field(None, nullable=True, index=True)
    nombre_completo: str | None = Field(None, nullable=True)
    
    # Personal information
    genero: str | None = Field(None, nullable=True)
    fecha_nacimiento: str | None = Field(None, nullable=True)
    lugar_nacimiento: str | None = Field(None, nullable=True)
    
    # Political information
    partido: str | None = Field(None, nullable=True, index=True)
    bloque_id: int | None = Field(None, nullable=True, index=True)
    distrito: str | None = Field(None, nullable=True, index=True)
    
    # Contact and media
    email: str | None = Field(None, nullable=True)
    telefono: str | None = Field(None, nullable=True)
    imagen: str | None = Field(None, nullable=True)
    
    # Legislative period
    periodo_inicio: str | None = Field(None, nullable=True)
    periodo_fin: str | None = Field(None, nullable=True)
    activo: bool = Field(default=True, nullable=False)
    
    @field_validator("nombre", "apellido", "nombre_completo", "partido", "distrito", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """Validate and clean text fields."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return str(value).strip() if value else None


class DBLegisladorDiputadoPublic(BaseModel):
    """Public model for deputies/legislators (diputados)."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    diputado_id: int
    nombre: str
    apellido: str | None = None
    nombre_completo: str | None = None
    genero: str | None = None
    fecha_nacimiento: str | None = None
    lugar_nacimiento: str | None = None
    partido: str | None = None
    bloque_id: int | None = None
    distrito: str | None = None
    email: str | None = None
    telefono: str | None = None
    imagen: str | None = None
    periodo_inicio: str | None = None
    periodo_fin: str | None = None
    activo: bool = True
