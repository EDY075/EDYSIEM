# EDY SIEM — Security Model

> Modelo de segurança da própria plataforma. Como protegemos o SIEM.

## 1. Princípios

- **Segurança por padrão**: headers seguros, inputs validados, zero secrets em código.
- **Menor privilégio**: funções de usuário (`viewer`, `analyst`, `admin`).
- **Auditoria**: toda mutação da API vai para `audit_entries` com identidade e resultado.
  Por padrão, a trilha usa `edysiem.audit.db`, isolando contenção do banco operacional;
  `EDYSIEM_AUDIT_DB` permite definir outro caminho protegido.
- **API protegida**: autenticação e autorização desde a v1 (não adicionar depois).

## 2. Controles

### API
- Autenticação fail-closed: `EDYSIEM_API_KEY`, `EDYSIEM_API_IDENTITY` e
  `EDYSIEM_API_ROLE` são obrigatórios para rotas protegidas.
- O papel é vinculado à chave no servidor. `X-EDY-Role` é ignorado e nunca concede acesso.
- `/health` e `/version` são públicos. A ingestão EDY Shield usa seu próprio token M2M.
- Rate limiting por token/IP (anti-abuso).
- Payload limitado (1 MB padrão) com validação de schema.
- Toda rota mutável exige uma permissão explícita e gera registro append-only de auditoria.

### Input
- Toda entrada validada por schema (dataclasses/pydantic-like — decisão na Sprint 1).
- Sem `eval`/`exec`; regras são declarativas (ver ADR-004).

### Persistência
- Valores SQL são parametrizados; nomes dinâmicos de coluna usam allowlist por repositório.
- Secrets/credenciais fora do repo (env vars, .env ignorado).

### UI
- Escape de dados em todo render (XSS).
- A chave é informada pelo operador e mantida apenas em `sessionStorage`; não entra no bundle.
- O Vite e a API escutam somente em loopback. A versão 0.3.0 não oferece modo LAN;
  os binds e as portas não devem ser publicados.

### Pendências de hardening HTTP

- CSP, HSTS, `nosniff`, proteção de frame e Trusted Host devem ser definidos pelo
  reverse proxy antes de uma implantação pública. O runner de desenvolvimento não
  representa um deployment de Internet.

## 3. Modelo de ameaças à plataforma (resumo)

Ver `THREAT_MODEL.md` para análise detalhada (STRIDE por componente).
Principais riscos: injeção de eventos malformados, DoS via ingestão,
acesso não autorizado à API, XSS no dashboard, exfiltração de dados sensíveis.
