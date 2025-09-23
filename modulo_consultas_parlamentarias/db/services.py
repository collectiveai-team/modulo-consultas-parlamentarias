"""Database service layer for common operations."""

from typing import List, Optional
from uuid import UUID

from sqlmodel import Session, select

from modulo_consultas_parlamentarias.db.engine import get_engine
from modulo_consultas_parlamentarias.db.models.asuntos import DBAsuntoDiputado, DBAsuntoDiputadoPublic
from modulo_consultas_parlamentarias.db.models.bloques import DBBloqueDiputado, DBBloqueDiputadoPublic
from modulo_consultas_parlamentarias.db.models.legisladores import DBLegisladorDiputado, DBLegisladorDiputadoPublic
from modulo_consultas_parlamentarias.db.models.votaciones import DBVotacionDiputado, DBVotacionDiputadoPublic


class AsuntosService:
    """Service for managing parliamentary issues (asuntos)."""
    
    def __init__(self):
        self.engine = get_engine()
    
    def get_by_id(self, asunto_id: UUID) -> Optional[DBAsuntoDiputadoPublic]:
        """Get asunto by UUID."""
        with Session(self.engine) as session:
            asunto = session.get(DBAsuntoDiputado, asunto_id)
            return DBAsuntoDiputadoPublic.model_validate(asunto) if asunto else None
    
    def get_by_asunto_id(self, asunto_id: int) -> Optional[DBAsuntoDiputadoPublic]:
        """Get asunto by original asunto_id."""
        with Session(self.engine) as session:
            asunto = session.exec(
                select(DBAsuntoDiputado).where(DBAsuntoDiputado.asunto_id == asunto_id)
            ).first()
            return DBAsuntoDiputadoPublic.model_validate(asunto) if asunto else None
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[DBAsuntoDiputadoPublic]:
        """List all asuntos with pagination."""
        with Session(self.engine) as session:
            asuntos = session.exec(
                select(DBAsuntoDiputado).offset(offset).limit(limit)
            ).all()
            return [DBAsuntoDiputadoPublic.model_validate(a) for a in asuntos]
    
    def search_by_title(self, title_query: str, limit: int = 50) -> List[DBAsuntoDiputadoPublic]:
        """Search asuntos by title."""
        with Session(self.engine) as session:
            asuntos = session.exec(
                select(DBAsuntoDiputado).where(
                    DBAsuntoDiputado.titulo.contains(title_query)
                ).limit(limit)
            ).all()
            return [DBAsuntoDiputadoPublic.model_validate(a) for a in asuntos]


class BloquesService:
    """Service for managing parliamentary blocks (bloques)."""
    
    def __init__(self):
        self.engine = get_engine()
    
    def get_by_id(self, bloque_id: UUID) -> Optional[DBBloqueDiputadoPublic]:
        """Get bloque by UUID."""
        with Session(self.engine) as session:
            bloque = session.get(DBBloqueDiputado, bloque_id)
            return DBBloqueDiputadoPublic.model_validate(bloque) if bloque else None
    
    def get_by_bloque_id(self, bloque_id: int) -> Optional[DBBloqueDiputadoPublic]:
        """Get bloque by original bloque_id."""
        with Session(self.engine) as session:
            bloque = session.exec(
                select(DBBloqueDiputado).where(DBBloqueDiputado.bloque_id == bloque_id)
            ).first()
            return DBBloqueDiputadoPublic.model_validate(bloque) if bloque else None
    
    def list_all(self, active_only: bool = True) -> List[DBBloqueDiputadoPublic]:
        """List all bloques."""
        with Session(self.engine) as session:
            query = select(DBBloqueDiputado)
            if active_only:
                query = query.where(DBBloqueDiputado.activo)
            
            bloques = session.exec(query).all()
            return [DBBloqueDiputadoPublic.model_validate(b) for b in bloques]
    
    def search_by_name(self, name_query: str) -> List[DBBloqueDiputadoPublic]:
        """Search bloques by name."""
        with Session(self.engine) as session:
            bloques = session.exec(
                select(DBBloqueDiputado).where(
                    DBBloqueDiputado.bloque.contains(name_query)
                )
            ).all()
            return [DBBloqueDiputadoPublic.model_validate(b) for b in bloques]


class LegisladoresService:
    """Service for managing legislators (diputados)."""
    
    def __init__(self):
        self.engine = get_engine()
    
    def get_by_id(self, legislador_id: UUID) -> Optional[DBLegisladorDiputadoPublic]:
        """Get legislador by UUID."""
        with Session(self.engine) as session:
            legislador = session.get(DBLegisladorDiputado, legislador_id)
            return DBLegisladorDiputadoPublic.model_validate(legislador) if legislador else None
    
    def get_by_diputado_id(self, diputado_id: int) -> Optional[DBLegisladorDiputadoPublic]:
        """Get legislador by original diputado_id."""
        with Session(self.engine) as session:
            legislador = session.exec(
                select(DBLegisladorDiputado).where(DBLegisladorDiputado.diputado_id == diputado_id)
            ).first()
            return DBLegisladorDiputadoPublic.model_validate(legislador) if legislador else None
    
    def list_all(self, active_only: bool = True, limit: int = 100, offset: int = 0) -> List[DBLegisladorDiputadoPublic]:
        """List all legislators with pagination."""
        with Session(self.engine) as session:
            query = select(DBLegisladorDiputado).offset(offset).limit(limit)
            if active_only:
                query = query.where(DBLegisladorDiputado.activo)
            
            legisladores = session.exec(query).all()
            return [DBLegisladorDiputadoPublic.model_validate(legislador) for legislador in legisladores]
    
    def get_by_bloque(self, bloque_id: int) -> List[DBLegisladorDiputadoPublic]:
        """Get legislators by bloque."""
        with Session(self.engine) as session:
            legisladores = session.exec(
                select(DBLegisladorDiputado).where(DBLegisladorDiputado.bloque_id == bloque_id)
            ).all()
            return [DBLegisladorDiputadoPublic.model_validate(legislador) for legislador in legisladores]
    
    def search_by_name(self, name_query: str) -> List[DBLegisladorDiputadoPublic]:
        """Search legislators by name."""
        with Session(self.engine) as session:
            legisladores = session.exec(
                select(DBLegisladorDiputado).where(
                    (DBLegisladorDiputado.nombre.contains(name_query)) |
                    (DBLegisladorDiputado.apellido.contains(name_query)) |
                    (DBLegisladorDiputado.nombre_completo.contains(name_query))
                )
            ).all()
            return [DBLegisladorDiputadoPublic.model_validate(legislador) for legislador in legisladores]


class VotacionesService:
    """Service for managing parliamentary votes (votaciones)."""
    
    def __init__(self):
        self.engine = get_engine()
    
    def get_by_id(self, votacion_id: UUID) -> Optional[DBVotacionDiputadoPublic]:
        """Get votacion by UUID."""
        with Session(self.engine) as session:
            votacion = session.get(DBVotacionDiputado, votacion_id)
            return DBVotacionDiputadoPublic.model_validate(votacion) if votacion else None
    
    def get_by_asunto(self, asunto_id: int, limit: int = 1000) -> List[DBVotacionDiputadoPublic]:
        """Get all votes for a specific asunto."""
        with Session(self.engine) as session:
            votaciones = session.exec(
                select(DBVotacionDiputado).where(
                    DBVotacionDiputado.asunto_id == asunto_id
                ).limit(limit)
            ).all()
            return [DBVotacionDiputadoPublic.model_validate(v) for v in votaciones]
    
    def get_by_diputado(self, diputado_id: int, limit: int = 1000) -> List[DBVotacionDiputadoPublic]:
        """Get all votes by a specific diputado."""
        with Session(self.engine) as session:
            votaciones = session.exec(
                select(DBVotacionDiputado).where(
                    DBVotacionDiputado.diputado_id == diputado_id
                ).limit(limit)
            ).all()
            return [DBVotacionDiputadoPublic.model_validate(v) for v in votaciones]
    
    def get_by_bloque(self, bloque_id: int, limit: int = 1000) -> List[DBVotacionDiputadoPublic]:
        """Get all votes by a specific bloque."""
        with Session(self.engine) as session:
            votaciones = session.exec(
                select(DBVotacionDiputado).where(
                    DBVotacionDiputado.bloque_id == bloque_id
                ).limit(limit)
            ).all()
            return [DBVotacionDiputadoPublic.model_validate(v) for v in votaciones]
    
    def get_vote_summary_by_asunto(self, asunto_id: int) -> dict:
        """Get vote summary for a specific asunto."""
        with Session(self.engine) as session:
            votaciones = session.exec(
                select(DBVotacionDiputado).where(
                    DBVotacionDiputado.asunto_id == asunto_id
                )
            ).all()
            
            summary = {
                "AFIRMATIVO": 0,
                "NEGATIVO": 0,
                "ABSTENCION": 0,
                "AUSENTE": 0,
                "total": len(votaciones)
            }
            
            for votacion in votaciones:
                if votacion.voto in summary:
                    summary[votacion.voto] += 1
            
            return summary


# Service instances for easy import
asuntos_service = AsuntosService()
bloques_service = BloquesService()
legisladores_service = LegisladoresService()
votaciones_service = VotacionesService()
