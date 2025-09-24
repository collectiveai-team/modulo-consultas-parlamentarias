"""SQLModel definitions for parliamentary blocks (bloques)."""

import uuid
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Field, SQLModel, func, text


class DBBloqueBase(SQLModel):
    """Base model shared by parliamentary blocks tables."""

    # Index and primary key
    id: uuid.UUID | None = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )
    bloque_id: int = Field(
        ...,
        alias="bloqueId",
        unique=True,
        nullable=False,
        index=True,
    )

    # Block details
    bloque: str = Field(..., nullable=False)
    color: str | None = Field(None, nullable=True)

    # Timestamps
    created_at: datetime = Field(
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now()},
    )

    @field_validator("bloque", "color", mode="before")
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
        return str(value).strip() if value else None


class DBBloqueDiputados(DBBloqueBase, table=True):
    """Database model for parliamentary blocks (bloques) from deputies."""

    __tablename__ = "bloques_diputados"


class DBBloqueSenadores(DBBloqueBase, table=True):
    """Database model for parliamentary blocks (bloques) from senators."""

    __tablename__ = "bloques_senadores"


class DBBloquePublicBase(BaseModel):
    """Base public model shared between deputies and senators bloques."""

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None = None

    bloque_id: int
    bloque: str
    color: str | None = None


class DBBloqueDiputadosPublic(DBBloquePublicBase):
    """Public model for parliamentary blocks (bloques) from deputies."""

    pass


class DBBloqueSenadoresPublic(DBBloquePublicBase):
    """Public model for parliamentary blocks (bloques) from senators."""

    pass
