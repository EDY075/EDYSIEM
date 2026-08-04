"""Search Engine da camada de persistencia.

Busca desacoplada sobre Alert/Incident/Case com:
- Paginacao, ordenacao, filtros
- Busca parcial (LIKE) e exata (EQ)
- Campos: ioc, asset, user, hostname, ip, hash, mitre, rule, severity, status

O SQL fica isolado nos repositorios; esta camada compoe filtros declarativos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypeVar

from edysiem.alerts import Alert, AlertSeverity
from edysiem.cases import Case
from edysiem.incidents import Incident

from .query import Page, QueryFilter, QueryOp, SortOrder
from .repos.alerts import AlertRepository
from .repos.cases import CaseRepository
from .repos.incidents import IncidentRepository
from .repository import GenericRepository

T = TypeVar("T")


def _filters(*pairs: tuple[str, Any]) -> list[QueryFilter]:
    """Constroi filtros EQ a partir de pares (campo, valor) nao-None."""
    return [QueryFilter(field=f, value=v) for f, v in pairs if v is not None]


def _like(*pairs: tuple[str, str | None]) -> list[QueryFilter]:
    """Constroi filtros CONTAINS (busca parcial) a partir de pares."""
    return [
        QueryFilter(field=f, op=QueryOp.CONTAINS, value=v)
        for f, v in pairs
        if v is not None and v != ""
    ]


def _paginate(
    repo: GenericRepository[T],
    filters: list[QueryFilter],
    *,
    sort_by: str,
    order: SortOrder,
    limit: int,
    offset: int,
) -> Page[T]:
    """Executa consulta com filtros e paginacao."""
    return repo.query(filters, sort_by=sort_by, order=order, limit=limit, offset=offset)


def _empty_page() -> Page[Any]:
    """Pagina vazia padrao."""
    return Page(items=[], total=0, offset=0, limit=0)


@dataclass(frozen=True, slots=True)
class SearchResults:
    """Resultado agregado de uma busca multi-entidade.

    Attributes:
        alerts: Pagina de alertas.
        incidents: Pagina de incidentes.
        cases: Pagina de cases.
    """

    alerts: Page[Alert] = field(default_factory=_empty_page)
    incidents: Page[Incident] = field(default_factory=_empty_page)
    cases: Page[Case] = field(default_factory=_empty_page)

    @property
    def total(self) -> int:
        """Total agregado de resultados."""
        return self.alerts.total + self.incidents.total + self.cases.total


class SearchEngine:
    """Busca desacoplada sobre os repositorios de Alert/Incident/Case.

    Args:
        alerts: Repositorio de alertas.
        incidents: Repositorio de incidentes.
        cases: Repositorio de cases.
    """

    def __init__(
        self,
        alerts: AlertRepository,
        incidents: IncidentRepository,
        cases: CaseRepository,
    ) -> None:
        self._alerts = alerts
        self._incidents = incidents
        self._cases = cases

    # --- Alert ----------------------------------------------------------

    def search_alerts(
        self,
        *,
        term: str | None = None,
        rule: str | None = None,
        severity: str | AlertSeverity | None = None,
        status: str | None = None,
        ioc: str | None = None,
        asset: str | None = None,
        user: str | None = None,
        hash: str | None = None,
        mitre: str | None = None,
        exact: bool = False,
        sort_by: str = "created_at",
        order: SortOrder = SortOrder.DESC,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[Alert]:
        """Busca alertas por multiplos campos.

        ``term`` busca em title/description/rule_id (parcial ou exata).
        ``exact=True`` usa igualdade; ``False`` usa LIKE (parcial).
        """
        filters: list[QueryFilter] = []

        if term:
            op = QueryOp.EQ if exact else QueryOp.CONTAINS
            filters.append(QueryFilter(field="title", op=op, value=term))

        filters += _like(("ioc_ids", ioc), ("mitre", mitre))
        filters += _filters(
            ("rule_id", rule),
            ("asset_id", asset),
            ("user", user),
            ("fingerprint_hash", hash),
        )
        if severity is not None:
            value = severity.value if isinstance(severity, AlertSeverity) else severity
            filters.append(QueryFilter(field="severity", value=value))
        if status:
            filters.append(QueryFilter(field="status", value=status))

        return _paginate(
            self._alerts, filters, sort_by=sort_by, order=order, limit=limit, offset=offset
        )

    # --- Incident --------------------------------------------------------

    def search_incidents(
        self,
        *,
        term: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        ioc: str | None = None,
        asset: str | None = None,
        user: str | None = None,
        hash: str | None = None,
        mitre: str | None = None,
        exact: bool = False,
        sort_by: str = "created_at",
        order: SortOrder = SortOrder.DESC,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[Incident]:
        """Busca incidentes por multiplos campos."""
        filters: list[QueryFilter] = []

        if term:
            op = QueryOp.EQ if exact else QueryOp.CONTAINS
            filters.append(QueryFilter(field="title", op=op, value=term))

        filters += _like(("iocs", ioc), ("assets", asset), ("users", user), ("mitre", mitre))
        filters += _filters(("severity", severity), ("status", status), ("fingerprint_hash", hash))

        return _paginate(
            self._incidents, filters, sort_by=sort_by, order=order, limit=limit, offset=offset
        )

    # --- Case ------------------------------------------------------------

    def search_cases(
        self,
        *,
        term: str | None = None,
        owner: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        ioc: str | None = None,
        asset: str | None = None,
        user: str | None = None,
        mitre: str | None = None,
        exact: bool = False,
        sort_by: str = "created_at",
        order: SortOrder = SortOrder.DESC,
        limit: int = 50,
        offset: int = 0,
    ) -> Page[Case]:
        """Busca cases por multiplos campos."""
        filters: list[QueryFilter] = []

        if term:
            op = QueryOp.EQ if exact else QueryOp.CONTAINS
            filters.append(QueryFilter(field="title", op=op, value=term))

        filters += _like(("iocs", ioc), ("assets", asset), ("users", user), ("mitre", mitre))
        filters += _filters(("owner", owner), ("severity", severity), ("status", status))

        return _paginate(
            self._cases, filters, sort_by=sort_by, order=order, limit=limit, offset=offset
        )

    # --- Multi-entidade ----------------------------------------------------

    def search(
        self,
        *,
        term: str | None = None,
        ioc: str | None = None,
        asset: str | None = None,
        user: str | None = None,
        hostname: str | None = None,
        ip: str | None = None,
        hash: str | None = None,
        mitre: str | None = None,
        rule: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        entity: str | None = None,
        exact: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> SearchResults:
        """Busca agregada por entidades (Alert/Incident/Case).

        ``entity`` filtra por tipo: ``"alert"``, ``"incident"``, ``"case"``.
        ``hostname``/``ip`` buscam nos campos de identidade disponiveis
        (asset/user/ioc dos agregados).
        """
        # hostname/ip nao sao colunas dos agregados; mapeia para asset/user/ioc
        alias_term = hostname or ip

        alerts = incidents = cases = None
        if entity in (None, "alert"):
            alerts = self.search_alerts(
                term=term,
                rule=rule,
                severity=severity,
                status=status,
                ioc=ioc or alias_term,
                asset=asset or alias_term,
                user=user,
                hash=hash,
                mitre=mitre,
                exact=exact,
                limit=limit,
                offset=offset,
            )
        if entity in (None, "incident"):
            incidents = self.search_incidents(
                term=term,
                severity=severity,
                status=status,
                ioc=ioc or alias_term,
                asset=asset or alias_term,
                user=user,
                hash=hash,
                mitre=mitre,
                exact=exact,
                limit=limit,
                offset=offset,
            )
        if entity in (None, "case"):
            cases = self.search_cases(
                term=term,
                owner=user,
                severity=severity,
                status=status,
                ioc=ioc or alias_term,
                asset=asset or alias_term,
                user=user,
                mitre=mitre,
                exact=exact,
                limit=limit,
                offset=offset,
            )

        return SearchResults(
            alerts=alerts if alerts is not None else _empty_page(),
            incidents=incidents if incidents is not None else _empty_page(),
            cases=cases if cases is not None else _empty_page(),
        )


__all__ = ["SearchEngine", "SearchResults"]
