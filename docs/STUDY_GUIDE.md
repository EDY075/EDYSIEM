# EDY SIEM — Study Guide (O que é SIEM)

> Guia didático. Cada conceito tem uma explicação simples e a relação com o módulo
> correspondente no EDY SIEM. Objetivo: aprender construindo.

## 1. O que é um SIEM

**SIEM** = Security Information and Event Management.
Combina **SIM** (coleta e armazenamento de logs para análise) com **SEM** (correlação e
alerta em tempo real). É o "painel de controle" do SOC: concentra eventos, encontra
padrões suspeitos e dá contexto para resposta.

## 2. Como funciona (visão geral)

```
Eventos acontecem -> são coletados -> normalizados -> enriquecidos
-> correlacionados -> detectados como alertas -> viram incidentes -> investigados
```

O EDY SIEM implementa exatamente esse fluxo (ver `ARCHITECTURE.md`).

## 3. Como um evento percorre o sistema

1. **Coleta** (`collectors`): syslog/arquivo/API emitem eventos brutos.
2. **Normalização** (`normalization`): transforma formatos diferentes no mesmo modelo.
3. **Enriquecimento** (`enrichment`): adiciona contexto (asset, geo, intel).
4. **Correlação** (`correlation`): junta eventos relacionados (mesmo host, janela, padrão).
5. **Detecção** (`detection`): regras geram alertas com severidade e MITRE.
6. **Incidente** (`incident`): alertas viram incidentes gerenciáveis.
7. **Persistência** → **API/UI/CLI**.

## 4. Como ocorre a correlação

Correlação compara eventos por **identidade** (host, usuário, IP) dentro de uma **janela
temporal** e aplica **agregações** (ex.: 5 falhas de login em 60s). O resultado é um evento
correlacionado que alimenta a detecção. No EDY SIEM: `correlation` + regras YAML (ADR-004).

## 5. Como funciona um SOC

- **Monitorar** (coletar e observar).
- **Detectar** (alertas e regras).
- **Triar** (o que é real? qual o risco?).
- **Investigar** (contexto, evidências, timeline).
- **Responder** (conter, erradicar, recuperar).
- **Documentar** (post-mortem, lições).

O EDY SIEM dá suporte a todo esse ciclo.

## 6. Conceitos-chave

### MITRE ATT&CK
Framework de táticas e técnicas de adversários. No EDY SIEM, cada detection rule é mapeada
a `tactic`/`technique` (ex.: T1110 — Brute Force). Isso padroniza a linguagem de detecção.

### IOC (Indicators of Compromise)
Evidências observáveis de comprometimento: IP, domínio, URL, hash, e-mail.
O módulo `iocs` permite cadastrar e enriquecer eventos com intel.

### Logs
- **Syslog**: protocolo padrão de logs (RFC 3164/5424).
- **Windows Event**: logs do Windows (Security, System, Application).
- **Linux logs**: auth.log, syslog, journald, etc.
No EDY SIEM: `collectors` + parsers de `normalization`.

### Detecção
Transformar eventos em alertas por regras declarativas (ADR-004).
Engenharia de detecção = criar regras precisas com poucos falsos positivos.

### Threat Hunting
Busca proativa por ameaças **antes** da detecção automática, com hipóteses e consultas.

### Incident Response
Processo de resposta: preparação, detecção, contenção, erradicação, recuperação, lições.

## 7. Trilha de aprendizado no código

1. Leia `PRODUCT_VISION.md` e `ARCHITECTURE.md`.
2. Siga o fluxo de um evento no `SYSTEM_DESIGN.md`.
3. Explore cada módulo `app/` na ordem do pipeline.
4. Rode os exemplos em `examples/events/`.
5. Estude as regras em `config/rules/` e teste-as.
