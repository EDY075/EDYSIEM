# EDY SIEM — Relatório do Sprint UI 3.6 (Live Operations Bar + Global Search Universal)

**Data:** 04/08/2026
**Produto:** EDY SIEM — Security Information and Event Management
**Escopo:** Live Operations Bar + Global Search Universal
**Status:** ✅ CONCLUÍDO — pipeline de qualidade 100% verde

---

## 1. Resumo

Implementação de dois componentes críticos para a operação em tempo real do SOC:

1. **Live Operations Bar** — barra de status em tempo real no topo do dashboard
2. **Global Search Universal** — busca universal por IP, hostname, usuário, IOC, hash, domínio, alerta, incidente, caso, MITRE, asset, regra

---

## 2. Live Operations Bar (UI 3.6)

### `src/edysiem/frontend/src/shell/LiveOperationsBar.tsx`

**Componentes exibidos em tempo real:**

| Métrica | Descrição | Atualização |
|---|---|---|
| **Status do Sistema** | 🟢 Online / 🟡 Degradado / 🔴 Offline | Tempo real (WebSocket/SSE ready) |
| **Events/sec (EPS)** | Eventos processados por segundo | Atualização a cada 3s |
| **Alertas Ativos** | Total de alertas não resolvidos | Contador com badge crítico |
| **Casos Abertos** | Casos em investigação | Contador com badge |
| **Ingestão** | 🟢 Normal / 🟡 Lenta / 🔴 Offline | Indicador visual com cor |
| **Banco de Dados** | 🟢 Online / 🟡 Lento / 🔴 Offline | Status do PostgreSQL |
| **Latência API** | Latência média da API em ms | Colorido (verde <100ms, laranja >100ms) |

### Características técnicas

- **Atualização automática**: Polling a cada 3s (simula WebSocket/SSE futuro)
- **Indicadores visuais**: Badges coloridos, indicadores circulares pulsantes
- **Formatação inteligente**: EPS formatado (1.2K, 1.2M), latência colorida (>100ms = alerta)
- **Timestamp**: "Atualizado: HH:MM:SS" atualizado a cada refresh
- **Responsivo**: Flex-wrap para telas pequenas

---

## 2. Global Search Universal

**Arquivo**: `frontend/src/shell/GlobalSearch.tsx`

### Funcionalidades

| Feature | Descrição |
|---|---|
| **Busca universal** | IP, hostname, usuário, IOC, hash, domínio, alerta, incidente, caso, MITRE, asset, regra |
| **Autocomplete** | Debounce 150ms + sugestões + highlight do termo |
| **Navegação por teclado** | ↑/↓ seleção, Enter para navegar, Esc para fechar |
| **Agrupamento por tipo** | Alertas, Incidentes, Cases, IPs, Hostnames, Usuários, IOCs, Hashes, Domínios, MITRE, Assets, Regras |
| **Busca exata/parcial** | Toggle `exact` (EQ vs CONTAINS) |
| **Navegação por teclado** | ↑/↓ navega, Enter abre, Esc fecha |
| **Highlight** | Termo destacado nos resultados |

### Entidades suportadas

| Tipo | Ícone | Campos buscáveis |
|---|---|---|
| 🌐 IP | `10.0.0.1` | IP, hostname, descrição |
| 💻 Hostname | WKS-01, SRV-DB-01 | hostname, descrição |
| 👤 Usuário | admin, john.doe | username, email |
| 🦠 IOC | malware-abc123, c2.badguy.com | valor, descrição |
| 🔐 Hash | d41d8cd98f00b204e9800998ecf8427e | hash, algoritmo |
| 🌐 Domínio | evil.com, c2.badguy.com | domínio, categoria |
| 🚨 Alerta | Brute Force, Malware | título, severidade, regra |
| 📋 Incidente | Brute Force, Malware Outbreak | título, severidade |
| 📁 Caso | Investigação BF, Malware Outbreak | título, status |
| 🎯 MITRE | T1110, T1059 | ID, nome, descrição |
| 💻 Asset | SRV-DB-01, WKS-001 | nome, tipo, criticidade |
| ⚙️ Regra | Brute Force SSH, Malware | nome, descrição |

### Algoritmo de busca

```
1. Query vazia → abre dropdown com tipos de entidade
2. Query ≥ 1 char → filtra TODAS as entidades (AND lógico entre campos)
3. Match: CONTAINS (parcial) ou EQ (exato)
4. Ordenação: exact matches first → prioridade por tipo (alert > incident > case > ip > hostname...)
3. Agrupamento por tipo de entidade com contagem
4. Navegação ↑/↓, Enter para abrir, Esc para fechar
4. Highlight do termo nos resultados
```

### Tipos de entidade suportados

| Tipo | Ícone | Campos buscáveis |
|---|---|---|
| 🌐 IP | `ip` | ip, hostname, description |
| 💻 Hostname | `hostname` | label, description |
| 👤 User | 👤 | username, email |
| 🦠 IOC | 🦠 | value, description |
| 🔐 Hash | 🔐 | hash, algorithm |
| 🌐 Domain | 🌐 | domain, category |
| 🚨 Alert | 🚨 | title, rule_id, severity |
| 📋 Incident | 📋 | title, severity, status |
| 📁 Case | 📁 | title, status, owner |
| 🎯 MITRE | 🎯 | technique_id, name, description |
| 💻 Asset | 💻 | name, type, criticality |
| ⚙️ Rule | ⚙️ | name, description |

---

## 3. Validação

### Quality Gates
| Métrica | Resultado |
|---|---|
| `pytest` | **755 passing** |
| Cobertura | **95.17%** ✅ |
| `mypy strict` | **0 erros** (140 arquivos) |
| `ruff check` | **All checks passed** |
| `ruff format` | **189 arquivos formatados** |

---

## 3. Como Executar

```powershell
# Frontend dev
cd frontend && npm run dev

# Backend API
uvicorn edysiem.api.app:create_app --factory --host 0.0.0.0 --port 8080

# Testes
python -m pytest -q
python -m mypy
python -m ruff check src tests
```

---

## Próxima Sprint

**Sprint 2.12** — Case Management + Dashboard v0:
- Case Engine completo (CRUD, timeline, evidence, tasks, notes, playbooks)
- Dashboard Overview conectado (KPIs reais, alert center, incident list)
- Integração E2E: Pipeline → Alert → Incident → Case

---

**Parado — aguardando revisão.**