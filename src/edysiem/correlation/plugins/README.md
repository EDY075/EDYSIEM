# Guia de Desenvolvimento de Regras de Correlacao

Este documento descreve como criar regras de correlacao para o EDY SIEM.

## Visao Geral

Regras de correlacao recebem um ``EnrichedEvent`` e um ``CorrelationContext``
e retornam um ``CorrelationResult``. O framework garante:

- **Isolamento de falhas**: falha de uma regra nao derruba o pipeline
- **Timeout**: execucao com timeout configuravel por regra
- **Prioridade**: ordem de execucao baseada em prioridade + dependencias
- **Metricas**: execucao, matches, falhas, timeouts coletados automaticamente
- **Janelas temporais**: o ``CorrelationContext`` mantem estado de janela por regra + chave

## Estrutura Minima de uma Regra

```python
# minha_regra.py
from edysiem.correlation import (
    CorrelationRule,
    CorrelationMetadata,
    CorrelationPriority,
    CorrelationMatch,
    CorrelationReason,
    CorrelationResult,
    CorrelationContext,
)
from edysiem.domain import EnrichedEvent


class MinhaRegra:
    """Exemplo de regra de correlacao."""

    @property
    def metadata(self) -> CorrelationMetadata:
        return CorrelationMetadata(
            id="minha-regra",
            name="Minha Regra",
            version="1.0.0",
            description="Detecta X",
            priority=CorrelationPriority.NORMAL,
            author="Minha Equipe",
            required_fields=frozenset(["ip_src"]),
            required_event_types=frozenset(["auth", "network"]),
            window_seconds=300.0,  # usa janela de 5 minutos
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(
        self, event: EnrichedEvent, context: CorrelationContext
    ) -> CorrelationResult:
        # 1. Validar se a regra se aplica
        if not event.ip_src:
            return CorrelationResult.no_match(duration_ms=0.0, rule_id=self.metadata.id)

        # 2. Acumular estado na janela
        context.add_event(
            rule_id=self.metadata.id,
            identity_key=event.ip_src,
            event_id=event.event_id,
        )

        # 3. Consultar janela
        window = context.get_window(self.metadata.id, event.ip_src, 300.0)

        # 4. Decidir
        if len(window) < 3:
            return CorrelationResult.deferred(duration_ms=0.0, rule_id=self.metadata.id)

        # 5. Disparar match
        match = CorrelationMatch(
            rule_id=self.metadata.id,
            matched_event_ids=window,
            reason=CorrelationReason(
                rule_id=self.metadata.id,
                condition="3 eventos do mesmo IP na janela",
                values={"ip_src": event.ip_src, "count": len(window)},
            ),
        )
        return CorrelationResult.match(matches=(match,), duration_ms=0.0, rule_id=self.metadata.id)
```

## Registro e Uso

```python
from edysiem.correlation import (
    CorrelationEngine,
    CorrelationRegistry,
    CorrelationContext,
)

registry = CorrelationRegistry()
registry.register(MinhaRegra())

context = CorrelationContext()
engine = CorrelationEngine(registry, context)

correlated = await engine.process(enriched_event)
for match in correlated.matches:
    print(match.rule_id, match.reason.values)
```

## Metadados Obrigatorios

Todo regra deve declarar ``CorrelationMetadata``:

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| ``id`` | ``str`` | Sim | Identificador unico (ex.: ``"brute-force"``) |
| ``name`` | ``str`` | Sim | Nome legivel |
| ``version`` | ``str`` | Sim | Versao semantica (ex.: ``"1.0.0"``) |
| ``description`` | ``str`` | Nao | Descricao do que detecta |
| ``priority`` | ``CorrelationPriority`` | Nao | Ordem de execucao (padrao: NORMAL) |
| ``author`` | ``str`` | Nao | Autor/origem (padrao: ``"edysiem"``) |
| ``required_fields`` | ``frozenset[str]`` | Nao | Campos obrigatorios no evento; regra e pulada se faltar |
| ``required_event_types`` | ``frozenset[str]`` | Nao | Tipos de evento suportados (vazio = todos) |
| ``window_seconds`` | ``float | None`` | Nao | Janela temporal (None = sem janela) |
| ``dependencies`` | ``frozenset[str]`` | Nao | IDs de regras dependentes |
| ``enabled_by_default`` | ``bool`` | Nao | Ativa por padrao (padrao: True) |
| ``timeout_seconds`` | ``float`` | Nao | Timeout de execucao (0 = default do engine, 5s) |
| ``tags`` | ``frozenset[str]`` | Nao | Tags para agrupamento |

## Prioridades

```python
from edysiem.correlation import CorrelationPriority

CorrelationPriority.CRITICAL  # 0   - executa primeiro
CorrelationPriority.HIGH  # 10  - alta prioridade
CorrelationPriority.NORMAL  # 50  - padrao
CorrelationPriority.LOW  # 100 - baixa prioridade
CorrelationPriority.BACKGROUND  # 200 - executa por ultimo
```

## Campos Disponiveis no Evento (EnrichedEvent)

Os ``required_fields`` usam nomes de campos canonicos:
``ip_src``, ``ip_dst``, ``user``, ``hostname``, ``source_host``,
``event_category``, ``event_action``, ``process``, ``command_line``.

O engine **pula a regra** se o evento nao tiver os campos exigidos.

## Decisoes Retornadas

| Decisao | Significado | Uso |
|---------|-------------|-----|
| ``MATCH`` | A regra disparou | Produz ``CorrelationMatch`` |
| ``NO_MATCH`` | A regra nao se aplica | Continua pipeline |
| ``DEFERRED`` | Acumulando estado na janela | Continua pipeline sem match |

## Janela Temporal (CorrelationContext)

Regras baseadas em janela acumulam eventos por ``(rule_id, identity_key)``:

```python
# Adicionar evento a janela
context.add_event(rule_id, identity_key, event_id)

# Consultar eventos na janela (mais recentes primeiro)
window = context.get_window(rule_id, identity_key, window_seconds)

# Quantidade na janela
count = context.window_size(rule_id, identity_key, window_seconds)
```

A expiracao e **lazy**: eventos fora da janela sao descartados ao acessar.
Janelas vazias sao removidas automaticamente para nao vazar memoria.

## Timeout e Falhas

- Timeout padrao do engine: 5s
- Timeout por regra: ``metadata.timeout_seconds`` (0 = usa default)
- Falha de regra **nao para o pipeline** - erro logado + metrica
- ``CorrelationRuleTimeoutError`` ao exceder timeout

## Metricas Coletadas Automaticamente

Por regra:
- Execucoes
- Matches
- Falhas
- Timeouts

Agregadas:
- Eventos processados
- Duracao media
- Tamanho do estado (janelas ativas)

## Boas Praticas

1. **Sempre retorne um ``CorrelationResult``** - nunca levante excecao diretamente
2. **Declare ``required_fields``** para regras especificas
3. **Use ``CorrelationResult.deferred``** para regras que acumulam estado
4. **Nunca mutar o evento de entrada**
5. **Use async/await** para I/O externo
6. **Escolha ``identity_key`` com cuidado** (IP, user, host) para limitar estado
7. **Defina ``window_seconds``** realista para sua regra

## Exemplos de Regras Oficiais (Futuras)

| Regra | ID | Janela | Descricao |
|-------|-----|--------|-----------|
| DEMO Threshold | ``demo-threshold-by-ip`` | configuravel | Mesmo IP gerou N eventos em X minutos |
| Brute Force | ``brute-force`` | sim | Multiplas falhas de autenticacao no mesmo host |
| Impossible Travel | ``impossible-travel`` | sim | Login em locais geograficamente distantes |
| Beaconing | ``beaconing`` | sim | Comunicacoes periodicas com C2 |
| Data Exfil | ``data-exfil`` | sim | Grande volume de dados para IP externo |

## Diretorio de Regras

Regras oficiais ficam em ``src/edysiem/correlation/plugins/``:

```
correlation/
├── plugins/
│   ├── __init__.py        # Exports oficiais
│   ├── demo.py            # DEMO: ThresholdByIpRule
│   ├── brute_force.py     # (futuro)
│   ├── impossible_travel.py  # (futuro)
│   ├── beaconing.py       # (futuro)
│   └── custom/            # Suas regras customizadas
│       ├── __init__.py
│       └── minha_regra.py
```

Para usar regras customizadas:

```python
from edysiem.correlation.plugins.custom import MinhaRegra

registry.register(MinhaRegra())
```