# EDY SIEM — Project Manifesto

> Documento fundador. Define o **caráter** do produto: o que é, o que não é,
> o que valorizamos e como medimos sucesso.
> Este é o contrato moral do projeto — todo desenvolvimento deve honrá-lo.

---

## 1. O que é

O EDY SIEM é uma **plataforma profissional de Security Information and Event Management (SIEM)**
desenvolvida como produto Enterprise: com arquitetura sustentável, documentação impecável,
segurança por padrão e experiência de usuário digna de software comercial.

Não é um projeto de faculdade. Não é um exercício de portfólio com aparência de produto —
é um produto com **qualidade de engenharia real**, que poderia existir comercialmente.

## 2. Missão

Capacitar times de segurança — pequenos ou em formação — com uma plataforma SIEM
**autônoma, didática e bem arquitetada**, que permita monitorar, detectar, investigar e
responder a ameaças com clareza e eficiência, sem depender de nuvem obrigatória ou
licenças caras.

## 3. Visão

Ser reconhecida como uma plataforma SIEM open source de referência para equipes de
Blue Team e para a formação de profissionais de SOC — provando que qualidade Enterprise
não exige infraestrutura pesada, e que um produto pode ser ao mesmo tempo **profissional,
extensível e profundamente didático**.

## 4. Valores

| Valor | Significado prático |
|---|---|
| **Arquitetura antes de velocidade** | Nenhuma funcionalidade sem arquitetura aprovada (Regra Nº 1) |
| **Qualidade de engenharia** | Código tipado, testado, documentado, responsabilidade única |
| **Segurança por padrão** | Segurança não é feature, é requisito base |
| **Experiência operacional** | Cada tela responde: o quê, onde, risco, quem, ação |
| **Documentação impecável** | Sem código sem docs; sem docs sem feature |
| **Sustentabilidade** | Decisões pensadas para "daqui a um ano" |
| **Didática real** | O produto ensina; o aprendizado é parte do valor |

## 5. O que não é

- Não é uma cópia de Sentinel, Splunk, Elastic ou QRadar.
- Não é um wrapper de ferramentas prontas.
- Não é uma coleção de scripts.
- Não é um projeto onde "funciona na minha máquina" é aceitável.
- Não é um projeto onde a velocidade vence a arquitetura.

## 3. Para quem existe

- **Analistas de SOC** que precisam de clareza, contexto e ação rápida.
- **Engenheiros de detecção** que precisam de regras testáveis e auditáveis.
- **Equipes pequenas** que precisam de um SIEM autônomo e extensível.
- **Estudantes sérios** que querem aprender como um SIEM real é construído.
- **Profissionais** que querem demonstrar engenharia de verdade no mercado.

## 4. O problema que resolve

Organizações pequenas e profissionais em formação não têm acesso a plataformas SIEM
que sejam ao mesmo tempo:

- **Autônomas** — sem nuvem obrigatória, licença cara ou agentes proprietários.
- **Didáticas** — onde cada módulo ensina um conceito real de SOC.
- **Extensíveis** — com contratos claros para coletores, regras e plugins.
- **Bem projetadas** — capazes de evoluir por anos sem retrabalho.

O EDY SIEM entrega isso sem sacrificar qualidade de engenharia.

## 5. Nossos valores

| Valor | Significado prático |
|---|---|
| **Arquitetura antes de velocidade** | Nenhuma funcionalidade sem arquitetura aprovada (Regra Nº 1) |
| **Qualidade de engenharia** | Código tipado, testado, documentado, responsabilidade única |
| **Segurança por padrão** | Segurança não é feature, é requisito base |
| **Experiência operacional** | Cada tela responde: o quê, onde, risco, quem, ação |
| **Documentação impecável** | Sem código sem docs; sem docs sem feature |
| **Sustentabilidade** | Decisões pensadas para "daqui a um ano" |
| **Didática real** | O produto ensina; o aprendizado é parte do valor |

## 6. Princípios de engenharia

- **Clean Architecture** com dependências apontando para o domínio.
- **SOLID, KISS, DRY, YAGNI.**
- **Baixo acoplamento, alta coesão, responsabilidade única.**
- **Código autodocumentado** — nomes claros, tipos fortes.
- **Zero gambiarra, zero duplicação, zero dependências desnecessárias.**
- **Testes como parte do produto**, não como formalidade.
- **ADR para toda decisão arquitetural** (ver `docs/architecture/decisions.md`).

## 7. Experiência do produto

Cada tela, cada fluxo e cada resposta da API deve responder:

| Pergunta | Resposta |
|---|---|
| O que aconteceu? | Evento/alerta com descrição e severidade |
| Onde aconteceu? | Host, fonte, entidade afetada |
| Qual o risco? | Score de risco e MITRE ATT&CK |
| Quem está envolvido? | Usuário, processo, IP, asset |
| Qual ação devo tomar? | Triagem, resposta, investigação |

Nenhuma tela existe por estética. **Tudo tem propósito operacional.**

## 8. Como medimos sucesso

- **Técnico:** arquitetura limpa, CI verde (pytest, mypy strict, ruff, coverage ≥ 85%),
  zero dívida consciente não registrada.
- **Produto:** fluxo SOC completo operacional: ingerir → normalizar → correlacionar →
  detectar → incidente → investigar → documentar.
- **Usuário:** um analista consegue usar sem manual e explicar o que viu.
- **Didático:** um estudante consegue aprender um conceito de SIEM em cada módulo.
- **Comercial:** o repositório poderia ser apresentado como produto em entrevista ou venda.

## 9. Critério transversal de decisão

Toda decisão técnica, de produto ou de UX deve responder:
> **Como esta decisão afeta a manutenção, a escalabilidade e a experiência do usuário
> daqui a um ano?**

Se a resposta não for positiva, a decisão precisa ser repensada.

## 10. Compromisso

Nós construímos o EDY SIEM com a seriedade de quem entrega software para produção.
Não aceitamos atalhos que comprometam a arquitetura.
Não publicamos código sem documentação.
Não criamos interface sem UX definida.
Não criamos API sem contrato.
Não criamos módulo sem responsabilidade única.

**Qualidade de arquitetura antes de velocidade. Sempre.**

---

*Assinado: EDY SIEM — fundação, 2026.*
