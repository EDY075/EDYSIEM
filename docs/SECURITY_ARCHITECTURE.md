# EDY SIEM — Security Architecture

> Arquitetura de segurança do produto, definida por design (Security by Design).
> Segurança não é feature — é requisito base. Fundamento: `SECURITY_MODEL.md` + `THREAT_MODEL.md`.

---

## 1. Princípios

- **Segurança por padrão**: configurações seguras por default.
- **Menor privilégio**: papel mínimo necessário.
- **Defesa em profundidade**: múltiplas camadas.
- **Fail safe**: falha fecha acesso, nunca abre.
- **Nunca confiar em input**: validação em toda fronteira.
- **Auditabilidade**: toda ação relevante registrada.
- **Secrets nunca no código**: apenas via env/secret manager.

---

## 2. Autenticação

### 2.1 Modelo
- **JWT** (access token) para API/UI (stateless).
- **Refresh token** (armazenado, revogável) para renovação.
- Credenciais: username/email + password (hash).
- Futuro: OAuth2 / SSO (ADR quando implementar).

### 2.2 Fluxo
1. `POST /api/v1/auth/login` → valida credencial → emite access token (curto) + refresh token.
2. Cliente envia `Authorization: Bearer <access>`.
3. Access token curto (ex.: 15 min); refresh rotacionado.
4. Logout revoga refresh (blacklist).

### 2.3 Validação de token
- Assinatura verificada (HMAC/RS256).
- `exp`, `nbf`, `iss`, `aud` verificados.
- Rejeição em cache de revogação.

---

## 3. RBAC e Permissões

### 3.1 Papéis (v1)

| Papel | Capacidade |
|---|---|
| `admin` | Tudo + gestão de usuários, regras, configuração |
| `analyst` | Operar: triagem, investigação, incidentes, iocs, coleta |

### 3.2 Modelo de permissão

Permissões atômicas agrupadas em papéis:

```text
alert.read, alert.ack, alert.resolve, alert.associate
case.read, case.update, case.close
rule.read, rule.create, rule.update, rule.disable
ioc.read, ioc.create, ioc.import
user.read, user.manage (admin)
config.read, config.manage (admin)
report.export
```

- Papel = conjunto de permissões.
- Toda rota exige permissão (decorator/middleware de autorização).
- Falta de permissão → 403.

---

## 4. Sessões

- JWT para API; sessão de UI no mesmo token (Authorization header).
- Sem cookie `JSESSIONID` sensíveis; se cookie, flags seguras.
- **Logout** invalida refresh.
- **Idle timeout** e **absolute timeout** configuráveis.

---

## 5. CSRF (Cross-Site Request Forgery)

- API usa **Bearer token** (não depende de cookie → mitigação forte).
- Se usar cookie de sessão em UI: **CSRF token** + `SameSite=Strict`.
- Métodos mutáveis exigem token/confirmação.
- Verificação de `Content-Type: application/json` em POSTs.

---

## 6. CSP (Content Security Policy)

```text
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';   # tokens inline (avaliar remover)
img-src 'self' data:;
connect-src 'self';
font-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

- **Sem** `'unsafe-inline'` em script (XSS local mitigado).
- Header enviado em todas as respostas HTML.

---

## 7. XSS

- **Escape** de toda saída renderizada (framework/escape).
- **Nunca** `innerHTML` com dados não escapados.
- CSP restritiva como defesa em profundidade.
- **Sanitização** de entrada na fronteira (validação de schema).
- Inputs de regras/IOCs escapados na UI.

---

## 8. SQL Injection

- **Parametrização obrigatória** em toda query (zero SQL concat).
- Regras declarativas validadas por schema (sem execução arbitrária) → previne injeção por regra.
- `q` de busca sanitizada/quoted corretamente.

---

## 9. Secrets

- **Nunca** secrets no repositório (`.env` ignorado).
- Variáveis de ambiente / secret manager.
- Rota de regras/parsers não executa código arbitrário (evita exfiltração por plugin).
- Logs nunca contêm secrets/payloads sensíveis.

---

## 10. JWT

- Algoritmo seguro (RS256 preferido; HS256 com segredo forte).
- Payload mínimo (sub, role, exp, iat, jti).
- `exp` curta para access.
- Chave de assinatura gerenciada; rotação possível (kid).

---

## 11. API Keys

- Para automação/CLI (em vez de usuário interativo).
- Geradas com hash (armazenamento) — nunca em claro.
- Escopo: papéis/permissões limitadas.
- Revogáveis; rotação; limite por chave.

---

## 12. Rate Limit

- Por IP e por API key/token.
- Estratégia: token bucket (sliding window).
- Defaults:
  - Auth: ___/min (anti brute force).
  - GET: ___/min.
  - POST: ___/min.
- Resposta: `429` + `Retry-After`.
- Protege ingestão e busca de DoS.

---

## 13. Password Policy

- Mínimo 12 chars; recomendado 16.
- Mix: maiúscula, minúscula, dígito, símbolo (incentivado, não obrigatório exclusivo).
- Hash: **Argon2** (preferido) ou bcrypt (salt).
- Proibido: hash MD5/SHA1 de senha.
- MFA disponível para admin (futuro).
- Reset com token de uso único expirável.

---

## 14. Audit Trail

- Toda ação de usuário importante → `audit_log` (ver DATABASE_DESIGN).
- Campos: `actor, action, target, details, trace_id, created_at, ip`.
- Audit é **append-only** e protegido (só admin lê/exporta, ninguém edita/apaga).
- Eventos de segurança (login ok/falha, acesso negado) → Security Log.

---

## 15. Encryption

- **Em trânsito**: HTTPS/TLS obrigatório (produção); HTTP apenas local/dev.
- **Em repouso**: dados sensíveis (secrets, tokens) hasheados com Argon2/bcrypt.
- Payloads de eventos: TLS em trânsito; em repouso no SQLite (futuro: criptografia de coluna).
- Backups: criptografia em repouso.

---

## 16. Key Rotation

- JWT signing key: rotação programada (kid para versionar).
- API keys: rotação individual.
- Refresh tokens: rotação a cada uso (reuse detection).
- Secret de DB/smtp: rotação com planjob.

---

## 17. Backup

- Backups do SQLite (WAL + checkpoint).
- Estratégia: backups regulares (daily) + retenção.
- Backup **criptografado**.
- Restore testado periodicamente (equote).
- Recovery point: eventos append-only permitem replay parcial.

---

## 18. Resumo de headers HTTP

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains  (HTTPS)
Content-Security-Policy: (ver §6)
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: no-referrer
Permissions-Policy: geolocation=(), microphone=(), camera=()
Cache-Control: no-store (respostas sensíveis)
```

---

## 19. Implementação (faseamento)

| Fase | Controle | Sprint |
|---|---|---|
| V1 | Tipagem/hash, JWT, RBAC básico, rate limit, headers, audit, parametrização | 1–3 |
| V1 | Password policy, API keys, logout/revogação | 2–3 |
| V2 | OAuth2/SSO, MFA | futura |
| V2 | Encryption de coluna, key rotation automatizada | futura |

---

## 20. Recovery (continuidade)

- **RPO**: eventos append-only permitem replay parcial; janela de perda configurável.
- **RTO**: procedimento de restore validado e documentado (teste periódico).
- Restore: banco + migrações + verificação de health/integridade.
- Recovery de identidade: chaves de assinatura restauradas do secret manager.
- Post-restore: health check automático + validação de contagem/últimos eventos.

## 21. Threat Model (resumo)

Ver `THREAT_MODEL.md` para STRIDE completo. Prioridades:

| Ameaça | Mitigação |
|---|---|
| Injeção de eventos falsos | Whitelist de fontes + validação de schema |
| DoS na ingestão | Backpressure + rate limit + filas limitadas |
| Acesso não autorizado | JWT + RBAC + rate limit |
| Roubo de token | exp curta + rotação + revogação |
| XSS | Escape + CSP restritiva |
| SQL Injection | Parametrização obrigatória |
| Exfiltração via regra | Regras declarativas (sem exec) + plugins isolados |
| Secrets vazando | Env/secret manager; logs sem secrets |

## 22. OWASP Top 10 (mapeamento)

| OWASP | Controle no EDY SIEM |
|---|---|
| A01 Broken Access Control | RBAC por permissão em toda rota |
| A02 Cryptographic Failures | Argon2/bcrypt, TLS, headers |
| A03 Injection | SQL parametrizado; regras declarativas |
| A04 Insecure Design | Security by design desde a fundação |
| A05 Security Misconfiguration | Config segura por default; headers |
| A06 Vulnerable Components | Audit de dependências |
| A07 Identification/Auth Failures | JWT + password policy + rate limit |
| A08 Integrity Failures | Assinatura de token + validação de schema |
| A09 Logging/Monitoring | Audit trail + logging estruturado |
| A10 SSRF | Allow-list em coletores/feeds |