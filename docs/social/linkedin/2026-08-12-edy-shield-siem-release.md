# LinkedIn — EDY Shield + EDY SIEM release

- Data de preparação: 2026-08-12
- Status: PREPARADO — não publicado em 2026-08-12 08:20 -03:00. A sessão estava
  autenticada, mas o controle disponível não conseguiu anexar o arquivo ao seletor nativo
  do LinkedIn nem inserir a acentuação no editor. O rascunho foi descartado sem envio.
- Imagem publicada: `2026-08-12-edy-ecosystem-release.png`
- Origem da imagem: `assets/screenshots/release-decision-center.png`, com recorte vertical
  que remove somente o rodapé de versão anterior da captura. Não há dados sensíveis.
- Repositórios: https://github.com/EDY075/edy-shield · https://github.com/EDY075/EDYSIEM
- Releases: https://github.com/EDY075/edy-shield/releases/tag/v2.3.0 · https://github.com/EDY075/EDYSIEM/releases/tag/v0.3.0

## Texto final

Fechei hoje uma etapa que vinha faltando no ecossistema EDY: o Shield e o SIEM deixaram de parecer dois dashboards independentes e passaram a trabalhar no mesmo fluxo Blue Team.

O EDY Shield v2.3.0 ficou responsável pela integridade do endpoint: baseline, comparação de arquivos, hashes e alertas locais. Quando precisa encaminhar um evento, ele usa um outbox local durável.

Do outro lado, o EDY SIEM v0.3.0 recebe esse evento, normaliza, coloca na Decision Queue e leva a investigação até evidências, contexto de entidade, MITRE quando aplicável, decisão e caso. O Case Center também consegue voltar ao mesmo `event_id`, sem perder a origem do alerta.

O teste que eu mais quis fechar não era o caminho feliz. Derrubei o SIEM durante o fluxo: o Shield continuou funcionando, manteve os eventos pendentes e, quando o receptor voltou, entregou tudo. Nos testes realizados, isso terminou com zero eventos perdidos e zero duplicação lógica.

Foi a primeira vez que senti que os dois projetos começaram a funcionar como partes do mesmo ecossistema, e não só como interfaces que combinam visualmente.

Fechei a release com 687 testes no Shield e 948 no SIEM, além de validação de lint, tipos, builds e do fluxo completo em processos reais.

EDY Shield: https://github.com/EDY075/edy-shield
EDY SIEM: https://github.com/EDY075/EDYSIEM

#CyberSecurity #BlueTeam #SOC #SIEM #Python #React
