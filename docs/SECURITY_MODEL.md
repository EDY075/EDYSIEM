# EDY SIEM — Security Model

> Modelo de segurança da própria plataforma. Como protegemos o SIEM.

## 1. Princípios

- **Segurança por padrão**: headers seguros, inputs validados, zero secrets em código.
- **Menor privilégio**: funções de usuário (analyst/admin).
- **Auditoria**: toda ação relevante vai para `audit_log`.
- **API protegida**: autenticação e autorização desde a v1 (não adicionar depois).

## 2. Controles

### HTTP
- Headers: `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy`.
- `Cache-Control: no-store` em respostas sensíveis.
- Server header ofuscado.

### API
- Autenticação: token (API key) com escopo; futuramente OAuth.
- Rate limiting por token/IP (anti-abuso).
- Payload limitado (1 MB padrão) com validação de schema.

### Input
- Toda entrada validada por schema (dataclasses/pydantic-like — decisão na Sprint 1).
- Sem `eval`/`exec`; regras são declarativas (ver ADR-004).

### Persistência
- SQL parametrizado em toda consulta (zero SQL concat).
- Secrets/credenciais fora do repo (env vars, .env ignorado).

### UI
- Escape de dados em todo render (XSS).
- CSP restritiva; sem inline scripts desnecessários.

## 3. Modelo de ameaças à plataforma (resumo)

Ver `THREAT_MODEL.md` para análise detalhada (STRIDE por componente).
Principais riscos: injeção de eventos malformados, DoS via ingestão,
acesso não autorizado à API, XSS no dashboard, exfiltração de dados sensíveis.
