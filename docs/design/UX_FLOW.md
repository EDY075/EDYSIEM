# EDY SIEM — UX Flow

> Fluxos de interação detalhados, tela por tela. Foco em **o que acontece em cada clique**
> e **estados possíveis**. Complementa `UX_ARCHITECTURE.md` e `WIREFRAMES.md`.

## Fluxo A — Triagem de Alerta

```mermaid
flowchart TD
    A[Abrir /alerts] --> B[Filtro padrão: críticos+altos 24h]
    B --> C[Lista carregada com skeleton]
    C --> D[Clicar alerta]
    D --> E[Drawer abre: resumo + evidências + timeline + ações]
    E --> F{Decisão}
    F -->|Falso positivo| G[Resolve]
    F -->|Real| H[ACK + Investigar]
    F -->|Alto impacto| I[Escalar p/ Incidente]
    G --> J[Toast: estado atualizado + badge atualiza]
    H --> J
    I --> J
```

**Estados possíveis no Drawer:** carregando (skeleton) → carregado → erro (retry).
**Feedback:** toast em toda ação; lista re-renderiza; badge de status atualiza.

## Fluxo B — Investigação por Entidade

```mermaid
flowchart TD
    A[Drawer de Alerta] --> B[Clicar entidade host/user/IP]
    B --> C[Timeline de entidade carrega]
    C --> D[Eventos relacionados listados]
    D --> E{Padrão malicioso?}
    E -->|Sim| F[Marcar evidências + anotar]
    E -->|Não| G[Fechar]
    F --> H[Criar Incidente + Exportar]
    H --> I[Toast + navega p/ Incidentes]
```

**Regra:** entidade clicável em qualquer drawer/tabela leva ao contexto da entidade.

## Fluxo C — Ciclo de Incidente

```mermaid
flowchart LR
    A[OPEN] -->|Iniciar análise| B[INVESTIGATING]
    B -->|Encerrar| C[RESOLVED]
    B -->|Sem evidência| D[FALSE_POSITIVE]
    C -->|Reabrir| A
    D -->|Reabrir| A
```

**Transições:** cada mudança registra auditoria (quem/quando/nota) e atualiza timeline.

## Fluxo D — Criação de Regra

```mermaid
flowchart TD
    A[/rules Nova Regra/] --> B[Form: nome, severidade, MITRE, condição, timeframe]
    B --> C{Schema válido?}
    C -->|Não| D[Erro inline no campo]
    C -->|Sim| E[Botão Testar]
    E --> F[Executa contra eventos de exemplo]
    F --> G{Alertas esperados?}
    G -->|Não| H[Ajusta condição]
    G -->|Sim| I[Salvar enabled]
    I --> J[Toast + regra ativa]
```

**Regra:** "testar" é obrigatório antes de publicar regra nova.

## Fluxo E — Hunting

```mermaid
flowchart TD
    A[/hunting/] --> B[Escolher técnica MITRE]
    B --> C[Query sugerida pré-preenchida]
    C --> D[Executar]
    D --> E[Timeline de resultados]
    E --> F{Achou?}
    F -->|Sim| G[Promover a Incidente]
    F -->|Não| H[Ajustar query / nova técnica]
```

## Regras transversais de fluxo

1. **Carregamento:** sempre skeleton no primeiro render; refresh silencioso preserva dados.
2. **Erro:** mensagem clara + retry; nunca tela vazia sem explicação.
3. **Vazio:** orientação de próxima ação.
4. **Ação em lote:** confirmação quando > 5 itens ou destrutiva.
5. **Navegação interna:** filtros/estado preservados (nunca recarrega perde contexto).
6. **Acessibilidade:** ESC fecha sobreposições; teclado navega; foco retorna ao gatilho.
