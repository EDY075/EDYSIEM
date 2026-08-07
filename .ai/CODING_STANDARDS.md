# CODING_STANDARDS.md — Convenções de Código

> Padrões que qualquer agente deve seguir no EDY SIEM. Fonte canônica: `docs/CODING_STANDARD.md`.

## Princípios
- **Clean Architecture**: dependências sempre apontam para o domínio.
- **SOLID, KISS, DRY, YAGNI**; baixo acoplamento; responsabilidade única.
- **Zero gambiarra, zero duplicação, zero dependências desnecessárias.**
- **Código autodocumentado** — nomes claros, tipos fortes.

## Python (backend)
- **Tipo forte e rigoroso**: mypy strict em `src` (`disallow_untyped_defs`).
- **Result[T]** em vez de exceções de fluxo quando aplicável (estilo Rust). Nunca retorne `None` como "sucesso silencioso" onde `Result` cabe.
- **Dataclasses puras** para entidades; enums para domínio.
- `Any` apenas em fronteiras dinâmicas justificadas (exceções documentadas em `pyproject.toml`).
- **Ruff line-length 100**, seleção `E,F,I,B,UP,ANN,YTT,S,B008,RUF,PT`; ignores `UP046/UP047/UP040`.
- Erros tipados na hierarquia de `exceptions/`.

## TypeScript/React (frontend)
- **Tipagem estrita** (tsc) — sem `any` solto.
- Componentes no **Design System** (`frontend/src/design-system/`) reutilizáveis; páginas em `frontend/src/pages/`.
- Consumo de dados **sempre via API real** (hooks/`api/client.ts`). **Proibido inventar dados**.
- Estados de indisponibilidade explícitos (skeleton/empty/retry), nunca dados fictícios.
- Roteamento com `React.lazy` + `Suspense` (performance).

## Nomenclatura
- Backend: `snake_case` funções/var, `PascalCase` classes, módulos minúsculos.
- Frontend: `PascalCase` componentes/arquivos; hooks `useXxx`; tipos `XxxProps`.

## Governança de código
- Todo arquivo toca pelo menos um contexto de teste; testar em módulos `tests/`.
- Limpar imports sem uso e diretivas de lint obsoletas.
- Rodar **sempre** os gates antes de "pronto" (pytest, mypy, ruff, tsc).

## Referências
- `docs/CODING_STANDARD.md` · `docs/guides/CODING_GUIDE.md` · `docs/guides/QUALITY_GUIDE.md` (quando existirem de forma canônica)