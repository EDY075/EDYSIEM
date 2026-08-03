# EDY SIEM — Wireframes

> Wireframes textuais (ASCII) de todas as telas. Guia visual para a implementação.
> Sem HTML/CSS — apenas documentação. Segue `UX_ARCHITECTURE.md` e `SCREEN_MAP.md`.

---

## W1 — Shell (Sidebar + Topbar)

```
┌──────────────────────────────────────────────────────────────────────┐
│ ◧ EDY SIEM          🔍 Buscar...            [⏻] [🛎] [👤 Analista] │
├────────────┬─────────────────────────────────────────────────────────┤
│ OPERAÇÕES  │                                                         │
│  ▸ Overview│                                                         │
│  ▸ Events  │                                                         │
│  ▸ Alerts  │                     [CONTEÚDO DA PÁGINA]                │
│  ▸ Incidents│                                                        │
│  ▸ Hunting │                                                         │
│ SISTEMA    │                                                         │
│  ▸ Rules   │                                                         │
│  ▸ Intel   │                                                         │
│  ▸ Assets  │                                                         │
│  ▸ Settings│                                                         │
│────────────│                                                         │
│ ● API ● DB │                                                         │
│ ● Anz ● v  │                                                         │
└────────────┴─────────────────────────────────────────────────────────┘
```

---

## W2 — Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│ Dashboard — Resumo operacional                [1h] [24h] [7d] [30d]  │
├──────────────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐         │
│ │ Críticos│ │ Altos   │ │ Médios  │ │ Total   │ │ Incid.  │         │
│ │  3  ██  │ │ 12  ████│ │ 45  ████│ │ 120 ████│ │ 2  ███  │         │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘         │
│ ┌───────────────────────────┐ ┌───────────────────────────┐          │
│ │ Tendência 24h (chart)     │ │ Alertas críticos          │          │
│ │ ▁▂▃▄▅▆▇█▆▅▄▃            │ │ • alt_… web-01 brute      │          │
│ │                           │ │ • alt_… vpn-02 anomaly    │          │
│ └───────────────────────────┘ └───────────────────────────┘          │
│ ┌───────────────────────────┐ ┌───────────────────────────┐          │
│ │ Timeline recente          │ │ Estado componentes        │          │
│ │ ● alt_… 14:02 high        │ │ ● API ● DB ● Engines      │          │
│ │ ● evt_… 14:01 web-01      │ │ ● Collectors              │          │
│ └───────────────────────────┘ └───────────────────────────┘          │
└──────────────────────────────────────────────────────────────────────┘
```

**KPI clicável → `/alerts?severity=critical&since=24h`.**

---

## W3 — Alerts (tela principal + drawer)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Alert Center                              [⬆ Atualizar] [⇅ Exportar] │
├──────────────────────────────────────────────────────────────────────┤
│ [🔍 Buscar...] [Sev ▾] [Status ▾] [Fonte ▾] [Período ▾] [Limpar]     │
│ 248 alertas encontrados                                               │
│ ┌────────────────────────────────────────────────────────────────┐   │
│ │ ☑ Sev   Status  Título            Host   User   Última   ⚙     │   │
│ │ ☐ HIGH  NEW     Brute force web-01 admin  14:02   ⋮        │   │
│ │ ☐ CRIT  TRIAGE  Anomalia vpn-02   vpn02  -      14:01   ⋮     │   │
│ │ ☐ MED   OPEN    Scan portas ...   dmz01  -      13:58   ⋮     │   │
│ └────────────────────────────────────────────────────────────────┘   │
│ [☑ 2 selecionados: ACK | Resolve | Suppress]   [1-25 de 248]         │
└──────────────────────────────────────────────────────────────────────┘

──────────── Drawer de Alerta (direita) ────────────────
┌──────────────────────────────┐
│ [HIGH] Brute force web-01     │  ← o quê + badge
│ Host: web-01 · User: admin    │  ← impacto
│ Risco: alto · MITRE T1110     │
│──────────────────────────────│
│ [Resumo] [Evidências] [Timeline] [Relacionados]   ← abas
│ 24 falhas de login em 5min    │
│ (últimas evidências com mono) │
│──────────────────────────────│
│ [Resolve] [ACK] [→ Incidente] │  ← o que fazer (1 primário)
└──────────────────────────────┘
```

---

## W4 — Incidents (workspace)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Incidents                              [Status ▾] [Severidade ▾]     │
├──────────────────────────────────────────────────────────────────────┤
│ Título            Sev    Entidades    Alerts  Status   Atualizado    │
│ Brute force web-01 HIGH  web-01/admin  24     INVESTIGATING  14:05  │
│ Anomalia vpn-02   CRIT  vpn-02        -      OPEN          14:01    │
└──────────────────────────────────────────────────────────────────────┘

──────────── Workspace de Incidente ────────────────
┌────────────────────────────────────────────┐
│ INC-002 Brute force web-01   [INVESTIGATING]│
│ Host: web-01 · User: admin · MITRE T1110    │
│────────────────────────────────────────────│
│ Timeline de ações                           │
│ 14:00 alerta criado                         │
│ 14:03 investigação iniciada (analista)      │
│ 14:05 nota: origem ip 10.0.0.5              │
│────────────────────────────────────────────│
│ Notas: [escrever...] [Enviar]               │
│────────────────────────────────────────────│
│ [Exportar JSON/MD] [Mudar status ▾]         │
└────────────────────────────────────────────┘
```

---

## W5 — Rules (form + teste)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Rules                        [Nova Regra]                           │
├──────────────────────────────────────────────────────────────────────┤
│ Nome           Sev    MITRE          Enabled  Versão                 │
│ Brute force    HIGH   T1110          ●        1                      │
│ Scan ports     MED    T1046          ●        1                      │
└──────────────────────────────────────────────────────────────────────┘

──────────── Modal: Nova Regra ────────────────
┌──────────────────────────────────────────┐
│ Nova Detection Rule                       │
│ Nome: [________________________]          │
│ Severidade: [HIGH ▾]  MITRE: [T1110 ▾]   │
│ Condição: [________________________]      │
│ Timeframe (s): [300]                      │
│ [Testar]  [Cancelar]  [Salvar]            │
│ ── Resultado do teste: 24 alertas ──      │
└──────────────────────────────────────────┘
```

---

## W6 — Events (busca + drawer)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Events   [⏱ query language... ] [Datas ▾] [Fonte ▾] [Executar]      │
├──────────────────────────────────────────────────────────────────────┤
│ Hora      Fonte    Host    Tipo       User   IP src    Sev            │
│ 14:02:11  syslog   web-01  auth.fail  admin  10.0.0.5  HIGH           │
│ 14:02:10  syslog   web-01  auth.fail  admin  10.0.0.5  HIGH           │
└──────────────────────────────────────────────────────────────────────┘

──────────── Drawer de Evento ────────────────
┌──────────────────────────────────────────┐
│ evt_… 14:02:11 auth.fail [HIGH]           │
│ Host: web-01 · User: admin · IP 10.0.0.5  │
│──────────────────────────────────────────│
│ Campos canônicos (mono)                   │
│──────────────────────────────────────────│
│ Raw (original, colapsável)                │
│──────────────────────────────────────────│
│ Enriquecimento: asset/geo/intel           │
│ [Ver alertas deste host]                  │
└──────────────────────────────────────────┘
```

---

## W7 — Intelligence (IOCs)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Intelligence   [Importar IOCs]    [🔍 Buscar]                        │
├──────────────────────────────────────────────────────────────────────┤
│ Tipo     Valor           Fonte     Ameaça      Criado   ⚙             │
│ IP       10.0.0.5        feed-x    botnet      02/08    ⋮            │
│ Hash     a1b2…          manual    malware     02/08    ⋮            │
│ Domain   evil.example   feed-y    phishing    01/08    ⋮            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## W8 — Hunting

```
┌──────────────────────────────────────────────────────────────────────┐
│ Hunting   [Técnica MITRE ▾] [Executar]                              │
├──────────────────────────────────────────────────────────────────────┤
│ Técnica: T1110 — Brute Force (query sugerida pré-preenchida)         │
│ Timeline de resultados (gráfico + tabela)                            │
│ ┌──────────────────────────────────────────────┐                     │
│ │ Entidade        Eventos  Janela    Ação       │                     │
│ │ 10.0.0.5 → web-01 24      5min     [Promover] │                     │
│ └──────────────────────────────────────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Regras de wireframe

- Todo drawer fecha com ESC/X e preserva a lista.
- Todo KPI/badge é clicável (drill-down filtrado).
- Um botão primário por view (ação recomendada).
- Estados vazios indicam próxima ação.
- Mono para dados técnicos (IDs, hashes, IPs, timestamps).
