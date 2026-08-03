# EDY SIEM — Business Rules

> Todas as regras de negócio do domínio. **Nada implícito.** Toda regra aqui é
> implementada e testada na Sprint 1+. Classificação: [CRÍTICA] [REGRAS] [UX] [FUTURO].

---

## 1. Eventos

- BR-E01 [CRÍTICA] Evento é **imutável** após normalização.
- BR-E02 [CRÍTICA] Todo evento possui `trace_id` desde a ingestão.
- BR-E03 [CRÍTICA] Eventos são **append-only** (nunca UPDATE/DELETE).
- BR-E04 [REGRAS] Re-ingestão do mesmo evento não duplica (idempotência por chave).
- BR-E05 [REGRAS] Evento malformado → log estruturado + drop controlado (nunca crash).
- BR-E06 [REGRAS] Enriquecimento gera derivado; nunca muta o evento original.
- BR-E07 [UX] Evento deve expor: o quê, onde, risco, quem.

## 2. Detecção e regras

- BR-D01 [CRÍTICA] Regras são **declarativas** (YAML validado); sem execução arbitrária.
- BR-D02 [CRÍTICA] Todo alerta tem `severity` e `mitre` (tactic/technique).
- BR-D03 [REGRAS] Regra nova exige **teste** antes de ativar.
- BR-D04 [REGRAS] Alteração de regra incrementa `version`; soft-disable (enabled=0).
- BR-D05 [REGRAS] Regra inválida não entra em produção (schema falha).
- BR-D06 [CRÍTICA] Fingerprint de alerta é determinístico (dedupe).

## 3. Alertas

- BR-A01 [CRÍTICA] Transições de status são **validas**: OPEN→TRIAGE→INVESTIGATING→
  RESOLVED/FALSE_POSITIVE (reopen permitido).
- BR-A02 [REGRAS] Alerta deduplicado não gera novo alerta (incrementa count).
- BR-A03 [REGRAS] Evidências referenciam events imutáveis.
- BR-A04 [UX] Alerta responde: o quê, impacto, o que fazer, onde clicar.
- BR-A05 [REGRAS] Ação em lote > 5 itens ou destrutiva pede confirmação.

## 4. Cases/Incidentes

- BR-C01 [CRÍTICA] Case agrega alertas (1..N); não existe sem alerta inicial.
- BR-C02 [CRÍTICA] Toda transição de status gera Audit.
- BR-C03 [REGRAS] Timeline de ações é **append-only**.
- BR-C04 [REGRAS] Nota exige autor + hora; editável só pelo autor (por enquanto).
- BR-C05 [REGRAS] Reopen só de RESOLVED/FALSE_POSITIVE para OPEN.

## 5. IOCs e Intelligence

- BR-I01 [CRÍTICA] IOC é UNIQUE (type, value).
- BR-I02 [REGRAS] IOC ativo participa do match de enriquecimento.
- BR-I03 [REGRAS] Feed importado versionável; IOC revogado não gera match.
- BR-I04 [FUTURO] Reputação (threat intel online) aplicada como enrichment opcional.

## 6. Assets

- BR-AS01 [CRÍTICA] Asset UNIQUE por hostname/IP.
- BR-AS02 [REGRAS] Asset fornece contexto a eventos/alerts (enrichment).
- BR-AS03 [REGRAS] Criticality e tags livres (valores validados).

## 7. Usuários e auditoria

- BR-U01 [CRÍTICA] Toda ação de usuário importante gera Audit.
- BR-U02 [CRÍTICA] RBAC mínimo: analyst (opera) / admin (configura, gerencia usuários).
- BR-U03 [REGRAS] Credenciais nunca em log/payload (secrets proibidos).

## 8. Health e operação

- BR-H01 [CRÍTICA] Health reporta estado por componente (online/degraded/offline).
- BR-H02 [REGRAS] Componente degradado não derruba pipeline (graceful).
- BR-H03 [REGRAS] Métricas simples por etapa (contadores) para diagnóstico.

## 9. API

- BR-P01 [CRÍTICA] Erros retornam `code` estável + `message` + `trace_id`.
- BR-P02 [REGRAS] Versionamento `/api/v1`; mudança quebradora → v2.
- BR-P03 [REGRAS] POSTs críticos aceitam `Idempotency-Key`.
- BR-P04 [REGRAS] Rate limiting em toda rota.

## 10. Qualidade

- BR-Q01 [CRÍTICA] Cobertura ≥ 85% (críticos ≥ 90%); sem testes artificiais.
- BR-Q02 [CRÍTICA] mypy strict 0 issues; ruff limpo.
- BR-Q03 [REGRAS] Critério "daqui a um ano" em toda decisão.
- BR-Q04 [REGRAS] Nada de código sem contrato/documentação.

---

## Resumo por prioridade

- **Críticas:** imutabilidade do evento, append-only, regras declarativas, dedupe,
  transições validadas, audit, RBAC, idempotência, MITRE/severity obrigatórios.
- **Regras:** confirmação de ações em lote, soft-disable, notas auditadas, UNIQUEs.
- **UX:** 4 perguntas por tela, 1 botão primário, feedback em toda ação.
- **Futuro:** UEBA, threat intel online, playbooks de automação.
