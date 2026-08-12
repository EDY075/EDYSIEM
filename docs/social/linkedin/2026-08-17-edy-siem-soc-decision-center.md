# LinkedIn — EDY SIEM por dentro: SOC Decision Center

- Data planejada: 2026-08-17
- Status: APPROVED
- Tema: EDY SIEM por dentro — SOC Decision Center
- Ângulo: reduzir KPIs genéricos para deixar a próxima decisão explícita.
- Imagem selecionada: `2026-08-17-edy-siem-decision-queue.png`
- Origem: `../../../assets/screenshots/release-decision-center.png`; recorte focado na
  Decision Queue para não repetir a composição usada no post de 12/08.
- Link: https://github.com/EDY075/EDYSIEM
- Hashtags: `#SOC #SIEM #BlueTeam #CyberSecurity`

## Texto final

Em uma tela de SOC, é fácil esconder o trabalho real atrás de KPI bonito.

Durante a revisão do EDY SIEM, eu percebi que estava colocando informação demais na Home. Mais cards, mais números, mais indicadores — mas isso não respondia a pergunta principal: o que precisa da minha atenção agora?

Foi daí que a Decision Queue virou o centro da tela.

Cada item reúne o que eu realmente gostaria de ter na frente durante uma triagem: severidade, SLA, responsável, ativo, evidência e a próxima ação. Se o alerta está sem responsável ou perto de estourar o prazo, isso aparece ali mesmo, junto do evento.

Outra coisa que eu preferi manter foi transparência nos estados. Se algum dado operacional não está disponível, o SIEM mostra isso. Não preenche o espaço com número inventado só para o dashboard parecer completo.

No fim, a Home ficou com menos gráficos e menos cards, mas muito mais útil para decisão.

Era exatamente essa mudança que eu queria: sair de um dashboard que mostra números e chegar mais perto de uma tela que ajuda alguém a decidir o que investigar primeiro.

Código: https://github.com/EDY075/EDYSIEM

#SOC #SIEM #BlueTeam #CyberSecurity
