# EDY SIEM — Threat Model

> Análise de ameaças à plataforma (metodologia STRIDE aplicada por componente).
> Foco: proteger o SIEM e os dados que ele processa.

## 1. Escopo

Componentes: Collectors, Ingestion, Normalization, Enrichment, Correlation, Detection,
Incident, Persistence, API, UI, CLI, Regras (YAML).

## 2. STRIDE por componente

### Collectors / Ingestion
| Ameaça | Mitigação |
|---|---|
| Spoofing (fonte falsa injeta eventos) | Whitelist de fontes; validação de schema bruto; campo source_host confiável |
| DoS via flood de eventos | Backpressure, filas limitadas, rate limit por fonte |
| Evento malformado | Falha tolerada (log + drop), nunca crash |
| Injeção de payload malicioso no campo raw | `raw` nunca é executado; apenas armazenado; parsers não avaliam |

### Normalization / Enrichment
- Enricher com timeout; falha degrada graciosamente (ADR-003).
- Dados externos (threat intel) sempre tratados como não confiáveis (escapados).

### Correlation / Detection
- Regras declarativas: validadas por schema, **sem execução arbitrária** (ADR-004).
- Evitar ReDoS: regex limitadas/validáveis nas condições.

### Persistence
- SQL parametrizado (zero concat).
- Eventos append-only; backup/retention futuros.
- Secrets nunca no banco de regras (valores em env).

### API
- Autenticação + autorização por papel (analyst/admin).
- Rate limiting + payload limitado.
- Erros não vazam stack (trace_id + mensagem genérica).

### UI
- XSS: escape total de dados renderizados.
- CSP restritiva; sem inline scripts desnecessários.

### CLI
- Validação de inputs; caminhos seguros (resolve + containment).

## 3. Matriz de riscos (v1)

| Risco | Impacto | Probabilidade | Prioridade |
|---|---|---|---|
| Injeção de eventos falsos | Médio | Alta | Alta |
| DoS na ingestão | Alto | Média | Alta |
| Acesso não autorizado à API | Alto | Média | Alta |
| XSS no dashboard | Alto | Baixa | Alta |
| Erro de regra causa falso positivo em massa | Médio | Média | Média |

## 4. Resposta a incidentes da plataforma

- Health endpoint + logs estruturados (trace_id) para diagnóstico.
- Kill switch de regra (disable) sem deploy.
- Backup de banco para recuperação.

## 5. Limitações conhecidas

- Threat intel offline/local na v1 (sem API externa obrigatória).
- Auth local (sem SSO/OAuth na v1) — documentado como evolução.
