# Relatório de Release Candidate — EDY SIEM

Data: 2026-08-06  
Status: `0.2.0-rc.1`

## Resumo executivo

O EDY SIEM foi consolidado como release candidate com identidade Echelon, shell operacional, telas SOC coerentes, contratos existentes preservados e validações de qualidade executadas. O frontend não apresenta conteúdo operacional fictício onde o contrato de API ainda não existe: mantém a estrutura e comunica a indisponibilidade de dados ou de integração de maneira explícita.

## Melhorias realizadas

### Sprint Final — acabamento Enterprise 1.0

- Eliminada a latência aleatória da barra operacional: o produto agora mostra `—` quando o contrato não fornece essa telemetria.
- Corrigido o chip `CRITICAL` no detalhe de Cases, que era esticado pelo alinhamento padrão de um container flex.
- Confirmados skeletons e empty states operacionais no Overview quando a API não está disponível; nenhum dado é inventado para preencher a tela.
- Revisados temas claro e escuro, sem overflow horizontal no viewport de notebook validado.
- Separados relógio local e momento da última resposta API, sem criar telemetria artificial ou alterar contratos.

- Aplicação da identidade Echelon no shell, Design System, favicon e assinatura visual.
- Revisão do Overview, War Room, Triage, Alertas, Incidentes, Investigation, Cases, Regras, Intelligence, Playbooks e Configurações.
- Sidebar com grupos de operação claros, nomes em maiúsculas, badges refinadas, estado ativo e interações discretas.
- Header operacional com workspace, command palette, estado do SOC, notificações, perfil e alternância de tema.
- KPIs semânticos, gráficos, tabelas, empty states, skeletons, badges, tooltips e drawers padronizados.
- Separação visual e conceitual entre catálogo de Regras e Intelligence/IOC Manager.
- Triage e Playbooks estruturados sem registros inventados; ações indisponíveis informam que dependem de integração.
- Remoção de evidências, eventos, correlações e timeline simulados do detalhe de alertas.
- Correção de um teste instável de rate limiting e cobertura dos caminhos de degradação do endpoint de saúde.
- Remoção de import órfão em `run.py` e limpeza de uma diretiva Ruff obsoleta.
- Varredura de caracteres corrompidos nos fontes de frontend, backend e testes alterados.

## Problemas encontrados e resolvidos

### Sprint — Polimento final e integração controlada

- A Command Palette agora reconhece o atalho nativo da plataforma (`Ctrl K` ou `⌘K`), mantém foco, teclado e comandos reais para navegação, tema, recarga e notificações.
- A central de notificações usa alertas existentes, permite marcar itens como lidos com persistência local e abre a rota de alertas; nenhum registro foi criado para compor a lista.
- Perfil passa a oferecer preferências e alternância de tema. Encerramento de sessão continua indisponível com explicação, pois não há autenticação segura no contrato atual.
- Configurações foi expandida para incluir Collectors, Retention, Security e Audit. Os itens sem API aparecem como pendentes, sem simular estado ou configuração operacional.
- Não foi necessário criar endpoint, token, banco ou autenticação provisória: preferências exclusivamente de interface continuam no navegador, e os dados operacionais permanecem originados pela API existente.

| Problema | Tratamento |
|---|---|
| Detalhe de alerta exibia artefatos e eventos fictícios | Abas agora exibem somente dados de contrato e estados internos de indisponibilidade. |
| Teste de token bucket era sensível a recarga imediata | Teste passou a usar taxa realista para validar consumo sem alterar a implementação. |
| Endpoint de saúde não tinha teste dos fallbacks por exceção | Novo cenário confirma que engines indisponíveis retornam estado `error` sem derrubar a API. |
| Rótulos da sidebar recebiam sublinhado padrão de links | Navegação recebeu estilo explícito sem decoração de texto. |
| Import e regra de lint sem uso | Removidos para manter o backend limpo. |

## Validação executada

| Verificação | Resultado |
|---|---|
| TypeScript (`tsc -b`) | Aprovado |
| Command Palette | Validada no navegador local: `Ctrl K`, foco automático e comandos de sistema visíveis |
| Persistência de tema/notificações | Validada por armazenamento local do navegador, sem token ou identidade fictícia |
| Testes Python | 793 aprovados |
| Cobertura | 95,05% (gate de 95% aprovado) |
| Ruff check | Aprovado |
| Ruff format (fontes e testes) | Aprovado |
| MyPy strict | Aprovado em 146 arquivos |
| Compileall | Aprovado |
| Runtime e rotas | 11 rotas principais carregadas no navegador local sem tela vazia |
| Tema dark/light | Validado; dark restaurado como padrão |
| Overflow em viewport de notebook (1280×720) | Não identificado |
| UTF-8/mojibake | Nenhum padrão encontrado nos fontes revisados |
| Build Vite | Aprovado em execução normal: 674 módulos transformados e bundle de produção gerado. |
| Build do pacote Python | O ambiente local não possui `hatchling`/`build`; a configuração de empacotamento está declarada no `pyproject.toml`, mas o artefato deve ser gerado em ambiente de release com dependências de build instaladas. |

Avisos externos restantes: duas deprecações originadas por `starlette.testclient`/`httpx` no ambiente instalado. Não afetam os 793 testes, mas devem ser tratadas em atualização planejada de dependências.

## Arquivos modificados

### Frontend

- `frontend/index.html`, `frontend/src/App.tsx`
- `frontend/src/charts/basic.tsx`, `frontend/src/charts/more.tsx`
- `frontend/src/components/Page.tsx`
- `frontend/src/design-system/components/{BrandMark.tsx,Button.tsx,DataTable.tsx,Timeline.tsx,badges.tsx,cards.tsx,feedback.tsx,overlays.tsx,primitives.tsx}`
- `frontend/src/design-system/tokens/{colors.ts,index.ts,tokensCss.ts}` e `frontend/src/design-system/index.ts`
- `frontend/src/pages/{AlertCenterPage.tsx,AlertDetailDrawer.tsx,CaseCenterPage.tsx,DashboardOverview.tsx,IncidentCenterPage.tsx,IntelligencePage.tsx,InvestigationPage.tsx,PlaybooksPage.tsx,RulesPage.tsx,SettingsPage.tsx,TriagePage.tsx,WarRoomPage.tsx}`
- `frontend/src/routing/routes.tsx`
- `frontend/src/shell/{AppShell.tsx,GlobalSearch.tsx,LiveOperationsBar.tsx,Sidebar.tsx,ThemeSwitch.tsx,Topbar.tsx,UserMenu.tsx}`
- `frontend/src/theme/ThemeProvider.tsx`
- `frontend/public/` (ícones e favicon Echelon)

### Backend e testes

- `run.py`
- `src/edysiem/soc/service.py`
- `tests/test_api.py`, `tests/test_dev_runner.py`, `tests/test_ingestion_rate_limiter.py`

### Documentação

- `README.md`, `CHANGELOG.md`, `docs/ROADMAP.md`
- `docs/TRIAGE_PLAYBOOKS_API_CONTRACT.md`
- `docs/design/ECHELON_BRAND.md`
- `docs/RELEASE_CANDIDATE_REPORT.md`

## Pendências e recomendações para o JR antes da publicação

1. Instalar as dependências de build do backend (`hatchling` ou `python -m build`) e executar o wheel em ambiente de release.
2. Executar `npm run build` fora do sandbox do Codex e registrar o resultado no pull request.
3. Atualizar a combinação `starlette`/`httpx` para remover os dois avisos de deprecação, confirmando novamente a suíte.
4. Configurar variáveis de ambiente de produção, banco persistente, CORS, logs centralizados, monitoramento e backups antes de expor a API.
5. Configurar CI obrigatório com TypeScript, Ruff, MyPy, Pytest/cobertura e build do frontend.
6. Implementar os contratos já documentados para Triage, Playbooks e as abas enriquecidas de detalhes de alerta; manter as ações indisponíveis até então.
7. Revisar licenças de dependências, política de retenção de dados, autenticação/RBAC e gestão de segredos antes do deploy público.
8. Revisar o diff, incluir os novos assets e efetuar o commit em uma branch de release.
