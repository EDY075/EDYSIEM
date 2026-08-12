# LinkedIn — EDY Shield por dentro: Endpoint Integrity & Defense

- Data planejada: 2026-08-14
- Status: DRAFT
- Tema: EDY Shield por dentro — Endpoint Integrity & Defense
- Ângulo: por que FIM não deve se comportar como um mini-SIEM.
- Imagem selecionada: `2026-08-14-edy-shield-endpoint-integrity.png`
- Origem: `../../../../edy-shield/docs/screenshots/release-endpoint-integrity.png`; cópia com
  recorte do rodapé da captura, sem alterar a interface original.
- Link: https://github.com/EDY075/edy-shield
- Hashtags: `#CyberSecurity #BlueTeam #FIM #Python`

## Texto final

Uma coisa que eu precisei ajustar no EDY Shield foi a ambição da tela principal.

No começo, era tentador fazer o painel crescer para todos os lados: mais indicadores, mais
cards, mais sinais. Mas o papel do Shield não é tentar virar um mini-SIEM. Ele precisa
responder bem a uma pergunta mais direta: o que mudou em um endpoint e o que eu preciso
revisar agora?

Por isso o Endpoint Integrity Center ficou centrado em FIM. A baseline cria a referência.
O scan compara o estado atual com ela. Quando um arquivo muda, a investigação mostra a
alteração, o contexto da baseline e a comparação de hashes antes de sugerir qualquer
decisão.

Também mantive esse caminho local-first. Baseline, scans, análise de hashes e alertas
locais continuam disponíveis mesmo quando o SIEM não está acessível. Isso parece um detalhe
de arquitetura até o momento em que o serviço remoto cai e o endpoint ainda precisa ser
avaliado.

O resultado ficou menos espalhado: menos aparência de dashboard genérico e mais foco em
integridade de endpoint.

Código: https://github.com/EDY075/edy-shield

#CyberSecurity #BlueTeam #FIM #Python
