"""Database service layer for common operations."""

from typing import Any, Generic, Literal, Type, TypeVar, cast
from uuid import UUID

from sqlmodel import Session, SQLModel, select

from modulo_consultas_parlamentarias.db.engine import get_engine
from modulo_consultas_parlamentarias.db.models.asuntos import (
    DBAsuntoBase,
    DBAsuntoDiputados,
    DBAsuntoDiputadosPublic,
    DBAsuntoSenadores,
    DBAsuntoSenadoresPublic,
)
from modulo_consultas_parlamentarias.db.models.bloques import (
    DBBloqueBase,
    DBBloqueDiputados,
    DBBloqueDiputadosPublic,
    DBBloqueSenadores,
    DBBloqueSenadoresPublic,
)
from modulo_consultas_parlamentarias.db.models.legisladores import (
    DBLegisladorBase,
    DBLegisladorDiputados,
    DBLegisladorDiputadosPublic,
    DBLegisladorSenadores,
    DBLegisladorSenadoresPublic,
)
from modulo_consultas_parlamentarias.db.models.votaciones import (
    DBVotacionBase,
    DBVotacionDiputados,
    DBVotacionDiputadosPublic,
    DBVotacionSenadores,
    DBVotacionSenadoresPublic,
)

# Type variables for generic services
T = TypeVar("T", bound=SQLModel)
TPublic = TypeVar("TPublic", bound=Any)

# Type for chamber selection
ChamberLiteral = Literal["diputados", "senadores"]


class BaseService(Generic[T, TPublic]):
    """Base service with common database operations."""

    def __init__(
        self, model: Type[T], public_model: Type[TPublic], id_field: str = "id"
    ):
        self.engine = get_engine()
        self.model = model
        self.public_model = public_model
        self.id_field = id_field

    def get_by_id(self, record_id: UUID) -> TPublic | None:
        """Get record by UUID."""
        with Session(self.engine) as session:
            record = session.get(self.model, record_id)
            return self.public_model.model_validate(record) if record else None

    def _get_by_field(self, field_name: str, value: Any) -> TPublic | None:
        """Get record by a specific field value."""
        with Session(self.engine) as session:
            stmt = select(self.model).where(
                getattr(self.model, field_name) == value
            )
            record = session.exec(stmt).first()
            return self.public_model.model_validate(record) if record else None

    def list_all(
        self, limit: int = 100, offset: int = 0, **filters
    ) -> list[TPublic]:
        """list records with pagination and optional filters."""
        with Session(self.engine) as session:
            query = select(self.model)

            # Apply filters
            for field_name, value in filters.items():
                if hasattr(self.model, field_name):
                    query = query.where(
                        getattr(self.model, field_name) == value
                    )

            # Apply pagination
            query = query.offset(offset).limit(limit)

            records = session.exec(query).all()
            return [self.public_model.model_validate(r) for r in records]


class AsuntosServiceBase(BaseService[DBAsuntoBase, Any]):
    """Base service for managing parliamentary issues (asuntos)."""

    def get_by_asunto_id(self, asunto_id: int) -> Any | None:
        """Get asunto by original asunto_id."""
        return self._get_by_field("asunto_id", asunto_id)

    def search_by_title(self, title_query: str, limit: int = 50) -> list[Any]:
        """Search asuntos by title."""
        with Session(self.engine) as session:
            asuntos = session.exec(
                select(self.model)
                .where(self.model.titulo.contains(title_query))
                .limit(limit)
            ).all()
            return [self.public_model.model_validate(a) for a in asuntos]


class AsuntosDiputadosService(AsuntosServiceBase):
    """Service for managing parliamentary issues (asuntos) for Diputados."""

    def __init__(self):
        super().__init__(DBAsuntoDiputados, DBAsuntoDiputadosPublic)


class AsuntosSenadoresService(AsuntosServiceBase):
    """Service for managing parliamentary issues (asuntos) for Senadores."""

    def __init__(self):
        super().__init__(DBAsuntoSenadores, DBAsuntoSenadoresPublic)


class BloquesServiceBase(BaseService[DBBloqueBase, Any]):
    """Base service for managing parliamentary blocks (bloques)."""

    def get_by_bloque_id(self, bloque_id: int) -> Any | None:
        """Get bloque by original bloque_id."""
        return self._get_by_field("bloque_id", bloque_id)

    def list_all(self, active_only: bool = True, **kwargs) -> list[Any]:
        """list all bloques with optional active filter."""
        filters = kwargs
        if active_only and hasattr(self.model, "activo"):
            filters["activo"] = True
        return super().list_all(**filters)

    def search_by_name(self, name_query: str) -> list[Any]:
        """Search bloques by name."""
        with Session(self.engine) as session:
            bloques = session.exec(
                select(self.model).where(
                    self.model.bloque.contains(name_query)
                )
            ).all()
            return [self.public_model.model_validate(b) for b in bloques]


class BloquesDiputadosService(BloquesServiceBase):
    """Service for managing parliamentary blocks (bloques) for Diputados."""

    def __init__(self):
        super().__init__(DBBloqueDiputados, DBBloqueDiputadosPublic)


class BloquesSenadoresService(BloquesServiceBase):
    """Service for managing parliamentary blocks (bloques) for Senadores."""

    def __init__(self):
        super().__init__(DBBloqueSenadores, DBBloqueSenadoresPublic)


class LegisladoresServiceBase(BaseService[DBLegisladorBase, Any]):
    """Base service for managing legislators."""

    def __init__(
        self,
        model: Type[T],
        public_model: Type[TPublic],
        legislador_id_field: str,
    ):
        super().__init__(model, public_model)
        self.legislador_id_field = legislador_id_field

    def get_by_legislador_id(self, legislador_id: int) -> Any | None:
        """Get legislador by original ID (diputado_id or senador_id)."""
        return self._get_by_field(self.legislador_id_field, legislador_id)

    def list_all(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
        **kwargs,
    ) -> list[Any]:
        """list all legislators with pagination and optional active filter."""
        filters = kwargs
        if active_only and hasattr(self.model, "activo"):
            filters["activo"] = True
        return super().list_all(limit=limit, offset=offset, **filters)

    def get_by_bloque(self, bloque_id: int) -> list[Any]:
        """Get legislators by bloque."""
        return self.list_all(bloque_id=bloque_id, limit=1000)

    def search_by_name(self, name_query: str) -> list[Any]:
        """Search legislators by name."""
        with Session(self.engine) as session:
            legislators = session.exec(
                select(self.model).where(
                    (self.model.nombre.contains(name_query))
                    | (self.model.apellido.contains(name_query))
                    | (self.model.nombre_completo.contains(name_query))
                )
            ).all()
            return [self.public_model.model_validate(l) for l in legislators]


class LegisladoresDiputadosService(LegisladoresServiceBase):
    """Service for managing legislators (diputados)."""

    def __init__(self):
        super().__init__(
            DBLegisladorDiputados, DBLegisladorDiputadosPublic, "diputado_id"
        )

    def get_by_diputado_id(
        self, diputado_id: int
    ) -> DBLegisladorDiputadosPublic | None:
        """Get legislador by original diputado_id."""
        return cast(
            DBLegisladorDiputadosPublic | None,
            self.get_by_legislador_id(diputado_id),
        )


class LegisladoresSenadoresService(LegisladoresServiceBase):
    """Service for managing legislators (senadores)."""

    def __init__(self):
        super().__init__(
            DBLegisladorSenadores, DBLegisladorSenadoresPublic, "senador_id"
        )

    def get_by_senador_id(
        self, senador_id: int
    ) -> DBLegisladorSenadoresPublic | None:
        """Get legislador by original senador_id."""
        return cast(
            DBLegisladorSenadoresPublic | None,
            self.get_by_legislador_id(senador_id),
        )


class VotacionesServiceBase(BaseService[DBVotacionBase, Any]):
    """Base service for managing parliamentary votes (votaciones)."""

    def __init__(
        self,
        model: Type[T],
        public_model: Type[TPublic],
        legislador_id_field: str,
    ):
        super().__init__(model, public_model)
        self.legislador_id_field = legislador_id_field

    def get_by_asunto(self, asunto_id: int, limit: int = 1000) -> list[Any]:
        """Get all votes for a specific asunto."""
        return self.list_all(asunto_id=asunto_id, limit=limit)

    def get_by_legislador(
        self, legislador_id: int, limit: int = 1000
    ) -> list[Any]:
        """Get all votes by a specific legislator."""
        return self.list_all(
            **{self.legislador_id_field: legislador_id}, limit=limit
        )

    def get_by_bloque(self, bloque_id: int, limit: int = 1000) -> list[Any]:
        """Get all votes by a specific bloque."""
        return self.list_all(bloque_id=bloque_id, limit=limit)

    def get_vote_summary_by_asunto(self, asunto_id: int) -> dict[str, int]:
        """Get vote summary for a specific asunto."""
        with Session(self.engine) as session:
            votaciones = session.exec(
                select(self.model).where(self.model.asunto_id == asunto_id)
            ).all()

            summary = {
                "AFIRMATIVO": 0,
                "NEGATIVO": 0,
                "ABSTENCION": 0,
                "AUSENTE": 0,
                "PRESIDENTE": 0,
                "total": len(votaciones),
            }

            for votacion in votaciones:
                if votacion.voto in summary:
                    summary[votacion.voto] += 1

            return summary


class VotacionesDiputadosService(VotacionesServiceBase):
    """Service for managing parliamentary votes (votaciones) for Diputados."""

    def __init__(self):
        super().__init__(
            DBVotacionDiputados, DBVotacionDiputadosPublic, "diputado_id"
        )

    def get_by_diputado(
        self, diputado_id: int, limit: int = 1000
    ) -> list[DBVotacionDiputadosPublic]:
        """Get all votes by a specific diputado."""
        return cast(
            list[DBVotacionDiputadosPublic],
            self.get_by_legislador(diputado_id, limit),
        )


class VotacionesSenadoresService(VotacionesServiceBase):
    """Service for managing parliamentary votes (votaciones) for Senadores."""

    def __init__(self):
        super().__init__(
            DBVotacionSenadores, DBVotacionSenadoresPublic, "senador_id"
        )

    def get_by_senador(
        self, senador_id: int, limit: int = 1000
    ) -> list[DBVotacionSenadoresPublic]:
        """Get all votes by a specific senador."""
        return cast(
            list[DBVotacionSenadoresPublic],
            self.get_by_legislador(senador_id, limit),
        )


# Generic chamber-aware services
class AsuntosService:
    """Unified service for managing parliamentary issues (asuntos) from both chambers."""

    def __init__(self):
        self.diputados_service = AsuntosDiputadosService()
        self.senadores_service = AsuntosSenadoresService()

    def get_service(self, chamber: str):
        """Get the appropriate service based on the chamber."""
        if chamber == "diputados":
            return self.diputados_service
        elif chamber == "senadores":
            return self.senadores_service
        else:
            raise ValueError(f"Invalid chamber: {chamber}")


class BloquesService:
    """Unified service for managing parliamentary blocks (bloques) from both chambers."""

    def __init__(self):
        self.diputados_service = BloquesDiputadosService()
        self.senadores_service = BloquesSenadoresService()

    def get_service(self, chamber: str):
        """Get the appropriate service based on the chamber."""
        if chamber == "diputados":
            return self.diputados_service
        elif chamber == "senadores":
            return self.senadores_service
        else:
            raise ValueError(f"Invalid chamber: {chamber}")


class LegisladoresService:
    """Unified service for managing legislators from both chambers."""

    def __init__(self):
        self.diputados_service = LegisladoresDiputadosService()
        self.senadores_service = LegisladoresSenadoresService()

    def get_service(self, chamber: str):
        """Get the appropriate service based on the chamber."""
        if chamber == "diputados":
            return self.diputados_service
        elif chamber == "senadores":
            return self.senadores_service
        else:
            raise ValueError(f"Invalid chamber: {chamber}")


class VotacionesService:
    """Unified service for managing parliamentary votes (votaciones) from both chambers."""

    def __init__(self):
        self.diputados_service = VotacionesDiputadosService()
        self.senadores_service = VotacionesSenadoresService()

    def get_service(self, chamber: str):
        """Get the appropriate service based on the chamber."""
        if chamber == "diputados":
            return self.diputados_service
        elif chamber == "senadores":
            return self.senadores_service
        else:
            raise ValueError(f"Invalid chamber: {chamber}")


# Service instances for easy import
asuntos_service = AsuntosService()
bloques_service = BloquesService()
legisladores_service = LegisladoresService()
votaciones_service = VotacionesService()
