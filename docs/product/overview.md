# EDY SIEM — Product Vision

> Documento de visão do produto. Define **o quê**, **para quem** e **por que** o EDY SIEM existe.
> Este documento não descreve implementação — descreve intenção.

## 1. O que é o EDY SIEM

O EDY SIEM é uma plataforma profissional de **Security Information and Event Management (SIEM)**
desenvolvida para demonstrar e aplicar conhecimento de engenharia em:

- Blue Team / SOC
- Threat Intelligence
- Incident Response
- Log Management
- Correlation Engine
- Detection Engineering
- Software Engineering

É inspirada nos conceitos de produtos como Microsoft Sentinel, Splunk Enterprise Security,
Elastic Security e IBM QRadar, **porém com identidade própria**. O objetivo não é copiar
nenhuma ferramenta — é construir uma arquitetura sólida, moderna, sustentável e organizada.

## 2. Para quem

- **Analistas de SOC** — precisam de triagem rápida, contexto e resposta.
- **Engenheiros de detecção** — precisam criar e manter detection rules.
- **Estudantes de cibersegurança** — precisam de um playground didático e profissional.
- **Recrutadores de Blue Team** — precisam ver engenharia de verdade.

## 3. Problema que resolve

Times pequenos e profissionais em formação carecem de uma plataforma SIEM que seja:

- **Autônoma** — sem nuvem obrigatória, sem licença, sem agentes proprietários.
- **Didática** — cada módulo ensina um conceito real de SIEM.
- **Extensível** — plugins e connectors com contratos claros.
- **Bem arquitetada** — pronta para evoluir por anos sem retrabalho.

## 4. Experiência alvo

Cada tela da interface deve responder imediatamente:

| Pergunta | Resposta esperada |
|---|---|
| O que aconteceu? | Evento/alerta com descrição e severidade |
| Onde aconteceu? | Host, source, entidade afetada |
| Qual o risco? | Score de risco e MITRE ATT&CK |
| Quem está envolvido? | Usuário, processo, IP, asset |
| Qual ação devo tomar? | Ações de triagem, resposta e investigação |

Nenhuma tela existe apenas por estética. **Tudo tem propósito operacional.**

## 5. Não-objetivos (v1)

- Não é um EDR (não instala agentes de endpoint avançados).
- Não é um SOAR completo (automação de resposta será incremental).
- Não substitui SIEMs corporativos — é uma plataforma de estudo e operação leve.
- Não faz coleta de telemetria host profunda (isso é escopo futuro).

## 6. Princípios do produto

- **Qualidade de arquitetura antes de velocidade** (Regra Nº 1).
- Clean Architecture, SOLID, KISS, DRY, YAGNI.
- Baixo acoplamento, alta coesão, responsabilidade única.
- Zero gambiarra, zero código duplicado, zero dependências desnecessárias.
- Documentação impecável e código autodocumentado.
- Aparência de produto Enterprise — nunca de projeto de faculdade.

## 7. Sucesso na v1

- Ingestão de eventos de múltiplas fontes (syslog, Windows Event, Linux logs).
- Normalização para um modelo de evento único.
- Correlation Engine com regras configuráveis.
- Detection Rules com mapeamento MITRE ATT&CK.
- Dashboard SOC operacional com contexto por alerta.
- REST API e CLI completos.
- Documentação de nível Enterprise (guia de estudo incluído).
