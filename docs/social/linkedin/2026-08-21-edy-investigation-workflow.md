# LinkedIn — Investigation Workflow: do alerta ao caso

- Data planejada: 2026-08-21
- Status: APPROVED
- Tema: Investigation Workflow
- Ângulo: preservar o contexto do alerta até o caso, em vez de recriar a história.
- Imagem selecionada: `2026-08-21-investigation-case-workflow.png`
- Origem: `../../../assets/screenshots/release-case-center.png`; cópia recortada sem o
  rodapé da captura e com foco na proveniência, timeline e vínculo de caso.
- Link: https://github.com/EDY075/EDYSIEM
- Hashtags: `#IncidentResponse #SOC #SIEM #BlueTeam`

## Texto final

Um alerta não vira investigação só porque ganhou uma página nova.

No fluxo que fechei no EDY SIEM, eu queria evitar uma coisa que me incomodava: o analista precisar reconstruir a história toda vez que muda de tela.

A investigação começa com a evidência recebida, mantém o endpoint e o contexto do evento, mostra MITRE somente quando existe uma associação confiável e deixa a próxima decisão clara.

Quando essa decisão vira um caso, o contexto vai junto. O Case Center sabe de qual evento aquele caso nasceu e também oferece o caminho de volta para a investigação original usando o mesmo `event_id`.

Teve uma parte menos visível, mas importante: garantir que duas requisições simultâneas não criassem dois casos para o mesmo evento. A criação ficou idempotente e esse cenário também entrou nos testes.

No fim, o fluxo ficou:

alerta → evidência → entidade → MITRE → decisão → caso

O que eu queria era exatamente isso: que trocar de tela não significasse perder contexto no meio de uma investigação.

Código: https://github.com/EDY075/EDYSIEM

#IncidentResponse #SOC #SIEM #BlueTeam
