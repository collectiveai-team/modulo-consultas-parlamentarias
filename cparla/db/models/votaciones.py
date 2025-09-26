"""SQLModel definitions for parliamentary votes (votaciones)."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Field, SQLModel, func, text


class VotoEnum(str, Enum):
    """Enum for vote values."""

    AFIRMATIVO = "AFIRMATIVO"
    NEGATIVO = "NEGATIVO"
    ABSTENCION = "ABSTENCION"
    AUSENTE = "AUSENTE"
    PRESIDENTE = "PRESIDENTE"


# Mapping from integer values to vote strings
VOTO_MAPPING = {
    0: VotoEnum.AFIRMATIVO,
    1: VotoEnum.NEGATIVO,
    2: VotoEnum.ABSTENCION,
    3: VotoEnum.AUSENTE,
    4: VotoEnum.PRESIDENTE,
    # String variants for flexibility
    "0": VotoEnum.AFIRMATIVO,
    "1": VotoEnum.NEGATIVO,
    "2": VotoEnum.ABSTENCION,
    "3": VotoEnum.AUSENTE,
    "4": VotoEnum.PRESIDENTE,
    # Direct strings
    "AFIRMATIVO": VotoEnum.AFIRMATIVO,
    "NEGATIVO": VotoEnum.NEGATIVO,
    "ABSTENCION": VotoEnum.ABSTENCION,
    "ABSTENCIÓN": VotoEnum.ABSTENCION,
    "AUSENTE": VotoEnum.AUSENTE,
    "PRESIDENTE": VotoEnum.PRESIDENTE,
}


class DBVotacionBase(SQLModel):
    """Base model shared by parliamentary votes tables."""

    # Index and primary key
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    # Original CSV fields - Foreign keys
    asunto_id: int = Field(
        ...,
        alias="asuntoId",
        index=True,
    )

    # Common fields shared between diputados and senadores
    bloque_id: int = Field(
        ...,
        alias="bloqueId",
        index=True,
    )

    # Vote information
    voto: str = Field(..., nullable=False)

    # Timestamps
    created_at: datetime = Field(
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now()},
    )

    @field_validator("voto", mode="before")
    def validate_voto(cls, value: Any) -> str:
        """
        Validate and normalize vote values.

        Maps integers (0-4) and various string representations
        to standardized vote values.

        Args:
            value (Any): The input vote value to validate.

        Returns:
            str: The standardized vote value.

        Raises:
            ValueError: If the vote value is None or cannot be mapped.
        """
        if value is None:
            raise ValueError("Vote cannot be None")

        # Convert to uppercase string for lookup
        if isinstance(value, (int, float)):
            # Handle numeric values directly
            vote_value = VOTO_MAPPING.get(int(value))
            if vote_value is not None:
                return vote_value
        else:
            # Handle string values
            vote_str = str(value).strip().upper()
            vote_value = VOTO_MAPPING.get(vote_str)
            if vote_value is not None:
                return vote_value

        # If we get here, the value couldn't be mapped
        valid_votes = set(VotoEnum)
        raise ValueError(
            f"Invalid vote value: {value}. Must be mappable to one of {valid_votes}"
        )


class DBVotacionDiputados(DBVotacionBase, table=True):
    """Database model for parliamentary votes (votaciones) from deputies."""

    __tablename__ = "votaciones_diputados"

    # Fields specific to diputados
    diputado_id: int = Field(
        ...,
        alias="diputadoId",
        nullable=False,
        index=True,
    )


class DBVotacionSenadores(DBVotacionBase, table=True):
    """Database model for parliamentary votes (votaciones) from senators."""

    __tablename__ = "votaciones_senadores"

    # Fields specific to senadores
    senador_id: int = Field(
        ...,
        alias="senadorId",
        nullable=False,
        index=True,
    )


class DBVotacionPublicBase(BaseModel):
    """Base public model shared between deputies and senators votes."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    asunto_id: int
    bloque_id: int
    voto: str


class DBVotacionDiputadosPublic(DBVotacionPublicBase):
    """Public model for parliamentary votes (votaciones) from deputies."""

    diputado_id: int


class DBVotacionSenadoresPublic(DBVotacionPublicBase):
    """Public model for parliamentary votes (votaciones) from senators."""

    senador_id: int
