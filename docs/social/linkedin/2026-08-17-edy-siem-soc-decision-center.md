# LinkedIn — EDY SIEM por dentro: SOC Decision Center

- Data planejada: 2026-08-17
- Status: DRAFT
- Tema: EDY SIEM por dentro — SOC Decision Center
- Ângulo: reduzir KPIs genéricos para deixar a próxima decisão explícita.
- Imagem selecionada: `2026-08-17-edy-siem-decision-queue.png`
- Origem: `../../../assets/screenshots/release-decision-center.png`; recorte focado na
  Decision Queue para não repetir a composição usada no post de 12/08.
- Link: https://github.com/EDY075/EDYSIEM
- Hashtags: `#SOC #SIEM #BlueTeam #CyberSecurity`

## Texto final

Em uma tela de SOC, eu acho fácil demais esconder o trabalho real atrás de KPI bonito.

Durante a revisão do EDY SIEM, cortei boa parte dessa vontade de preencher a Home com
cards. Um número isolado de alertas não diz muito para quem precisa decidir o que atacar
primeiro.

O centro da tela passou a ser a Decision Queue. Cada item carrega a severidade, o SLA, o
responsável, o ativo, a evidência e a próxima ação suportada. Se não há responsável ou se o
prazo está perto, isso precisa aparecer na mesma linha em que a pessoa lê o evento — não
escondido em outra página.

Essa escolha também trouxe uma regra simples para o produto: quando algum dado operacional
não está disponível, a interface declara isso em vez de preencher o espaço com simulação.

Não é a tela com mais gráficos. É a tela que eu gostaria de encontrar quando existe uma fila
real esperando alguém tomar uma decisão.

Código: https://github.com/EDY075/EDYSIEM

#SOC #SIEM #BlueTeam #CyberSecurity
