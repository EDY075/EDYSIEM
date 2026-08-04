# Guia de Desenvolvimento de Regras de Deteccao

Este documento descreve como criar regras de deteccao para o EDY SIEM.

## Visao Geral

Regras de deteccao recebem um ``CorrelatedEvent`` e um ``DetectionContext``
e retornam um ``DetectionResult``. O framework garante:

- **Isolamento de falhas**: falha de uma regra nao derruba o pipeline
- **Timeout**: execucao com timeout configuravel por regra
- **Prioridade**: ordem de execucao baseada em prioridade + dependencias
- **Metricas**: execucao, deteccoes, falhas, timeouts coletados automaticamente
- **Validacao**: regras sao validadas antes de executar

## Estrutura Minima de uma Regra

```python
# minha_regra.py
from edysiem.detection import (
    DetectionRule,
    RuleMetadata,
    DetectionPriority,
    DetectionFinding,
    DetectionReason,
    DetectionResult,
    DetectionContext,
)
from edysiem.correlation import CorrelatedEvent
from edysiem.domain import Severity, RiskScore


class MinhaRegra:
    """Exemplo de regra de deteccao."""

    @property
    def metadata(self) -> RuleMetadata:
        return RuleMetadata(
            id="minha-regra",
            name="Minha Regra",
            version="1.0.0",
            description="Detecta X",
            priority=DetectionPriority.NORMAL,
            severity=Severity.HIGH,
            confidence=0.9,
            risk_score=RiskScore(70),
            required_fields=frozenset(["ip_src"]),
            tags=frozenset(["custom"]),
        )

    async def setup(self) -> None:
        pass

    async def shutdown(self) -> None:
        pass

    async def evaluate(self, event: CorrelatedEvent, context: DetectionContext) -> DetectionResult:
        source = event.source_event

        # 1. Verificar condicao
        if source.ip_src == "1.2.3.4":
            finding = DetectionFinding(
                rule_id=self.metadata.id,
                event_ids=(event.event_id,),
                reason=DetectionReason(
                    rule_id=self.metadata.id,
                    condition="IP malicioso detectado",
                    values={"ip_src": source.ip_src},
                ),
                severity=Severity.HIGH,
                confidence=0.9,
                risk_score=RiskScore(70),
            )
            return DetectionResult.detected(
                findings=(finding,), duration_ms=0.0, rule_id=self.metadata.id
            )

        return DetectionResult.no_detection(duration_ms=0.0, rule_id=self.metadata.id)
```

## Registro e Uso

```python
from edysiem.detection import (
    DetectionEngine,
    DetectionRegistry,
    RuleEngine,
)

registry = DetectionRegistry()
registry.register(MinhaRegra())

rule_engine = RuleEngine(registry)
det_engine = DetectionEngine(rule_engine)

outcome = await det_engine.process(correlated_event)
if outcome.detected_rule_ids:
    print("Deteccao:", outcome.detected_rule_ids)
```

## Metadados Obrigatorios

Toda regra deve declarar ``RuleMetadata``:

| Campo | Tipo | Obrigatorio | Descricao |
|-------|------|-------------|-----------|
| ``id`` | ``str`` | Sim | Identificador unico (ex.: ``"brute-force"``) |
| ``name`` | ``str`` | Sim | Nome legivel |
| ``version`` | ``str`` | Sim | Versao semantica |
| ``description`` | ``str`` | Nao | Descricao do que detecta |
| ``author`` | ``str`` | Nao | Autor/origem (padrao: ``"edysiem"``) |
| ``priority`` | ``DetectionPriority`` | Nao | Ordem de execucao (padrao: NORMAL) |
| ``severity`` | ``Severity`` | Nao | Severidade da deteccao (padrao: MEDIUM) |
| ``confidence`` | ``float`` | Nao | Confianca 0.0-1.0 (padrao: 1.0) |
| ``risk_score`` | ``RiskScore`` | Nao | Risco 0-100 (padrao: 50) |
| ``required_fields`` | ``frozenset[str]`` | Nao | Campos obrigatorios no evento; regra e pulada se faltar |
| ``dependencies`` | ``frozenset[str]`` | Nao | IDs de regras dependentes |
| ``enabled`` | ``bool`` | Nao | Ativa por padrao (padrao: True) |
| ``tags`` | ``frozenset[str]`` | Nao | Tags para agrupamento |
| ``timeout_seconds`` | ``float`` | Nao | Timeout de execucao (0 = default do engine, 5s) |

## Decisoes Retornadas

| Decisao | Significado | Uso |
|---------|-------------|-----|
| ``DETECTED`` | Condicao de interesse detectada | Produz ``DetectionFinding`` |
| ``NO_DETECTION`` | Regra nao se aplica | Continua pipeline |
| ``DEFERRED`` | Acumulando estado na janela | Continua sem deteccao |

## DSL de Condicoes

A DSL (``detection.dsl``) fornece blocos para condicoes declarativas:

```python
from edysiem.detection import RuleCondition, RuleExpression, RuleLogicalOp, RuleOperator

# Condicao atomica
cond = RuleCondition(field="event_category", operator=RuleOperator.EQ, value="auth")

# Expressao composta
expr = RuleExpression(
    logical=RuleLogicalOp.AND,
    operands=(
        RuleCondition("event_category", RuleOperator.EQ, "auth"),
        RuleCondition("severity", RuleOperator.GTE, "high"),
    ),
)

# Avaliar contra um mapa field->valor
matched = expr.evaluate({"event_category": "auth", "severity": "high"})
```

Parser minimo da sintaxe ``WHEN ... AND ... THEN``:

```python
from edysiem.detection import parse_rule_text

expr = parse_rule_text(
    "WHEN event.category == authentication AND event.severity >= HIGH THEN raise_alert()"
)
matched = expr.evaluate({"category": "authentication", "severity": "HIGH"})
```

Em sprints futuras o parser evoluira para Sigma/MITRE sem alterar o modelo.

## Buffer Temporal (DetectionContext)

Regras de threshold acumulam eventos por ``(rule_id, identity_key)``:

```python
context.add_event(rule_id, identity_key, event_id)
window = context.get_window(rule_id, identity_key, window_seconds)
count = context.window_size(rule_id, identity_key, window_seconds)
```

## Boas Praticas

1. **Sempre retorne um ``DetectionResult``** - nunca levante excecao diretamente
2. **Declare ``required_fields``** para regras especificas
3. **Use ``DetectionResult.deferred``** para regras que acumulam estado
4. **Nunca mutar o evento de entrada**
5. **Use async/await** para I/O externo
6. **Defina ``severity``, ``confidence`` e ``risk_score``** consistentes
7. **Valide com ``rule_engine.validate_rule(rule)``** antes de ativar

## Exemplos de Regras Oficiais (Futuras)

| Regra | ID | Descricao |
|-------|-----|-----------|
| DEMO Login Failures | ``demo-login-failures`` | Mais de N falhas de login em X minutos |
| Brute Force | ``brute-force`` | Ataque de forca bruta por host |
| Malware | ``malware-detection`` | Assinaturas de malware |
| Exfiltration | ``exfiltration`` | Grande volume de dados para IP externo |

## Diretorio de Regras

Regras oficiais ficam em ``src/edysiem/detection/plugins/``:

```
detection/
├── plugins/
│   ├── __init__.py        # Exports oficiais
│   ├── demo.py            # DEMO: LoginFailuresRule
│   ├── brute_force.py     # (futuro)
│   ├── malware.py         # (futuro)
│   └── custom/            # Suas regras customizadas
│       ├── __init__.py
│       └── minha_regra.py
```