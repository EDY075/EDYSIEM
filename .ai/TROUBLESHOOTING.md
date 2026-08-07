# TROUBLESHOOTING.md — Problemas conhecidos e soluções

> Amigável para agentes. Cobre os incidentes freqüentes ao rodar o EDY SIEM.

## Backend / subida
| Sintoma | Causa / solução |
|---|---|
| `Port 8080 already in use` | Encerre o processo antigo: `Get-NetTCPConnection -LocalPort 8080` → pegue o `OwningProcess` e `Stop-Process`. |
| Backend não responde (frontend sem dados) | Verifique `http://127.0.0.1:8080/docs`. Se não abrir, o Vite não terá proxy de dados. |
| Frontend abre vazio | Confirme que backend está online; o Vite faz proxy `/api` → `:8080`. |
| `node/npm` não encontrado | Instale Node.js 18+ (https://nodejs.org). |
| POST retorna 422 via curl | Não passe JSON inline (aspas são removidas). Use Swagger `/docs`, Python `requests`, ou `curl --data-binary @arquivo.json`. |
| Seed dá 500 no `/soc/pipeline/demo` | Provável dado já existente (idempotência) ou estado do banco; não é bloqueante — rules/iocs/assets se populam separadamente. |

## Dados
- **Reset de dados:** o banco dev fica em `instance/edysiem.db`. Remova o arquivo para recomeçar.
- **Seed repetido:** é idempotente — alertas/incidentes são reutilizados por *fingerprint*; case existente é preservado. Use `--no-seed` só se quiser começar sem demo.
- **Demonstração para screenshots:** use o seed dos endpoints `/soc/rules|iocs|assets` + `/soc/pipeline/demo` (o `demo` pode retornar 500 por idempotência; os demais populam as telas).

## Qualidade / CI
- **pytest falha por coverage < 95%:** o gate está em `pyproject.toml` (`fail_under = 95`). Adicione testes para cobrir.
- **mypy:** strict em `src` (`ignore_missing_imports=false`). Tipa tudo; `Any` só onde perfilado.
- **ruff:** line-length 100; exceções de lint documentadas por arquivo em `pyproject.toml`.
- **Teste de rate limit** sensível a recarga rápida: use taxa realista (não dispara em cascata).

## Frontend (build/visual)
- **Build falha (tsc):** tipos soltos; ajuste antes do commit.
- **Overflow horizontal na 1280×720:** revisar breakpoints e empilhamento (ver [UI_GUIDELINES.md](./UI_GUIDELINES.md)).

## Processos persistentes
- **uvicorn/vite são persistentes** — nunca use `WaitForExit()`/`communicate()`. Suba em background, faça health check e siga.
- Em Windows, inicie em background com `Start-Process` (logs em temp) e valide via `Invoke-WebRequest`.

## Referências
- Detalhes no [README](../README.md) ("Resolução de problemas") · `docs/guides/QUALITY_GUIDE.md`