# EDY SIEM — Screenshots (Sprint UI/UX Review)

Capturas com Chrome headless (1920×1080) contra o backend real (`/soc` seedado:
4 alertas, 1 incidente, 2 casos, 3 regras, 3 IOCs, 3 assets).

## Antes → Depois (polimento UI/UX Polish)

- **Antes:** `screenshots/` (+ `responsive_dashboard_1366/768.png`)
- **Depois:** `screenshots_after/` (mesmas rotas, pós-polish)

## Índice

| # | Tela | Arquivo | Rota |
|---|------|---------|------|
| 1 | Dashboard | `01_dashboard.png` | `/` |
| 2 | War Room | `02_war_room.png` | `/war-room` |
| 3 | Alert Center | `03_alert_center.png` | `/alerts` |
| 4 | Incident UI | `04_incidents.png` | `/incidents` |
| 5 | Case UI | `05_cases.png` | `/cases` |
| 6 | Investigation Workspace | `06_investigation.png` | `/investigate` |
| 7 | Rules (Intelligence) | `07_rules.png` | `/rules` |
| 8 | Detection Dashboard | `08_detection.png` | `/detection` |
| 9 | Dashboard 1366×768 | `responsive_dashboard_1366.png` | `/` |
| 10 | Dashboard tablet 768×1024 | `responsive_dashboard_768.png` | `/` |

## Estados que exigem interação (não capturáveis por URL estática)

Requirem clique/estado no navegador — captura manual ou automação (Puppeteer/Playwright):

- **Drawer aberto** (Alert Center / Incident Center)
- **Filtros ativos** (severidade/status no Alert Center)
- **Rule Simulator** / **IOC Manager** / **Asset Inventory** (abas da `IntelligencePage`)
- **Estado vazio** (listas sem dados)
- **Loading skeleton** (durante fetch)
- **Toast notification** (após ação)

> Comandos usados (exemplo):
> `chrome --headless=new --disable-gpu --hide-scrollbars --user-data-dir=tmp --window-size=1920,1080 --virtual-time-budget=12000 --screenshot=out.png http://localhost:5173/<rota>`
