# EDY SIEM — Glossário

> Termos do projeto e do domínio de SIEM/SOC. Linguagem ubíqua — usar estes termos
> consistentemente em código, docs e comunicação.

## A–C
| Termo | Definição |
|---|---|
| **Alert** | Resultado de uma detecção; o que aconteceu, impacto, MITRE, evidências. |
| **Asset** | Ativo monitorado (hostname/IP) com criticalidade e tags. |
| **ATT&CK (MITRE)** | Framework de táticas e técnicas de adversários. |
| **Audit** | Trilha de auditoria de ações (quem, quando, o quê). |
| **Backpressure** | Controle de fluxo que pausa a entrada quando o pipeline está cheio. |
| **Bounded Context** | Limite de um domínio com linguagem e modelo próprios. |
| **Canonical Event** | Modelo canônico de evento normalizado. |
| **Case** | Agrupamento de alertas sob gestão (sinônimo de incidente no produto). |
| **Collector** | Conector que obtém eventos de uma fonte. |
| **Comment** | Nota com autor e hora em um case/investigação. |
| **Correlation** | Agrupamento de eventos por identidade + janela + agregação. |
| **Criticality** | Nível de importância de um asset (low→critical). |

## D–I
| Termo | Definição |
|---|---|
| **Detection** | Aplicação de regras que transformam eventos em alertas. |
| **Detection Rule** | Condição declarativa que gera alerta (severidade + MITRE). |
| **Drawer** | Painel lateral para detalhe sem perder contexto. |
| **Enrichment** | Adição de contexto (asset, geo, intel) a um evento. |
| **Entity** | Participante de um evento: host, usuário, IP, processo. |
| **Event** | Ocorrência observável de uma fonte. |
| **Evidence** | Conjunto de eventos que sustentam um alerta. |
| **Feed (IOC)** | Fonte externa de indicadores/intel. |
| **Fingerprint** | Hash determinístico para deduplicação. |
| **Incident** | Agrupamento de alertas sob resposta (case). |
| **Investigation** | Análise de um case com timeline, evidências e notas. |
| **IOC** | Indicator of Compromise — artefato observável de ameaça. |
| **IOC Feed** | Lista/fonte de IOCs importada. |

## N–R
| Termo | Definição |
|---|---|
| **Normalization** | Conversão de eventos brutos para o modelo canônico. |
| **Notification** | Aviso (email/webhook) sobre alerta/case. |
| **Parser** | Extrator de campos estruturados de um payload. |
| **Playbook** | Roteiro de ações de resposta a incidentes. |
| **Plugin** | Coletor/parser/enricher registrado via registry. |
| **Report** | Exportação (JSON/MD) de case/investigação. |
| **Risk Score** | Pontuação de risco por entidade (acumulada). |
| **Rule** | Detection ou correlation rule (declarativa). |

## S–Z
| Termo | Definição |
|---|---|
| **Severity** | Nível de impacto: info/low/medium/high/critical. |
| **SIEM** | Security Information and Event Management. |
| **SOC** | Security Operations Center. |
| **State Machine** | Modelo de estados/transições de uma entidade. |
| **Status (alert)** | OPEN/TRIAGE/INVESTIGATING/RESOLVED/FALSE_POSITIVE. |
| **Status (case)** | OPEN/INVESTIGATING/RESOLVED/FALSE_POSITIVE. |
| **Threat Hunting** | Busca proativa por ameaças antes da detecção automática. |
| **Threat Intelligence** | Conhecimento sobre ameaças (IOCs, reputação). |
| **Timeline** | Sequência cronológica de eventos/ações. |
| **Trace ID** | Identificador que atravessa o pipeline. |
| **YARA / YARA-L** | Linguagem de regras de detecção (binária / baseada em log). |
| **Sigma** | Formato aberto de regras de detecção. |
| **UEBA** | User and Entity Behavior Analytics (futuro). |
| **WAL** | Write-Ahead Log (modo de concorrência do SQLite). |
