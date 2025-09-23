"""Database models for parliamentary data."""

from .asuntos import DBAsuntoDiputado
from .bloques import DBBloqueDiputado
from .legisladores import DBLegisladorDiputado
from .votaciones import DBVotacionDiputado

__all__ = [
    "DBAsuntoDiputado",
    "DBBloqueDiputado",
    "DBLegisladorDiputado",
    "DBVotacionDiputado",
]
