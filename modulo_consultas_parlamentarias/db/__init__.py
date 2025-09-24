"""Database models and utilities for parliamentary data management."""

from .engine import create_db_and_tables, get_engine, get_session
from .models import *
from .models.asuntos import (
    DBAsuntoBase,
    DBAsuntoDiputados,
    DBAsuntoDiputadosPublic,
    DBAsuntoSenadores,
    DBAsuntoSenadoresPublic,
)
from .models.bloques import (
    DBBloqueBase,
    DBBloqueDiputados,
    DBBloqueDiputadosPublic,
    DBBloqueSenadores,
    DBBloqueSenadoresPublic,
)
from .models.legisladores import (
    DBLegisladorBase,
    DBLegisladorDiputados,
    DBLegisladorDiputadosPublic,
    DBLegisladorSenadores,
    DBLegisladorSenadoresPublic,
)
from .models.votaciones import (
    DBVotacionBase,
    DBVotacionDiputados,
    DBVotacionDiputadosPublic,
    DBVotacionSenadores,
    DBVotacionSenadoresPublic,
)
from .services import (
    AsuntosService,
    BloquesService,
    LegisladoresService,
    VotacionesService,
    asuntos_service,
    bloques_service,
    legisladores_service,
    votaciones_service,
)

# Population functionality moved to scripts package

__all__ = [
    # Models - Base classes
    "DBAsuntoBase",
    "DBBloqueBase",
    "DBLegisladorBase",
    "DBVotacionBase",
    # Models - Diputados
    "DBAsuntoDiputados",
    "DBAsuntoDiputadosPublic",
    "DBBloqueDiputados",
    "DBBloqueDiputadosPublic",
    "DBLegisladorDiputados",
    "DBLegisladorDiputadosPublic",
    "DBVotacionDiputados",
    "DBVotacionDiputadosPublic",
    # Models - Senadores
    "DBAsuntoSenadores",
    "DBAsuntoSenadoresPublic",
    "DBBloqueSenadores",
    "DBBloqueSenadoresPublic",
    "DBLegisladorSenadores",
    "DBLegisladorSenadoresPublic",
    "DBVotacionSenadores",
    "DBVotacionSenadoresPublic",
    # Engine
    "get_engine",
    "get_session",
    "create_db_and_tables",
    # Services
    "asuntos_service",
    "bloques_service",
    "legisladores_service",
    "votaciones_service",
    "AsuntosService",
    "BloquesService",
    "LegisladoresService",
    "VotacionesService",
]
