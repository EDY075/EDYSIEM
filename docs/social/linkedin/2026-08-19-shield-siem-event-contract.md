# LinkedIn — Como construí a integração Shield → SIEM

- Data planejada: 2026-08-19
- Status: DRAFT
- Tema: Como construí a integração Shield → SIEM
- Ângulo: a entrega confiável começa antes da requisição HTTP.
- Imagem selecionada: `2026-08-19-shield-siem-outbox-handoff.png`
- Origem: `../../../../edy-shield/docs/screenshots/release-fim-siem-handoff.png`; recorte
  que preserva a confirmação de entrega e a evidência FIM.
- Links: https://github.com/EDY075/edy-shield · https://github.com/EDY075/EDYSIEM
- Hashtags: `#Python #SQLite #SIEM #BlueTeam #CyberSecurity`

## Texto final

A parte mais trabalhosa da integração Shield → SIEM não foi fazer um POST funcionar. Foi
decidir o que acontece quando ele não funciona.

O Event Contract v1 nasce no Shield com um `event_id` estável e é persistido em uma SQLite
Outbox antes de qualquer tentativa HTTP. O worker de entrega roda separado do scan e do
alerta local. Se o SIEM estiver offline, o evento não some e o Shield não precisa parar para
esperar o receptor.

No SIEM, a Ingestion API valida e normaliza o contrato, enquanto a Inbox usa a identidade
do evento para receber a mesma entrega sem criar outro registro lógico. Para falhas
temporárias, o worker remarca a tentativa com backoff exponencial e jitter; respostas que
não devem virar tempestade de retry recebem tratamento separado.

Eu derrubei o SIEM de propósito durante o fluxo para verificar a parte que não aparece no
diagrama. Quando ele voltou, os eventos pendentes foram entregues. Nos testes de processo
real, o resultado foi zero eventos perdidos e zero duplicação lógica.

Essa foi a diferença entre integrar duas telas e construir uma fronteira de entrega que eu
conseguiria confiar durante uma indisponibilidade.

EDY Shield: https://github.com/EDY075/edy-shield
EDY SIEM: https://github.com/EDY075/EDYSIEM

#Python #SQLite #SIEM #BlueTeam #CyberSecurity
