# Roadmap da versão 2.0

Cada sprint entrega algo jogável ou executável e testável. Os tickets `DM-N` são detalhados quando a sprint começa (ver `docs/design/dungeon-meister-2.0.md`, seção "Processo de implementação").

| Sprint | Submarco | Tickets | Entregável |
| --- | --- | --- | --- |
| S0 Fundação | n/a | DM-1 a DM-3 | Repo 2.0, CI verde, `meister roll` e `meister check` reproduzíveis por seed |
| S1 Combate abstrato | 1 (fecha) | DM-4 a DM-7 | Guerreiro nv. 2 vs goblins no console, sem grid, com seed, save e replay |
| S2 Grid e movimento | 2 | DM-8 a DM-10 | Combate no grid ASCII com movimento, ataques de oportunidade e os 5 monstros |
| S3 Magias e efeitos | 2 | DM-11 a DM-13 | Mago (nv. 1 a 5 por depuração) com as 6 magias, áreas e Shield |
| S4 IA tática e simulação | 2 (fecha) | DM-14 a DM-16 | Aliado e inimigos pela IA de utilidade; `meister sim` com estatísticas |
| S5 Conteúdo e validador | 3 | DM-17 a DM-19 | Formato canônico, JSON Schema, `meister validate`, one-shot válida |
| S6 Exploração e diálogo | 3 | DM-20 a DM-22 | One-shot jogável de ponta a ponta no console |
| S7 Oráculo e cadeia | 3 | DM-23 e DM-24 | **Critério de conclusão da 2.0**: encontro do oráculo resolvido pelo motor, reproduzível e testado |
| S8 Progressão | 3 (fecha) | DM-25 e DM-26 | XP e níveis 2 a 5 de guerreiro e mago |
| S9 TUI | 4 | DM-27 a DM-29 | Aventura completa jogável na TUI ratatui |
| S10 Fechamento | 4 (fecha) | DM-30 a DM-32 | Simulação na TUI, relatório pós-partida, replay, release `v2.0.0` |

## Escopo resumido dos tickets

**S0**
- DM-1 Repositório 2.0: tag `v1.0.0`, remoção do Python, workspace Cargo, licenças, CI.
- DM-2 `meister-dice`: RNG com seed e fluxos, expressões de dados, probabilidades, `meister roll`.
- DM-3 Fundamentos de `meister-rules`: atributos, perícias, CDs, checagens, `meister check`.

**S1**
- DM-4 `meister-srd`: vendorizar o 5e-database, tipos espelho, conversão do goblin e do equipamento, ficha do guerreiro nv. 2 em TOML.
- DM-5 Núcleo de combate: criaturas, iniciativa, turnos, economia de ações, ataque, dano, morte, Second Wind, Action Surge, `prompt()`/`submit()` com pilha derivada, opções válidas.
- DM-6 `meister-game` e `meister-tactics`: envelope de eventos, save JSONL versionado, load por fold, replay, controladores humano, IA simples e roteiro.
- DM-7 `meister-narration` e console: `meister console --seed N --vs goblin:3`, `meister replay`, cenário com insta.

**S2**
- DM-8 Geometria: células, distância configurável, terreno, alcance, linha de visão, cobertura, mapa ASCII.
- DM-9 Movimento em combate: célula a célula, ataque de oportunidade, Dash, Disengage, Dodge.
- DM-10 Esqueleto, lobo, orc e ogro.

**S3**
- DM-11 Sistema de efeitos: ataque, dano, cura, resistência, condição com duração, bônus de CA, concentração.
- DM-12 Gabaritos de área (esfera, cone, linha, cubo) e fogo amigo.
- DM-13 Mago: conjuração, espaços, as 6 magias em TOML, Shield como reação, construtor nv. 1 a 5.

**S4**
- DM-14 `ObservedView` e núcleo de utilidade com ruído pela seed e detalhamento das notas.
- DM-15 Perfis dos 5 monstros e do mago aliado, moral, coordenação de grupo.
- DM-16 `meister sim` e testes estatísticos.

**S5**
- DM-17 `meister-content`: formato canônico, versão de esquema, migrações, `meister schema`.
- DM-18 `meister validate`: referências, alcançabilidade, aventura concluível, orçamento de XP.
- DM-19 One-shot de exemplo sob CC-BY 4.0.

**S6**
- DM-20 Exploração: tela de cena, Percepção passiva, custo de tempo, descansos.
- DM-21 Diálogo por tópicos e pontos de interesse.
- DM-22 Transição exploração e combate, surpresa, playthroughs testados.

**S7**
- DM-23 `meister-oracle`: sim/não, eventos aleatórios, pares de significado, tensão.
- DM-24 Cadeia completa (encontro, dificuldade, orçamento, monstros, loot, combate).

**S8**
- DM-25 XP por combate, marcos e descoberta.
- DM-26 Níveis até o 5 de guerreiro (Campeão) e mago (até Fireball).

**S9**
- DM-27 Base da TUI.
- DM-28 Tela de combate.
- DM-29 Telas de cena, diálogo, mapa, ficha, save/load e oráculo.

**S10**
- DM-30 Simulação operada pela TUI.
- DM-31 Relatório pós-partida e visualizador de replay.
- DM-32 Polimento, guia de autoria, README e release `v2.0.0`.
