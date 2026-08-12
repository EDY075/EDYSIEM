# LinkedIn — Investigation Workflow: do alerta ao caso

- Data planejada: 2026-08-21
- Status: DRAFT
- Tema: Investigation Workflow
- Ângulo: preservar o contexto do alerta até o caso, em vez de recriar a história.
- Imagem selecionada: `2026-08-21-investigation-case-workflow.png`
- Origem: `../../../assets/screenshots/release-case-center.png`; cópia recortada sem o
  rodapé da captura e com foco na proveniência, timeline e vínculo de caso.
- Link: https://github.com/EDY075/EDYSIEM
- Hashtags: `#IncidentResponse #SOC #SIEM #BlueTeam`

## Texto final

Um alerta não vira investigação só porque ganhou uma página nova.

No fluxo que fechei no EDY SIEM, o objetivo era não obrigar o analista a reconstruir a
história toda vez que muda de tela. A investigação começa com a evidência recebida do
Shield, preserva o endpoint e os metadados do evento, mostra MITRE somente quando essa
associação veio na origem e deixa explícita a próxima decisão.

Quando faz sentido criar um caso, o vínculo carrega a proveniência do evento. O Case Center
continua sabendo de onde ele veio e oferece o caminho de volta para o mesmo `event_id`.

Teve uma parte menos visível, mas importante: criar o case duas vezes, inclusive em
requisições concorrentes, não pode duplicar evidência nem abrir outro caso para o mesmo
evento. Esse comportamento ficou coberto por teste e foi validado no fluxo real.

Eu quis que a transição alerta → investigação → caso fosse uma continuidade operacional,
não uma coleção de telas soltas. É um detalhe que muda bastante a leitura de quem precisa
responder a um evento sem perder contexto no caminho.

Código: https://github.com/EDY075/EDYSIEM

#IncidentResponse #SOC #SIEM #BlueTeam
