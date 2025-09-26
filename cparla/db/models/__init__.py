"""Database models for parliamentary data."""

from .asuntos import (
    DBAsuntoBase,
    DBAsuntoDiputados,
    DBAsuntoDiputadosPublic,
    DBAsuntoSenadores,
    DBAsuntoSenadoresPublic,
)
from .bloques import (
    DBBloqueBase,
    DBBloqueDiputados,
    DBBloqueDiputadosPublic,
    DBBloqueSenadores,
    DBBloqueSenadoresPublic,
)
from .legisladores import (
    DBLegisladorBase,
    DBLegisladorDiputados,
    DBLegisladorDiputadosPublic,
    DBLegisladorSenadores,
    DBLegisladorSenadoresPublic,
)
from .votaciones import (
    DBVotacionBase,
    DBVotacionDiputados,
    DBVotacionDiputadosPublic,
    DBVotacionSenadores,
    DBVotacionSenadoresPublic,
)

__all__ = [
    # Base classes
    "DBAsuntoBase",
    "DBBloqueBase",
    "DBLegisladorBase",
    "DBVotacionBase",
    # Diputados models
    "DBAsuntoDiputados",
    "DBBloqueDiputados",
    "DBLegisladorDiputados",
    "DBVotacionDiputados",
    # Senadores models
    "DBAsuntoSenadores",
    "DBBloqueSenadores",
    "DBLegisladorSenadores",
    "DBVotacionSenadores",
    # Public models - Diputados
    "DBAsuntoDiputadosPublic",
    "DBBloqueDiputadosPublic",
    "DBLegisladorDiputadosPublic",
    "DBVotacionDiputadosPublic",
    # Public models - Senadores
    "DBAsuntoSenadoresPublic",
    "DBBloqueSenadoresPublic",
    "DBLegisladorSenadoresPublic",
    "DBVotacionSenadoresPublic",
]
