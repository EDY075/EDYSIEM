# WORKFLOW.md — Fluxo de desenvolvimento, test, build e release

> O passo-a-passo operacional para agentes. Requisito: **nunca pular os gates** e
> nunca ficar preso por mais de **2 minutos** num passo travado (interrompa, preserve,
> relate pendência, continue com o que funciona).

## 1. Fluxo de feature/Sprint (regra geral)

```
docs → ADR (se decisão) → contrato/API → código → testes → docs (sincronizadas)
```

- **Regra Nº 1:** arquitetura aprovada antes de funcionalidade.
- Definition of Done: tipado, testado, documentado, ADR se decisão, CI verde.

## 2. Rodar o ambiente

```bash
python run.py                  # 1 comando: instala deps + cria DB + sobe backend/pre + seed + browser
```

## 3. Rodar os gates (antes de considerar pronto)

```bash
python -m pytest             # testes + coverage ≥ 95%
python -m mypy               # strict
python -m ruff check .       # lint
cd frontend && npm run build # tsc + vite
```

## 4. Padrão de commit / Git
Ver **[GIT_WORKFLOW.md](./GIT_WORKFLOW.md)**.

## 5. Release / publicar

**Fluxo de release 0.2.0:**
1. Tudo verde (gates).
2. Commit de release (ex.: `chore(release): 0.2.0`) e **tag**.
3. Exemplo de tag: `git tag -a release-0.2.0 -m "EDY SIEM 0.2.0"`.
4. **Push** (precisa de remoto): ver `git remote -v`; se não houver remoto, adicione
   `git remote add origin <URL>` e `git push origin --tags`. Fornecer os comandos ao usuário.

## 6. Regras de "tempo" (importantes para agentes)
- Se um passo travar > 2 min → **interrompa**, não investigue, preserve o estado,
  commite o que funciona, relate a pendência.
- Não use `WaitForExit()`/`communicate()` em **uvicorn/vite** (persistentes). Suba em
  background, faça health check, siga o fluxo.

## 7. Scripts auxiliares
- `scripts/dev.ps1` / `scripts/dev.sh` — runners do ambiente.
- `docs/guides` — guias de workflow, qualidade, logging, event bus, coding.

## Referências
- `docs/CONTRIBUTING.md` · `docs/CODING_STANDARD.md` · `docs/TESTING_GUIDE.md` · `docs/guides/QUALITY_GUIDE.md`