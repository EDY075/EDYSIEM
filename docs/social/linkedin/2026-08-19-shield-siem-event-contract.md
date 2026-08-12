# LinkedIn — Como construí a integração Shield → SIEM

- Data planejada: 2026-08-19
- Status: APPROVED
- Tema: Como construí a integração Shield → SIEM
- Ângulo: a entrega confiável começa antes da requisição HTTP.
- Imagem selecionada: `2026-08-19-shield-siem-outbox-handoff.png`
- Origem: `../../../../edy-shield/docs/screenshots/release-fim-siem-handoff.png`; recorte
  que preserva a confirmação de entrega e a evidência FIM.
- Links: https://github.com/EDY075/edy-shield · https://github.com/EDY075/EDYSIEM
- Hashtags: `#Python #SQLite #SIEM #BlueTeam #CyberSecurity`

## Texto final

A parte mais trabalhosa da integração Shield → SIEM não foi fazer um POST funcionar.

Foi decidir o que deveria acontecer quando ele não funcionasse.

No EDY Shield, cada evento recebe um `event_id` estável e entra primeiro em uma SQLite Outbox. Só depois o worker tenta entregar esse evento ao SIEM.

Isso foi importante porque eu não queria que a proteção do endpoint dependesse de uma conexão disponível o tempo todo.

Do outro lado, o EDY SIEM valida e normaliza o Event Contract v1 antes de persistir o evento na Inbox. Se o mesmo `event_id` chegar novamente, ele é reconhecido sem criar outro registro lógico.

Também precisei separar bem o que merece nova tentativa do que não merece.

Timeout, indisponibilidade e falhas temporárias entram em retry com backoff. Já um payload estruturalmente inválido não pode ficar preso em um loop infinito tentando ser enviado para sempre.

O teste que mais me interessava era simples: desligar o SIEM no meio do fluxo.

O Shield continuou funcionando e guardando os eventos. Quando o SIEM voltou, os pendentes foram entregues.

Nos testes finais: zero eventos perdidos e zero duplicação lógica.

Foi aí que a integração começou a fazer sentido para mim. Não era só ligar duas interfaces, mas construir uma fronteira de entrega que continuasse confiável quando uma das partes estivesse fora do ar.

EDY Shield: https://github.com/EDY075/edy-shield
EDY SIEM: https://github.com/EDY075/EDYSIEM

#Python #SQLite #SIEM #BlueTeam #CyberSecurity
