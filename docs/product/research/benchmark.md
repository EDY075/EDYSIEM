# EDY SIEM — Benchmark Técnico de SIEMs

> Estudo comparativo de plataformas SIEM para fundamentar decisões de arquitetura e UX.
> **Nunca copiar interface.** Usar apenas como inspiração para o EDY SIEM.
> Data: 2026-08-03

## Resumo executivo

O mercado SIEM convergiu para um modelo comum: **ingestão → normalização → enriquecimento →
correlação → detecção (MITRE) → incidente → investigação → resposta**. A diferenciação está
em **UX de investigação**, **motor de busca**, **qualidade da correlação** e **ecossistema**.

| Produto | Modelo | Força central | Fraqueza central |
|---|---|---|---|
| Microsoft Sentinel | SaaS (cloud) | Integração M365 + KQL | Dependência total do Azure |
| Splunk Enterprise Security | On-prem/cloud | Busca SPL + detecção madura | Custo/licença elevados |
| IBM QRadar | On-prem/cloud | Correlação forte (rules) | UX datada, onboarding complexo |
| Elastic Security | Open/cloud | Free + Open, SIEM+EDR | Complexidade de operação (cluster) |
| Wazuh | Open source | Gratuito, FIM+SIEM+XDR | Escala/performance limitada |
| Graylog | Open source | Coleta centralizada + busca | Correlação/detecção limitadas |
| Google Chronicle | SaaS | Escala massiva + intel Google | UX de investigação específica |
| Exabeam | SaaS/híbrido | UEBA + analytics | Foco em comportamento, não regras |
| Securonix | SaaS/híbrido | Analytics + risco | Complexidade e custo |

---

## 1. Microsoft Sentinel

**Arquitetura:** SIEM SaaS nativo do Azure. Ingestão via Data Connectors → Log Analytics
(workspace) → Analytics Rules → Incidents → Workbooks/SOAR (Logic Apps).

**Fluxo de eventos:** Fontes → Connectors → Log Analytics → Normalização (ASIM) →
Enrichment (UEBA) → Detection (Analytics Rules) → Incident → Investigation graph.

**Dashboard/UX:** Workbooks altamente customizáveis; visão de Overview com KPIs;
tons de Azure; foco em integração M365.

**Menu:** navegação por blades: Overview, Logs, Hunting, Incidents, Workbooks,
Analytics, Data connectors, UEBA.

**Investigação:** **Investigation Graph** — grafo visual de entidades (host, user, IP,
processos) com relação entre alertas; timeline lateral.

**Timeline:** incident timeline com eventos, atividades e entidades relacionadas.

**Alertas:** Analytics Rules (scheduled/query-based) com severidade, MITRE ATT&CK,
entidades mapeadas; agrupamento em incidentes.

**Correlação:** baseada em KQL (queries sobre logs); agregação em janela; fusão de alertas
por entidade.

**Busca:** **KQL (Kusto Query Language)** — linguagem poderosa de consulta sobre dados
tabulados; suporta joins, agregações, time-series.

**Threat Intelligence:** conectores para feeds de TI (Anomali, MISP, Recorded Future);
indicadores aparecem em alertas.

**MITRE ATT&CK:** mapeamento automático em Analytics Rules; Hunting com navegação MITRE.

**Casos de uso:** SOC na nuvem Azure, detecção M365/AAD, incident response integrado a SOAR.

**Pontos fortes:** integração M365, KQL, grafo de investigação, SOAR nativo, MITRE embutido.

**Pontos fracos:** custo por ingestão, lock-in Azure, UX sobrecarregada em organizações
grandes, complexidade de governança.

**Inspiração para EDY SIEM:** grafo de investigação, mapeamento MITRE em regras,
agrupamento de alertas em incidentes por entidade.

---

## 2. Splunk Enterprise Security

**Arquitetura:** indexadores (indexers) + forwarders (coleta) + search heads (busca) +
Splunk ES app. On-prem ou Splunk Cloud. Pipeline: forward → index → parse → search.

**Fluxo de eventos:** Forwarders → Indexers → Parsing (CIM normalization) →
Correlation (ES) → Notable Events → Incident review → Investigation.

**Dashboard/UX:** dashboards ES ricos (posturas de segurança, ameaças, conformidade);
visual "enterprise" denso; navegação por páginas de domínio.

**Menu:** Overview, Security Posture, Threat Intelligence, Notable Events, Risk Analysis,
Investigation, ES Health, etc.

**Investigação:** páginas de investigação com tabelas de eventos relacionados, campo
"Notable Event" com drill-down; suporte a lançar busca a partir de um valor.

**Timeline:** linha do tempo do incidente; eventos ordenados por tempo com destaque.

**Alertas:** Notable Events (baseados em correlation searches) com severidade, owner,
status (new/ack/resolved); "Adaptive Response" para ações.

**Correlação:** correlation searches agendados (SPL), agregação temporal, risk-based alerting
(Accelerated Risk Score), "Asset & Identity framework".

**Busca:** **SPL (Search Processing Language)** — pipeline de comandos, extremamente
flexível; índice invertido.

**Threat Intelligence:** Threat Intelligence Framework (importar feeds, correlacionar com
eventos).

**MITRE ATT&CK:** frameworks de mapeamento em regras; suporte a risk object.

**Casos de uso:** SOC enterprise maduro, forense sobre grandes volumes, compliance.

**Pontos fortes:** SPL maduro, ecossistema enorme, risk-based alerting, maturity.

**Pontos fracos:** licença por volume de dados (cara), curva de aprendizado, UX densa
e datada, operação complexa.

**Inspiração para EDY SIEM:** risk-based alerting (score de risco por entidade),
drill-down de investigação, framework Asset & Identity.

---

## 3. IBM QRadar

**Arquitetura:** consoles (UI) + collectors (log sources) + event processors (EPS) +
offense engine. On-prem clássico; QRadar on Cloud; QRadar Suite (SIEM + EDR + SOAR).

**Fluxo de eventos:** Log sources → Collectors → Event Processors (normalização) →
Magnitude/Offense Engine → Offense → Investigation.

**Dashboard/UX:** dashboards por tab; visual enterprise denso e datado; navegação por
"Offenses" como conceito central.

**Menu:** Offenses, Log Activity, Network Activity, Assets, Rules, Reference Sets,
Dashboards, Reports, Admin.

**Investigação:** **Offenses** (agrupam eventos+fluxos+assinaturas) com "offense timeline";
drill-down para Log Activity (busca de eventos).

**Timeline:** offense timeline com eventos ordenados; "offense watchers".

**Alertas:** **Offenses** (magnitude = relevância por peso de regras/severidade/crimes) com
estado (open/hidden/closing); notificações.

**Correlação:** **QRadar Rules** (regras de correlação com condições, ofensa, janela);
**Magnitude** (score de relevância); Reference Sets (IOCs).

**Busca:** **Ariel Query Language (AQL)** — SQL-like sobre eventos/fluxos indexados.

**Threat Intelligence:** Reference Sets alimentados por feeds; integração intel.

**MITRE ATT&CK:** suporte via regras e integrações (QRadar Advisor).

**Casos de uso:** SOC enterprise com forte correlação, bancos, governo.

**Pontos fortes:** correlação madura (rules + magnitude), conceito de Offense,
Reference Sets, estabilidade.

**Pontos fracos:** UX datada, onboarding complexo, customização cara, AQL menos
conhecida que SPL/KQL.

**Inspiração para EDY SIEM:** conceito de "offense" (incidente agregado com magnitude),
Reference Sets (listas de intel reutilizáveis), regras com peso e janela.

---

## 4. Elastic Security

**Arquitetura:** stack Elasticsearch + Kibana (+ Beats/Agent). SIEM + EDR no mesmo stack.
Open source base + licenças comerciais (Enterprise).

**Fluxo de eventos:** Elastic Agent/Beats → Logstash/ES ingest → Elasticsearch →
Kibana (Security Solution) → Alerts (Detection Engine) → Cases → Investigation.

**Dashboard/UX:** Kibana moderno; Security Solution com visão unificada (Overview,
Alerts, Timelines, Hosts, Network, Cases); visual dark profissional.

**Menu:** Overview, Alerts, Timelines, Hosts, Network, Users, Rules, Exceptions,
Cases, Endpoints, Integrations.

**Investigação:** **Timeline** (investigation workspace arrastável) + Graph (relações entre
entidades); Timeline templates reutilizáveis.

**Timeline:** conceito central — tabela de eventos com dados de contexto, anotações,
pinos de eventos.

**Alertas:** Detection Rules (threshold, anomaly, EQL, ML) com severidade, status
(open/ack/closed), MITRE; **Cases** para agrupar alertas.

**Correlação:** **EQL (Event Query Language)** para correlação sequencial; regras
threshold/aggregation; correlação via índice de eventos.

**Busca:** **Kibana Query Language (KQL)** + Lucene; busca full-text em documentos JSON.

**Threat Intelligence:** Threat Intel indices (feeds), match de IOCs em regras.

**MITRE ATT&CK:** mapeamento completo em rules; tela de cobertura MITRE.

**Casos de uso:** SOC open source, observabilidade+segurança unificadas, hunting.

**Pontos fortes:** open source, SIEM+EDR integrado, Timelines, EQL, MITRE completo.

**Pontos fracos:** operação de cluster ES complexa, consumo de recursos, curva de
aprendizado, custo em escala.

**Inspiração para EDY SIEM:** conceito de Timeline como workspace, cobertura MITRE visual,
Cases (agrupamento de alertas), busca com query language própria.

---

## 5. Wazuh

**Arquitetura:** open source SIEM+XDR. Wazuh manager (servidor) + agents (endpoints) +
indexer/OpenSearch + dashboard. Agent-based (FIM, logcollector, rootcheck, syscheck).

**Fluxo de eventos:** Agents → Manager (decoders/rules) → Alertas → Indexer →
Dashboard; integração com dados externos via syslog.

**Dashboard/UX:** Wazuh Dashboard (OpenSearch Dashboards) com módulos: Security events,
Integrity monitoring, Vulnerabilities, PCI DSS, etc.

**Menu:** Overview, Security Events, Integrity Monitoring, Threat Hunting, Virustotal,
Vulnerabilities, Rules, Decoders, Agents.

**Investigação:** Threat Hunting com busca em eventos indexados; drill-down por agente;
mapa MITRE.

**Timeline:** eventos ordenados por tempo; tabela de alertas com detalhes por regra.

**Alertas:** Rules (XML-like) com nível (severity 1-15), grupo, MITRE mapping;
nível ≥ threshold vira alerta visível.

**Correlação:** decoders + rules; correlação simples (matches de campos); sem motor de
correlação complexo multi-janela.

**Busca:** query DSL do OpenSearch (Lucene-like); busca por campos do alerta.

**Threat Intelligence:** integração VirusTotal; feeds via regras/decoders.

**MITRE ATT&CK:** mapeamento em rules (mitre.id); Threat Hunting com MITRE.

**Casos de uso:** FIM, hardening, SOC leve open source, PCI DSS.

**Pontos fortes:** gratuito, FIM robusto, agentes, instalação relativamente simples,
comunidade ativa.

**Pontos fracos:** escala/performance limitadas, correlação simples, UX média, operação
do indexer OpenSearch.

**Inspiração para EDY SIEM:** integração FIM, mapeamento MITRE em regras de detecção,
dashboard de coverage por compliance.

---

## 6. Graylog

**Arquitetura:** open source log management centralizado. Graylog server + MongoDB
(metadados) + Elasticsearch/OpenSearch (índice de mensagens) + Inputs (syslog, GELF, HTTP).

**Fluxo de eventos:** Inputs → Graylog (extractors/parsers) → Elasticsearch index →
Search → Streams → Alerts → Dashboards.

**Dashboard/UX:** UI própria (React) com Busca, Streams, Dashboards, Alerts; visual limpo,
focado em logs.

**Menu:** Search, Streams, Alerts, Dashboards, Pipelines, System.

**Investigação:** busca por mensagens com highlight; contexto de mensagem; "Show surrounding
messages" (linhas adjacentes).

**Timeline:** não é conceito central; eventos ordenados na busca.

**Alertas:** Alert Conditions em Streams (mensagem, aggregation); alertas com
severidade/notificação.

**Correlação:** Streams (filtros) + aggregation conditions; sem motor de correlação
avançado; pipelines para transformação.

**Busca:** busca Lucene-like com filtros de tempo; "query language" simples.

**Threat Intelligence:** lookup tables (lookup adapter) para IOCs.

**MITRE ATT&CK:** não nativo; via pipelines/regras customizadas.

**Casos de uso:** centralização de logs, busca de eventos, alertas simples.

**Pontos fortes:** coleta centralizada simples, UI limpa, pipelines de processamento,
gratuito.

**Pontos fracos:** correlação/detecção limitadas, sem conceito de incidente maduro,
operações do cluster ES.

**Inspiração para EDY SIEM:** busca com "surrounding messages" (contexto por linhas),
pipelines de transformação declarativa.

---

## 7. Google Chronicle

**Arquitetura:** SIEM SaaS da Google Cloud, desenhado para escala massiva (petabytes),
com o **Unified Data Model (UDM)** como modelo canônico obrigatório.

**Fluxo de eventos:** Forwarders/API → Chronicle (parse + normalização UDM) →
enriquecimento automático (Google intel) → detecção (YARA-L) → alertas → investigação.

**Dashboard/UX:** UX moderna e limpa; foco em **busca rápida** e contexto; visão por
entidade (entity-centric).

**Menu:** Overview, Detect (YARA-L rules), Curate, Search, Explore, Assets, IOCs,
Audit, SIEM settings.

**Investigação:** **entity-centric** — busca por entidade (host, user, IP, domínio)
revela todos os eventos, alertas e intel associados em segundos.

**Timeline:** timeline de eventos por entidade; "event graph" para contexto visual.

**Alertas:** YARA-L rules (detecção baseada em UDM) com severidade e mapeamento MITRE;
alertas agrupáveis em cases.

**Correlação:** YARA-L (linguagem de detecção sobre eventos normalizados); agregação e
combinação de eventos; escala massiva.

**Busca:** busca por entidades, campos UDM, queries rápidas; indexação global.

**Threat Intelligence:** intel nativa do Google (threat intel, reputation) aplicada
automaticamente.

**MITRE ATT&CK:** mapeamento em YARA-L rules; visão por técnica.

**Casos de uso:** SOC enterprise com volume massivo, hunting com intel Google.

**Pontos fortes:** escala, modelo UDM forte, entity-centric, intel embutida, busca rápida.

**Pontos fracos:** lock-in Google Cloud, custo, YARA-L específica, onboarding de dados.

**Inspiração para EDY SIEM:** **modelo canônico forte (UDM)**, visão entity-centric,
busca rápida por entidade, enriquecimento automático.

---

## 8. Exabeam

**Arquitetura:** SIEM SaaS/híbrido focado em **UEBA** (User and Entity Behavior Analytics).
Coletores de logs → normalização → analytics comportamental → detecção de desvios.

**Fluxo de eventos:** Log sources → Exabeam collectors → normalização →
behavioral analytics (baselines por usuário/dispositivo) → Security Analytics →
Incident timeline.

**Dashboard/UX:** UX moderna com foco em **user/entity timeline**; painéis de risco;
interface limpa e orientada a contexto.

**Menu:** Security Analytics, Users & Entities, Threat Hunting, Cases, Rules,
Data Sources, Intelligence.

**Investigação:** **Session Timeline** — linha do tempo automática de atividades de um
usuário/entidade (bastante visual); "smart timelines" geradas por ML.

**Timeline:** é o coração — timeline por sessão/usuario com eventos, riscos, entidades.

**Alertas:** detecção por desvio de baseline (UEBA) + regras; risco acumulado por entidade.

**Correlação:** analytics comportamental + agrupamento por entidade; menos regras estáticas,
mais comportamento.

**Busca:** busca por entidades e eventos; foco em navegação de contexto, não query language.

**Threat Intelligence:** integração de feeds de intel para enriquecimento.

**MITRE ATT&CK:** mapeamento de eventos/táticas; visão por técnica.

**Casos de uso:** insider threat, comprometimento de conta, detecção comportamental.

**Pontos fortes:** UX de timeline excelente, UEBA embutido, foco em entidade.

**Pontos fracos:** custo, foco comportamental (menos regras tradicionais), dependência de
baseline para eficácia.

**Inspiração para EDY SIEM:** **session/entity timeline** (linha do tempo de atividades),
risco acumulado por entidade.

---

## 9. Securonix

**Arquitetura:** SIEM SaaS/híbrido com forte foco em **analytics** e **detecção de ameaças
desconhecidas**. Coleta → normalização → analytics (rules + ML) → incidentes.

**Fluxo de eventos:** Log sources → collectors → normalização → Spotter query language →
analytics (regras + UEBA) → Incident → investigation.

**Dashboard/UX:** UX enterprise moderna; painéis de risco; visão por incidente com contexto.

**Menu:** Incident Management, Threat Detection, User Analytics, Data Lake, Policies,
Risk, Intelligence.

**Investigação:** incident workspace com timeline, entidades e evidências; busca via
**Spotter**.

**Timeline:** incident timeline com eventos e ações; visual de atividades de entidades.

**Alertas:** Policies (regras) + analytics; risco por entidade; incidentes com priorização.

**Correlação:** Spotter query language (SQL-like) + policies; analytics comportamental;
agregação em incidentes.

**Busca:** Spotter (SQL-like sobre dados normalizados).

**Threat Intelligence:** integrações de intel; enriquecimento.

**MITRE ATT&CK:** mapeamento em policies; visão de coverage.

**Casos de uso:** SOC enterprise com analytics, insider threat, priorização de risco.

**Pontos fortes:** analytics forte, priorização por risco, incident workspace.

**Pontos fracos:** custo, complexidade de implementação, curva de aprendizado.

**Inspiração para EDY SIEM:** priorização por risco de entidade, incident workspace
integrado, query language sobre modelo normalizado.

---

## Tabela comparativa

| Critério | Sentinel | Splunk ES | QRadar | Elastic | Wazuh | Graylog | Chronicle | Exabeam | Securonix |
|---|---|---|---|---|---|---|---|---|---|
| Modelo | SaaS | On-prem/Cloud | On-prem/Cloud | Open/Cloud | Open | Open | SaaS | SaaS/Hybrid | SaaS/Hybrid |
| Custo | Altíssimo (ingestão) | Altíssimo (licença) | Alto | Médio (infra) | Baixo | Baixo | Altíssimo | Alto | Alto |
| Normalização | ASIM | CIM | nativa | ECS | decoders | extractors | UDM | própria | própria |
| Busca | KQL | SPL | AQL | KQL/Lucene | Lucene | Lucene | entity | entidade | Spotter |
| Correlação | KQL rules | correlation | rules+magnitude | EQL/threshold | simples | limitada | YARA-L | UEBA | policies |
| MITRE ATT&CK | ✅ | ✅ | ✅ | ✅ forte | ✅ | ❌ | ✅ | ✅ | ✅ |
| Investigação | Graph | drill-down | offense | Timeline | módulo | busca | entity-centric | timeline | workspace |
| Incidente | ✅ | ✅ | ✅ Offense | Cases | ❌ | ❌ | ✅ | ✅ | ✅ |
| UEBA | ✅ | ✅ | ✅ | ✅ ML | ❌ | ❌ | ✅ | ✅ forte | ✅ forte |
| UX moderna | ✅ | 🟡 | 🟡 | ✅ | 🟡 | ✅ | ✅ | ✅ | ✅ |
| Open source | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Escala | altíssima | alta | alta | alta | média | média | altíssima | alta | alta |

## Conclusões e lições para o EDY SIEM

### O que o mercado converge (adotar)
1. **Modelo canônico de evento** (UDM/CIM/ECS) — normalização forte é base de tudo.
2. **Mapeamento MITRE ATT&CK** em regras de detecção — padrão da indústria.
3. **Incident como agregador de alertas** (Cases/Offense) com ciclo de vida.
4. **Query language própria** para busca (KQL/SPL/AQL) — poder e identidade.
5. **Contexto por entidade** (host, user, IP) em investigação.
6. **Risk scoring por entidade** (Splunk/Securonix) — priorização útil.
7. **Timeline de investigação** como ferramenta central (Elastic/Exabeam).

### O que evitar
1. **Custo por volume de ingestão** (Sentinel/Splunk) — EDY SIEM é autônomo e leve.
2. **Lock-in de nuvem** (Sentinel/Chronicle) — portabilidade.
3. **UX densa e datada** (QRadar) — clareza operacional.
4. **Correlação frágil** (Graylog/Wazuh) — motor de correlação sério com janelas.
5. **Complexidade de operação** (Elastic cluster) — execução simples na v1.

### Direcionamentos para o EDY SIEM
- **Normalização canônica** no coração (`CanonicalEvent`).
- **Regras declarativas com MITRE** (ADR-004).
- **Incident workspace** com timeline, evidências e ações.
- **Busca própria** (query language leve, SQL-like) sobre o modelo canônico.
- **Entity-centric** na investigação (host/user/IP como primeiro contexto).
- **Risk score por entidade** acumulado.
- **Autônomo e leve**: SQLite → Protocol → storage escalável quando necessário.
- **Didático**: cada decisão acima documentada em `docs/product/study-guide.md`.

> Regra: **inspirar-se, nunca copiar.** O EDY SIEM tem identidade própria.





