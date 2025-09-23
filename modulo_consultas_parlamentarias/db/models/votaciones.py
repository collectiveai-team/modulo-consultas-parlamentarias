"""SQLModel for Votaciones Diputados (Parliamentary Votes)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Column, DateTime, Field, SQLModel, func, text


class DBVotacionDiputado(SQLModel, table=True):
    """Database model for parliamentary votes (votaciones) from deputies."""
    
    __tablename__ = "votaciones_diputados"

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

    # Original CSV fields - Foreign keys
    asunto_id: int = Field(..., nullable=False, index=True)
    diputado_id: int = Field(..., nullable=False, index=True)
    bloque_id: int | None = Field(None, nullable=True, index=True)
    
    # Vote information
    voto: str = Field(..., nullable=False, index=True)  # AFIRMATIVO, NEGATIVO, ABSTENCION, AUSENTE
    
    # Session information
    fecha_votacion: str | None = Field(None, nullable=True)
    sesion: str | None = Field(None, nullable=True)
    reunion: str | None = Field(None, nullable=True)
    
    # Additional metadata
    observaciones: str | None = Field(None, nullable=True)
    tipo_votacion: str | None = Field(None, nullable=True)  # NOMINAL, SECRETA, etc.
    
    @field_validator("voto", mode="before")
    def validate_voto(cls, value: Any) -> str:
        """Validate and normalize vote values."""
        if value is None:
            raise ValueError("Vote cannot be None")
        
        vote_str = str(value).strip().upper()
        valid_votes = {"AFIRMATIVO", "NEGATIVO", "ABSTENCION", "AUSENTE"}
        
        if vote_str not in valid_votes:
            # Try to map common variations
            vote_mapping = {
                "SI": "AFIRMATIVO",
                "SÍ": "AFIRMATIVO", 
                "YES": "AFIRMATIVO",
                "NO": "NEGATIVO",
                "ABS": "ABSTENCION",
                "ABSTENCIÓN": "ABSTENCION",
                "AUS": "AUSENTE",
            }
            vote_str = vote_mapping.get(vote_str, vote_str)
            
            if vote_str not in valid_votes:
                raise ValueError(f"Invalid vote value: {value}. Must be one of {valid_votes}")
        
        return vote_str

    @field_validator("observaciones", "tipo_votacion", mode="before")
    def validate_text_fields(cls, value: Any) -> str | None:
        """Validate and clean text fields."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return str(value).strip() if value else None


class DBVotacionDiputadoPublic(BaseModel):
    """Public model for parliamentary votes (votaciones) from deputies."""
    
    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    asunto_id: int
    diputado_id: int
    bloque_id: int | None = None
    voto: str
    fecha_votacion: str | None = None
    sesion: str | None = None
    reunion: str | None = None
    observaciones: str | None = None
    tipo_votacion: str | None = None
