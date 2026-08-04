# Guia de Desenvolvimento de Plugins de Enriquecimento

Este documento descreve como criar plugins de enriquecimento para o EDY SIEM.

## Visão Geral

Plugins de enriquecimento recebem um ``CanonicalEvent`` e um ``EnrichmentContext``
e retornam um ``EnrichedEvent`` com os enriquecimentos anexados.

O framework garante:
- **Imutabilidade**: eventos nunca são mutados; plugins retornam novo ``EnrichedEvent``
- **Isolamento de falhas**: falha de um plugin não derruba o pipeline
- **Timeout**: execução com timeout configurável por plugin
- **Prioridade**: ordem de execução baseada em prioridade + dependências
- **Métricas**: execução, duração, sucessos/falhas coletadas automaticamente

## Estrutura Mínima de um Plugin

```python
# meu_enricher.py
from edysiem.enrichment import (
    EnrichmentPlugin,
    PluginMetadata,
    PluginPriority,
    Enrichment,
    EnrichmentKind,
    EnrichmentContext,
)
from edysiem.domain import CanonicalEvent, EnrichedEvent
from edysiem.result import Result, ok


class MeuEnricher:
    """Exemplo de plugin de enriquecimento."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            id="meu-enricher",
            name="Meu Enriquecedor Customizado",
            version="1.0.0",
            author="Minha Equipe",
            description="Adiciona contexto customizado a eventos de autenticação",
            priority=PluginPriority.NORMAL,
            supported_event_categories=frozenset(["auth"]),
            timeout_seconds=10.0,
        )

    async def setup(self) -> None:
        """Inicialização: conexões DB, cache warm-up, validações."""
        # self._db = await connect_to_db()
        pass

    async def shutdown(self) -> None:
        """Limpeza: fechar conexões, flush caches."""
        # await self._db.close()
        pass

    async def enrich(
        self, event: CanonicalEvent, context: EnrichmentContext
    ) -> Result[EnrichedEvent]:
        """Executa o enriquecimento.

        Args:
            event: Evento canônico a enriquecer.
            context: Contexto compartilhado (asset DB, geo, intel, etc.).

        Returns:
            Success(EnrichedEvent) com enriquecimentos anexados;
            Failure se erro.
        """
        # 1. Validar se deve processar este evento
        if event.event_category != "auth":
            return ok(event)  # Não enriquece, retorna original

        # 2. Buscar dados no contexto
        user_info = None
        if event.user:
            user_info = await context.get_user_info(event.user)

        # 3. Construir enriquecimento
        enrichment = Enrichment(
            kind=EnrichmentKind.USER,
            provider="meu-enricher",
            data={
                "department": user_info.department if user_info else "unknown",
                "is_privileged": user_info.is_privileged if user_info else False,
            },
        )

        # 4. Retornar EnrichedEvent (imutável - cria novo)
        enriched = EnrichedEvent(
            event_id=event.event_id,
            trace_id=event.trace_id,
            timestamp=event.timestamp,
            received_at=event.received_at,
            source_type=event.source_type,
            source_host=event.source_host,
            hostname=event.hostname,
            event_category=event.event_category,
            event_action=event.event_action,
            severity=event.severity,
            user=event.user,
            process=event.process,
            command_line=event.command_line,
            ip_src=event.ip_src,
            ip_dst=event.ip_dst,
            vendor=event.vendor,
            product=event.product,
            event_original=event.event_original,
            normalized_fields=event.normalized_fields,
            tags=event.tags,
            confidence=event.confidence,
            metadata=event.metadata,
            schema_version=event.schema_version,
            normalized_at=event.normalized_at,
            enrichments=(enrichment,),
        )

        return ok(enriched)
```

## Registro do Plugin

```python
from edysiem.enrichment import EnrichmentEngine, EnrichmentRegistry, EnrichmentContext

# Criar registry e contexto
registry = EnrichmentRegistry()
context = EnrichmentContext()  # Com providers reais em produção

# Registrar plugins
registry.register(MeuEnricher())
registry.register(OutroEnricher())

# Criar engine
engine = EnrichmentEngine(registry, context)

# Usar
enriched = await engine.enrich(canonical_event)
```

## Metadados Obrigatórios

Todo plugin deve declarar ``PluginMetadata`` com:

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| ``id`` | ``str`` | Sim | Identificador único (ex.: ``"asset-enricher"``) |
| ``name`` | ``str`` | Sim | Nome legível |
| ``version`` | ``str`` | Sim | Versão semântica (ex.: ``"1.0.0"``) |
| ``author`` | ``str`` | Sim | Autor/origem |
| ``description`` | ``str`` | Não | Descrição do que faz |
| ``priority`` | ``PluginPriority`` | Não | Ordem execução (padrão: NORMAL) |
| ``dependencies`` | ``frozenset[str]`` | Não | IDs de plugins dependentes |
| ``supported_event_categories`` | ``frozenset[str]`` | Não | Categorias suportadas (vazio = todas) |
| ``cache_policy`` | ``str`` | Não | ``"none"``, ``"ttl"``, ``"eternal"`` |
| ``timeout_seconds`` | ``float`` | Não | Timeout execução (0 = sem limite) |
| ``tags`` | ``frozenset[str]`` | Não | Tags para agrupamento |
| ``enabled`` | ``bool`` | Não | Ativo por padrão (padrão: True) |

## Prioridades

```python
from edysiem.enrichment import PluginPriority

PluginPriority.CRITICAL  # 0  - Executa primeiro (ex.: asset crítico)
PluginPriority.HIGH  # 10 - Alta prioridade
PluginPriority.NORMAL  # 50 - Padrão
PluginPriority.LOW  # 100 - Baixa prioridade
PluginPriority.BACKGROUND  # 200 - Executa por último
```

## Dependências

Plugins podem declarar dependências:

```python
PluginMetadata(
    id="enricher-composto",
    ...
    dependencies=frozenset(["asset-enricher", "geo-enricher"]),
)
```

O registry resolve dependências topologicamente (Kahn's algorithm) e detecta ciclos.

## Categorias de Evento Suportadas

```python
supported_event_categories = frozenset(
    [
        "auth",  # Autenticação (logon, logoff, falha)
        "network",  # Rede (conexão, DNS, HTTP)
        "process",  # Processo (create, terminate, inject)
        "file",  # Arquivo (create, modify, delete)
        "system",  # Sistema (boot, shutdown, service)
        "threat",  # Ameaça (malware, exploit, C2)
    ]
)
```

Vazio = suporta todas as categorias.

## Acesso ao Contexto

O ``EnrichmentContext`` fornece:

```python
async def enrich(self, event: CanonicalEvent, context: EnrichmentContext):
    # Asset DB
    asset = await context.get_asset_by_ip(event.ip_src)
    asset = await context.get_asset_by_hostname(event.hostname)

    # GeoIP
    geo = await context.get_geo_info(event.ip_src)

    # Threat Intel
    intel = await context.check_threat_intel(event.ip_src, "ip")

    # User Directory
    user = await context.get_user_info(event.user)

    # Cache compartilhado
    cached = context._get_from_cache("minha-chave")
    context._set_cache("minha-chave", valor, ttl=600)
```

## Timeout e Falhas

- Timeout padrão do engine: 30s
- Timeout por plugin: ``metadata.timeout_seconds`` (0 = usa padrão do engine)
- Falha de plugin **não para o pipeline** - erro é logado e métricas coletadas
- ``EnrichmentTimeoutError`` lançado se exceder timeout

## Métricas Coletadas Automaticamente

Por plugin:
- Execuções totais
- Falhas totais
- Duração média (ms)
- Enriquecimentos aplicados

Agregadas:
- Eventos processados
- Enriquecimentos aplicados
- Duração média do pipeline
- Cache hit/miss por fonte (asset, geo, intel, user)

## Testes

```python
import pytest
from edysiem.enrichment import EnrichmentRegistry, EnrichmentContext, EnrichmentEngine
from edysiem.domain import CanonicalEvent, Severity
from datetime import datetime, UTC


@pytest.fixture
def engine():
    registry = EnrichmentRegistry()
    registry.register(MeuEnricher())
    context = EnrichmentContext()
    return EnrichmentEngine(registry, context)


@pytest.mark.asyncio
async def test_enrichment_adiciona_contexto(engine):
    event = CanonicalEvent(
        event_id="test-1",
        trace_id="trace-1",
        timestamp=datetime.now(UTC),
        received_at=datetime.now(UTC),
        source_type="windows",
        source_host="wks-01",
        event_category="auth",
        event_action="logon",
        severity=Severity.INFO,
        user="admin",
    )
    result = await engine.enrich(event)
    assert result.is_ok()
    enriched = result.unwrap()
    assert len(enriched.enrichments) == 1
    assert enriched.enrichments[0].provider == "meu-enricher"
```

## Boas Práticas

1. **Sempre retorne ``ok(event)`` se não houver enriquecimento aplicável**
2. **Nunca mutar o evento de entrada** - crie novo ``EnrichedEvent``
3. **Use ``async/await`` para I/O** (DB, HTTP, cache)
4. **Declare dependências explicitamente** no metadata
5. **Trate exceções** - retorne ``Failure`` em vez de levantar
6. **Use cache** para evitar consultas repetidas
7. **Declare ``timeout_seconds``** realista para seu plugin
8. **Implemente ``setup()``/``shutdown()``** para recursos

## Exemplos de Plugins Oficiais (Futuros)

| Plugin | ID | Categoria | Descrição |
|--------|-----|-----------|-----------|
| Asset Enricher | ``asset-enricher`` | all | Contexto de ativo (owner, criticality, tags) |
| Geo Enricher | ``geo-enricher`` | network, auth | GeoIP (país, cidade, ASN, VPN/Proxy/Tor) |
| Threat Intel | ``threat-intel-enricher`` | all | IOCs, reputação, feeds de ameaça |
| User Enricher | ``user-enricher`` | auth | Diretório de usuários (dept, roles, privileged) |
| Process Enricher | ``process-enricher`` | process | Árvore de processos, lineage, reputation |
| Network Enricher | ``network-enricher`` | network | Whois, passive DNS, certificados TLS |

## Diretório de Plugins

Plugins oficiais ficam em ``src/edysiem/enrichment/plugins/``:

```
enrichment/
├── plugins/
│   ├── __init__.py          # Exports oficiais
│   ├── asset.py             # AssetEnricher
│   ├── geo.py               # GeoEnricher
│   ├── intel.py             # ThreatIntelEnricher
│   ├── user.py              # UserEnricher
│   └── custom/              # Seus plugins customizados
│       ├── __init__.py
│       └── meu_enricher.py
```

Para usar plugins customizados, importe e registre:

```python
from edysiem.enrichment.plugins.custom import MeuEnricher

registry.register(MeuEnricher())
```