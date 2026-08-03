# EDY SIEM — Security Checklist

> Checklist de verificação de segurança. Usado em: definição de pronto (DoD), review de
> PR, preparação de release e auditoria. Base: `SECURITY_ARCHITECTURE.md`.

## 1. Autenticação e sessão
- [ ] Senhas com hash forte (Argon2/bcrypt), nunca MD5/SHA1
- [ ] JWT com `exp` curta, assinatura verificada, `iss`/`aud` validados
- [ ] Refresh token rotacionado e revogável
- [ ] Logout invalida token/refresh
- [ ] Password policy (mín 12 chars) aplicada

## 2. Autorização (RBAC)
- [ ] Permissões atômicas por papel (analyst/admin)
- [ ] Toda rota exige permissão (403 sem permissão)
- [ ] Menor privilégio por default

## 3. Transporte e headers
- [ ] HTTPS em produção (HSTS)
- [ ] CSP restritiva (sem unsafe-inline script)
- [ ] `X-Frame-Options: DENY`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Referrer-Policy: no-referrer`
- [ ] `Permissions-Policy` restritiva

## 4. Input e injeção
- [ ] SQL 100% parametrizado (zero concat)
- [ ] Escape de saída renderizada (XSS)
- [ ] Regras declarativas validadas por schema (sem exec)
- [ ] Payloads limitados (1 MB) com validação
- [ ] Rate limiting em auth e APIs

## 5. Secrets
- [ ] Nenhum secret no repositório (.env ignorado)
- [ ] Secrets via env/secret manager
- [ ] Logs sem secrets/payloads sensíveis

## 6. Auditoria
- [ ] Ações de usuário gravadas em `audit_log` (append-only)
- [ ] Eventos de segurança logados (login ok/falha, acesso negado)
- [ ] `trace_id` em logs de pipeline

## 7. Backup e recovery
- [ ] Backup criptografado + retenção
- [ ] Procedimento de restore documentado e testado
- [ ] Health check pós-restore

## 8. Dependências
- [ ] Audit de dependências sem vulnerabilidades conhecidas
- [ ] Zero dependência desnecessária (YAGNI)

## 9. OWASP Top 10
- [ ] A01–A10 mapeados e cobertos (ver SECURITY_ARCHITECTURE §22)

## 10. Release gate
- [ ] Checklist executado e assinado (data/revisão)
