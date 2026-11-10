# Dungeon Meister: Diagnóstico e Plano de Reestruturação

> Versão consolidada em 2026-11-09. Decisões da sessão de planejamento estão no "Registro de decisões" ao final; o cronograma está em `roadmap.md`.

## Contexto

O Dungeon Meister é um motor de RPG de mesa solo para D&D 5e, concebido para testar aventuras, settings e encontros sem a necessidade de um grupo. A versão atual, em Python (FastAPI, WebSocket, ChromaDB e Llama 3 via Ollama), passa a ser tratada como prova de conceito. A nova versão será reescrita em Rust, com inspiração conceitual em Baldur's Gate 3: as regras são inteiramente resolvidas pelo sistema, e a narrativa se apoia sobre essa base.

## Princípio central

Na versão atual, o LLM atua como árbitro do jogo, e o código apenas executa o que ele determina. A nova arquitetura inverte esse controle: o motor decide, e a IA apenas interpreta e narra. O jogador mantém a liberdade de tentar qualquer ação, mas perde a autoridade sobre o resultado, que pertence ao sistema.

**Prioridade atual:** fazer o motor solo funcionar, com o modo Oráculo e combate resolvido em código. O modo Dungeon Master com IA, que dá nome ao projeto, passa a ser uma etapa futura.

## Diagnóstico da versão atual

### Vazamento de spoilers pelo RAG

O retriever busca os três trechos semanticamente mais próximos da mensagem do jogador, sem filtro de local, embora o documento de design preveja esse filtro. Uma pergunta sobre a fraqueza do vilão recupera exatamente o trecho que a responde, de modo que o próprio sistema entrega o segredo ao modelo.

### Tags sem validação

As tags emitidas pelo LLM são executadas sem verificação: ADD\_ITEM aceita itens inexistentes no catálogo, ADD\_XP aceita qualquer valor e MODIFY\_HP não possui limites coerentes com as regras. Quem convence o modelo controla a ficha.

### Dados trapaceáveis

O comando de rolagem aceita qualquer expressão, inclusive modificadores arbitrários. O resultado é repassado ao modelo como texto simples, o que permite ao jogador digitar um resultado sem rolar. Além disso, não há CD calculada pelo código, e a decisão de sucesso fica a cargo do LLM.

### Ausência de loop de turnos

Inimigos não possuem ficha, e o avanço do turno depende do modelo. Por consequência, o jogador consegue agir indefinidamente, e os demais personagens raramente agem.

### Problemas menores

- Inconsistência de caminhos entre data\_manager.py (data/) e ingest.py (DATA/), que quebra em sistemas sensíveis a maiúsculas.
- Dados duplicados entre abilities.json, rules.json e os demais arquivos de regras.
- Processamento síncrono do LLM dentro do handler do WebSocket.
- Saída do LLM inserida no frontend via innerHTML sem sanitização.

## Arquitetura proposta

### Motor como máquina de estados

O jogo passa a ser governado por estados explícitos (exploração, diálogo e combate), com turnos, CDs e fichas de monstros resolvidos inteiramente em código.

### Ingestão estruturada no lugar de RAG em tempo de jogo

O módulo de aventura é convertido previamente em dados estruturados: locais, NPCs, o conhecimento de cada NPC, pistas e segredos condicionados a gatilhos. Um LLM pode auxiliar nessa extração offline, sempre com revisão humana. Durante a partida, cada NPC recebe apenas o próprio conjunto de conhecimento, o que torna o vazamento de segredos estruturalmente impossível.

### Papéis restritos para o LLM

- Entrada: traduzir o texto livre do jogador para uma ação pertencente a um conjunto fechado (atacar, persuadir, perguntar\_sobre etc.), posteriormente validada pelo código.
- Saída: narrar um resultado previamente decidido pelo motor.

## Escolha de linguagem: Rust

Rust foi escolhido por afinidade e interesse de aprendizado, por ser também a linguagem do Abstract-Tex e por oferecer desempenho e confiabilidade. Enums com pattern matching permitem modelar estados e ações de forma que o compilador rejeite transições inválidas, como atacar fora de combate ou gastar uma ação já utilizada. Alternativas consideradas e descartadas: TypeScript, mais pragmático e menos rígido, e C# com Godot, que ampliaria o escopo para um jogo completo, fora da ambição do projeto.

## Estrutura do workspace Cargo

1. **Crate de regras.** Núcleo puro, sem entrada e saída nem IA: fichas, dados, checagens, combate e turnos.
2. **Crate de conteúdo.** Formato do módulo (locais, NPCs, conhecimento e gatilhos), serializado com serde em TOML ou RON para facilitar a leitura e a edição manual.
3. **Crate de narração.** Uma trait implementável por um adaptador do Ollama, por um narrador de texto fixo ou por nenhum narrador, de modo que o jogo funcione mesmo sem IA.
4. **Interface.** Definida por último, no formato mais adequado.

O motor de regras, por ser uma biblioteca pura, pode ser testado integralmente com testes automatizados, sem nenhum modelo em execução.

## Recursos de destaque

- **RNG com seed:** partidas reproduzíveis, o que facilita testes e depuração.
- **Modo de simulação:** execução de um mesmo encontro milhares de vezes para estimar a letalidade e calibrar aventuras, recurso útil para mestres e de forte apelo no portfólio.
- **Dados do SRD 5.1:** licenciados sob CC-BY 4.0, podem substituir os JSONs incompletos atuais por um conjunto completo e legalmente publicável.

## Modos de jogo

O software terá dois modos sobre o mesmo motor: Dungeon Master, padrão, e Oráculo, alternativo. O modo Oráculo será implementado primeiro e servirá como prova de conceito do motor antes de qualquer integração com IA.

### Contrato comum

Ambos os modos implementam a mesma trait de mestre, que responde a perguntas e reage a resultados. O oráculo é a primeira implementação, totalmente determinística e testável por seed. A IA entrará depois pela mesma interface e poderá consultar o oráculo em vez de decidir sozinha, de modo que a imprevisibilidade venha das tabelas e o modelo apenas dê forma narrativa ao resultado.

### Funções do oráculo

- Respostas de sim ou não com probabilidades ajustáveis.
- Eventos aleatórios e sugestões de significado por pares de palavras.
- Estado de cena mantido pelo motor, no estilo do fator de caos do Mythic, e não pela memória da IA.

### Cadeia de geração hard-coded

Os resultados do oráculo alimentam cálculos fixos do motor, em sequência:

1. O oráculo determina que ocorre um encontro.
2. O valor rolado define a dificuldade do encontro.
3. O motor consulta o tamanho e o nível do grupo e calcula, pelas regras de orçamento de XP, quais monstros compõem um encontro justo. O SRD 5.1 não traz as tabelas de limiares de encontro (são do guia do mestre de 2014); a 2.0 usa a tabela "XP Budget per Character" do SRD 5.2.1 (CC-BY 4.0, baixa/moderada/alta por nível do grupo).
4. Outra tabela define o loot correspondente.

Essa cadeia exercita fichas de monstros, cálculo de dificuldade e tabelas de conteúdo, servindo como bateria de testes do motor. O oráculo é um crate separado (`meister-oracle`), e a cadeia que o liga às regras e ao catálogo fica em `meister-game`.

### Referências e licenças

- **Ironsworn:** oráculos sob CC-BY 4.0, reutilizáveis com atribuição.
- **Mythic GM Emulator:** comercial, serve apenas como referência conceitual; suas tabelas não podem ser copiadas.
- **Oráculo brasileiro citado (Risdan):** ponto de partida para sim ou não e probabilidade de encontros; confirmar nome exato, autor e licença.
- **Tabelas próprias:** escritas no formato de conteúdo do projeto.

## Base de regras

O motor adotará o SRD 5.1 (regras de 2014), por já existir em JSON estruturado no projeto 5e-database e por ser a mesma base conceitual de Baldur's Gate 3. O SRD está sob CC-BY 4.0, que permite inclusive uso comercial mediante atribuição.

### Importação

Os JSONs do 5e-database (monstros, magias, itens, classes e raças) serão importados com serde, dispensando a conversão manual do PDF. A arquitetura deve permitir a adoção futura do SRD 5.2 (regras de 2024) sem reescrever o motor.

### Separação entre dados e comportamento

- **Dados:** atributos, fichas de monstros, estatísticas de itens e tabelas entram diretamente do JSON.
- **Comportamento:** o que magias e habilidades fazem exige código, organizado como um sistema de efeitos composto por blocos (dano, cura, teste de resistência, condição, duração).

Cada magia passa a ser uma combinação desses blocos descrita em dados, e o motor apenas executa os blocos, evitando uma função específica por magia.

### Pendências: resolvidas

- **Licença do 5e-database:** o repositório `5e-bits/5e-database` foi arquivado e incorporado ao monorepo `5e-bits/5e-srd-api` (`packages/5e-database/src/2014/en`, 24 arquivos `5e-SRD-*.json`). O código é MIT; o conteúdo do SRD 5.1 é CC-BY 4.0 da Wizards. Os JSONs são vendorizados em `data/srd/5.1/` em commit fixo, com a licença MIT do 5e-bits e o aviso do SRD.
- **Completude dos efeitos:** dano (`damage_at_slot_level`), CD, área, concentração e duração vêm estruturados. Ficam só em prosa a paralisia do Hold Person, a contagem de dardos do Magic Missile, o +5 de CA do Shield e o alcance das ações dos monstros. Os blocos de efeito são escritos à mão em `data/rules/` e conferidos por teste contra o JSON.
- **Recorte inicial:** definido na seção Primeiro marco.

## Primeiro marco

O primeiro marco corresponde à versão 2.0, numerada assim por ser uma reformulação total da versão já publicada, e entrega uma versão jogável desde a primeira execução, com uma classe marcial, uma classe conjuradora e um pequeno conjunto de monstros, suficiente para rodar a cadeia do oráculo de ponta a ponta.

### Classes

- **Guerreiro:** valida ataques, ação bônus (Second Wind) e recursos por descanso (Action Surge).
- **Mago:** valida espaços de magia, truques e o sistema de efeitos.

### Magias escolhidas para cobrir os blocos de efeito

| Magia | Círculo | Bloco exercitado |
| --- | --- | --- |
| Fire Bolt | Truque | Jogada de ataque |
| Magic Missile | 1 | Dano automático, múltiplos alvos |
| Burning Hands | 1 | Teste de resistência em cone, metade do dano no sucesso |
| Shield | 1 | Reação e bônus temporário de CA |
| Hold Person | 2 | Condição com duração e concentração |
| Fireball | 3 | Área esférica a distância, teste de resistência, risco de atingir aliados no grid |

### Monstros

Cinco monstros do SRD com faixas de CR variadas, por exemplo goblin, esqueleto, lobo, orc e ogro, para testar o orçamento de XP e o cálculo de dificuldade.

### Critério de conclusão

Um combate completo entre o grupo e um encontro gerado pelo oráculo, resolvido inteiramente pelo motor, reproduzível por seed e coberto por testes automatizados.

### Escopo positivo da versão 2.0: decidido

1. **Regras:** atributos, testes de perícia e resistência, ataques, dano, CA, condições, descansos curto e longo, níveis 1 a 5 de guerreiro e mago.
2. **Sistema de efeitos:** blocos de dano, cura, teste de resistência, condição, duração e concentração, cobrindo as cinco magias escolhidas.
3. **Combate em grid:** iniciativa, economia de ações, movimento, ataques de oportunidade, gabaritos de área, linha de visão e cobertura.
4. **IA tática:** pontuação de utilidade e perfis de comportamento para os cinco monstros.
5. **Oráculo:** sim ou não, eventos aleatórios e a cadeia encontro, dificuldade, orçamento de XP e loot.
6. **Persistência:** log de eventos, seed, save e replay.
7. **Conteúdo:** formato canônico, validador e uma one-shot curta escrita à mão, com poucas cenas e caminhos alternativos, reiterável.
8. **Interface:** TUI com ratatui.
9. **Testes:** cobertura automatizada do crate de regras.

Decisões complementares: o jogador controla um guerreiro pré-gerado de nível 2, acompanhado por um mago aliado de nível 2 controlado pela IA tática, o que valida a mesma IA para aliados e adversários. O XP obtido em encontros e atividades permite subir de nível até o máximo de 5, como prova de conceito da progressão. O mago aliado tem contagem de XP própria e também progride até o nível 5, chegando às magias de terceiro círculo (Fireball). A progressão do guerreiro até o 5 inclui o arquétipo Campeão no nível 3, o aumento de atributo no 4 e o ataque extra no 5. O comportamento de NPCs fora de combate (diálogo e afins) será definido depois. O modo de simulação entra na 2.0 e é operado pela TUI: aventura, perguntas e rolagens do oráculo por texto no terminal, e combates no grid renderizado com ratatui.

## Decisões conceituais

Sete decisões precisam ser fechadas antes da modelagem dos tipos em Rust, para que as IAs de desenvolvimento recebam contexto explícito. Elas serão resolvidas uma a uma nesta sessão.

### 1. Posicionamento no combate: decidido

O combate usará grid; o teatro da mente fica restrito a narração, diálogo e descrição. O grid permite ao jogador planejar táticas e movimento, entender o alcance das magias e verificar se personagens marciais alcançam seus alvos.

Implicações a detalhar:

- Grid quadrado de 5 pés por célula. Toda diagonal conta 5 pés no primeiro marco (regra padrão do livro do jogador), com a regra mantida configurável para adotar depois a variante 5-10-5 do guia do mestre.
- Gabaritos de área (cone, esfera, linha, cubo) projetados sobre células.
- Linha de visão, cobertura, terreno difícil e ataques de oportunidade calculados pelo motor.
- O formato do módulo precisará descrever mapas de combate, e a interface precisará renderizar o grid.

### 2. Composição do grupo: decidido

O jogador controla apenas o próprio personagem. Aliados, demais NPCs e monstros agem por uma IA tática heurística implementada em código, sem LLM. O LLM fica reservado à narração e a funções fora de combate, nunca à tomada de decisão em combate. A IA tática usará pontuação de utilidade: a cada turno, o motor lista as ações possíveis, atribui uma nota a cada uma e escolhe a maior. Perfis de comportamento definidos em dados dão personalidade a cada criatura (o goblin foge quando ferido, o esqueleto luta até o fim, o lobo cerca o alvo com a matilha), sempre de forma reproduzível pela seed.

#### Planejamento da IA tática

O requisito central é que aliados e oponentes não pareçam burros, pois isso quebra a imersão. A IA tática seguirá estes princípios:

- **Considerações de pontuação:** dano esperado (chance de acerto vezes dano médio), potencial de abate de alvos feridos, ameaça representada por cada inimigo, autopreservação, posicionamento (cobertura, evitar ataques de oportunidade) e custo de recursos, para não gastar uma magia forte num alvo trivial.
- **Sofisticação proporcional à inteligência:** um lobo age por instinto e cerca o alvo; um orc prioriza conjuradores; um mago inimigo tenta quebrar a concentração do jogador.
- **Conhecimento limitado:** criaturas decidem com base no que observaram no log de eventos, nunca em informação oculta, como os pontos de vida exatos do jogador.
- **Imperfeição controlada:** ruído aleatório pela seed entre ações de pontuação próxima, para evitar comportamento robótico e previsível.
- **Moral:** fuga ou rendição calculadas a partir dos pontos de vida e das baixas registradas no log.
- **Coordenação de grupo:** um quadro compartilhado entre criaturas aliadas para dividir alvos e evitar que todas façam a mesma coisa.
- **Depuração e calibragem:** cada decisão registra o detalhamento das notas, explicando por que a criatura agiu assim, e o modo de simulação permite ajustar os pesos em milhares de combates.

### 3. Interface do primeiro marco: decidido

O primeiro marco usará uma TUI no terminal com ratatui, suficiente para renderizar o grid e testar a prova de conceito. A interface gráfica definitiva será desenhada depois, a partir de um wireframe próprio.

### 4. Registro de eventos: decidido

Cada ação vira um evento em log, e o estado do jogo é derivado desse log. O save passa a ser a seed mais os eventos, e o replay sai sem custo adicional. O log também serve de memória consultável pelo oráculo e pela IA tática, por exemplo para saber quem já perdeu vida, quem causou dano a quem e quantos aliados caíram.

### 5. Formato do módulo de aventura: decidido

O objetivo de longo prazo é importar aventuras existentes (módulos de fã, expansões do próprio usuário) a partir de PDF ou TXT. A estratégia separa o formato do importador:

- **Formato canônico primeiro:** o motor só entende um formato estruturado próprio (TOML ou RON) com locais, conexões, NPCs, conhecimento por NPC, segredos, gatilhos e mapas de combate. Esse formato é o contrato estável do projeto.
- **Primeiro marco:** uma aventura curta de exemplo escrita à mão nesse formato, com licença livre, para testar o motor de ponta a ponta.
- **Importador como pipeline em etapas, em fase posterior:** extração determinística do texto e da hierarquia de títulos; estruturação heurística (reconhecer blocos de estatísticas, nomes de locais e NPCs); revisão humana obrigatória antes de gerar o arquivo final. A extração assistida por LLM entra nessa etapa apenas depois do motor completo, sempre offline e com revisão.
- **Limite honesto:** sem LLM, a conversão automática de prosa livre em segredos e gatilhos é pouco confiável; a revisão humana não é opcional.
- **Distribuição:** o repositório inclui apenas conteúdo com licença livre; o importador é neutro e opera sobre arquivos fornecidos pelo usuário.

#### Conversão externa assistida por LLM

A conversão de módulos será feita fora do motor, com um prompt versionado no repositório e executado no Claude Code a partir do PDF. O motor permanece livre de LLM em tempo de execução; a IA atua apenas como ferramenta offline de autoria.

- **Esquema como contrato:** o JSON Schema do formato canônico é gerado automaticamente a partir dos tipos Rust (por exemplo, com schemars) e entregue ao prompt.
- **Validador no motor:** um comando de validação verifica o esquema e a integridade semântica: referências existentes, conexões válidas entre locais, segredos ligados a gatilhos alcançáveis e aventura concluível.
- **Ciclo fechado:** o Claude Code executa o validador e corrige o arquivo até que ele passe, sem intervenção manual em cada erro.
- **Revisão humana:** em aberto. O objetivo é jogar módulos desconhecidos sem revisá-los, como um teste cego, cujo valor depende de o jogador não conhecer a aventura, e só ao final ler o módulo original para avaliar o desempenho do motor.
- **Risco de spoiler:** como a revisão humana leria os segredos, as alternativas em estudo são: (a) uma segunda camada de compilação no motor Rust, com tipagem e checagens semânticas mais fortes; (b) um revisor por IA que compara o PDF com o arquivo gerado e emite apenas um relatório sem spoilers, com métricas de cobertura (por exemplo, "18 de 20 NPCs mapeados" ou "todos os encontros presentes"), sem revelar nada da história. Decisão adiada.
- **Aventura de exemplo:** escrita à mão, reiterável e projetada para exercitar diferentes decisões e caminhos.

**Relatório pós-partida (ideia):** ao final, o motor cruza o log de eventos com o conteúdo do módulo e mostra o que o jogador viu, o que perdeu e o que ficou inalcançável por erro de conversão, apoiando a avaliação do playtest contra a leitura do módulo original.

### 6. Fora de escopo da versão 2.0: decidido

Não entram na versão 2.0, ficando para o segundo marco em diante: multiplayer, progressão além do nível 5, geração de imagens, qualquer integração com LLM, o importador de módulos e a interface gráfica.

### 7. Convenções: decidido

- **Idioma:** a versão 2.0 usa apenas inglês, no conteúdo e na interface, por ser o idioma da maioria dos módulos disponíveis. Os textos da interface ficam centralizados em chaves (`data/text/en.toml`) desde o início, para facilitar português e outros idiomas no futuro. Código, comentários, commits e README também em inglês; este documento, o roadmap e os tickets ficam em português.
- **Licença:** código sob licença dupla MIT OR Apache-2.0, convenção do ecossistema Rust (a Apache-2.0 acrescenta proteção de patentes). Os dados do SRD 5.1 permanecem sob CC-BY 4.0, com o aviso de atribuição exigido em `NOTICE.md`, e a one-shot de exemplo pode ser publicada sob CC-BY 4.0. O projeto se descreve como "5E compatible" e não usa nenhuma outra atribuição à Wizards, como o SRD exige.
- **Testes:**
  1. Testes unitários com cargo test.
  2. Testes de propriedade com proptest, verificando invariantes como pontos de vida nunca acima do máximo, economia de ações nunca negativa e estado ao vivo igual ao estado reconstruído do log.
  3. Testes de snapshot com insta: uma seed e um log de eventos fixos devem sempre produzir o mesmo resultado.
  4. Testes de cenário: combates completos roteirizados, como guerreiro e mago contra três goblins.
  5. Testes estatísticos pelo modo de simulação, verificando se taxas de vitória ficam dentro de faixas esperadas; usados para balanceamento, marcados com `#[ignore]` e sem bloquear a integração contínua.
  6. Testes da TUI com o TestBackend do ratatui.

### Pontos adicionais: decididos

1. **Entrada de ações na TUI:** decidido. Menus contextuais inspirados em Baldur's Gate 3, com comandos curtos como atalho. O motor gera a lista de ações válidas, a mesma usada pela IA tática, de modo que nenhuma ação inválida é oferecida. A interface exibe permanentemente os recursos do turno: ação, ação bônus, reação, deslocamento restante, espaços de magia e recursos de classe. Layout em três áreas: grid ao centro, painel de recursos na lateral e menu de ações embaixo. Ao navegar por uma ação, o grid destaca seu alcance ou área e o menu mostra a chance de acerto.
2. **Exploração e diálogo sem IA:** decidido. Diálogo híbrido por tópicos, inspirado em Morrowind, e exploração em pointcrawl. Detalhes na seção Diálogo e exploração.
3. **Versionamento de formatos:** decidido. Todo arquivo de save e de aventura carrega a versão do esquema; quando o formato muda, o motor migra arquivos antigos passo a passo até a versão atual, em vez de recusá-los. Os eventos do log também são versionados, assim como a versão das regras usada na partida, para que um replay antigo reproduza o mesmo resultado mesmo após correções nas regras.

### Diálogo e exploração: decidido

O diálogo usa tópicos condicionados, e não árvores, porque módulos de D&D descrevem o que cada NPC sabe, o que torna os tópicos fáceis de converter e imunes a spoilers por construção.

- **Tópicos como opções:** o menu de conversa lista apenas os assuntos que o NPC conhece e que o jogador já descobriu.
- **Entradas condicionadas:** cada tópico tem várias entradas, e o motor entrega a mais profunda já desbloqueada. Gatilhos: informação prévia (pista descoberta), teste de perícia e atitude do NPC (hostil, indiferente ou amistosa, conforme o guia do mestre).
- **Testes explícitos:** opções como "Persuadir sobre os desaparecimentos (Persuasão, médio)" aparecem no menu, no estilo de Baldur's Gate 3, para que o jogador escolha arriscar.
- **Efeitos das respostas:** abrir tópicos, marcar pistas, alterar a atitude do NPC e desbloquear locais, fazendo a investigação avançar em cadeia.
- **Perguntas não cobertas:** o oráculo responde apenas com cor local, nunca com segredos da trama.
- **Garantia contra spoiler:** se o NPC não possui entrada sobre um assunto, o tópico não existe para ele, e nenhuma insistência do jogador o revela.
- **IA futura:** quando o LLM retornar, apenas dará voz a entradas já liberadas.

Exemplo com o guarda:

1. Perguntado sobre os desaparecimentos, ele só recomenda não andar à noite.
2. Com sucesso em Persuasão, revela luzes no velho moinho e abre o tópico "moinho".
3. Se o jogador já encontrou o símbolo do culto na taverna, o tópico "moinho" ganha uma entrada extra: o guarda reconhece o símbolo e fica nervoso.

A exploração segue um pointcrawl: cenas ligadas por caminhos, com objetos a examinar e perguntas ao oráculo. Os segredos se organizam como uma rede de pistas, com mais de um caminho para cada revelação, para que um teste falho nunca trave a aventura.

### Navegação e interação com o cenário: decidido

Objetos do cenário reutilizam o mecanismo dos tópicos de diálogo: cada ponto de interesse tem entradas condicionadas, e o motor entrega a mais profunda já desbloqueada. Há, portanto, um único sistema para conversar e para examinar.

A tela de cena exibe a descrição no topo e um menu em quatro grupos:

1. **Saídas:** caminhos conhecidos para outras cenas; saídas ocultas só aparecem depois de descobertas.
2. **Pessoas:** NPCs presentes, com sua atitude; selecionar um abre o diálogo por tópicos.
3. **Pontos de interesse:** por exemplo, examinar a lareira ou ler o quadro de avisos, com os testes possíveis indicados.
4. **Ações gerais:** procurar na área, descansar, consultar o oráculo e abrir o mapa.

Regras da exploração:

- **Percepção passiva automática:** ao entrar na cena, o motor compara a Percepção passiva com os elementos ocultos e revela o que seria notado, sem rolagem.
- **Tempo tem custo:** cada ação consome tempo, e o oráculo testa encontros aleatórios conforme o tempo avança, o que desencoraja examinar tudo sem consequência.
- **Testes falhos não se repetem livremente:** nova tentativa só se a situação mudar ou mediante custo alto de tempo.
- **Exibição dos testes:** o menu mostra a perícia e um rótulo de dificuldade, nunca a CD numérica. Os rótulos seguem as faixas do SRD: muito fácil (5), fácil (10), médio (15), difícil (20), muito difícil (25) e quase impossível (30).

O mapa é o pointcrawl exibido como grafo simples na TUI, com cenas visitadas e conhecidas; as demais permanecem ocultas até serem mencionadas ou descobertas.

## Próximos passos

O roadmap de sprints e tickets está em `docs/roadmap.md`. O primeiro passo é a Sprint 0 (DM-1 a DM-3): repositório 2.0, `meister-dice` e fundamentos de regras. Os tipos de combate, o modelo de dados do módulo e os demais itens são aprofundados ao longo das sprints seguintes.

## Reações e janelas de interrupção

Toda ação é resolvida em etapas, e o motor abre janelas de reação entre elas. A decisão entra na 2.0 por ser vital aos testes de combate.

- **Ataque:** declaração, rolagem e verificação de acerto; antes de aplicar o dano, abre-se a janela (Shield reage sabendo que foi atingido).
- **Movimento:** cada célula percorrida é uma etapa; sair do alcance de um inimigo abre a janela do ataque de oportunidade.
- **Implementação:** máquina de estados com pilha de decisões pendentes. O controlador da criatura responde, seja o jogador pela TUI, seja a IA tática pontuando a reação como qualquer ação.
- **Log:** cada etapa vira evento, então o replay reproduz as pausas.
- **Interface:** configuração por reação no estilo BG3 (sempre perguntar, usar automaticamente, nunca usar).

## Progressão e XP

Um único contador de XP por personagem, alimentado por combate e por marcos; o nível sobe ao atingir os limiares do SRD.

- **Combate:** XP dos monstros derrotados, conforme o SRD.
- **Marcos (estilo BG3):** completar quests e objetivos e descobrir locais concedem XP definido pelo módulo.
- **Orçamento do módulo:** o validador soma o XP disponível e avisa se a aventura não alcança o nível pretendido.
- **Depuração:** comando para criar personagens em qualquer nível de 1 a 5, para testes.

## Transição da exploração para o combate

Cada local do módulo pode ter um mapa tático opcional, com posições iniciais das criaturas e terreno.

- **Sem mapa próprio:** o motor usa gabaritos genéricos (corredor, sala, clareira).
- **Surpresa:** resolvida pelo motor antes da iniciativa, com Furtividade contra Percepção passiva, conforme o SRD.

## Autoridade do oráculo em aventuras escritas

O conteúdo do módulo sempre vence; o oráculo só preenche lacunas.

- **Encontros aleatórios:** só em locais e momentos que o módulo marcar como permitidos (estradas, descansos), nunca durante cenas-chave.
- **Tabelas:** cada local pode ter sua própria tabela de encontros; na ausência dela, o oráculo usa a tabela genérica.

## Submarcos da 2.0

A 2.0 é dividida em quatro submarcos, cada um jogável e testável isoladamente.

1. **Combate abstrato no terminal:** guerreiro contra goblins, sem grid, com log de eventos e seed.
2. **Grid e magias:** geometria, áreas, reações e IA tática.
3. **Exploração:** módulo, cenas, diálogo, oráculo e progressão.
4. **Interface completa:** TUI com ratatui, modo de simulação e relatório pós-partida.

## Processo de implementação

Este documento é o handoff para os agentes de IA. O processo adotado é o **agentic-sdlc**: cada sprint do roadmap (`docs/roadmap.md`) se divide em tickets `DM-N`, e cada ticket segue o fluxo `/sdlc-start` → planejamento → geração de tarefas → revisão do plano → implementação com TDD → revisão do código → commits, com um PR por ticket e aprovação humana a cada portão.

- Os tickets ficam em `local-dev/tickets/DM-N/DM-N.md` (local, fora do git). O roadmap é versionado.
- Todo ticket termina com **Pontos de estudo**, ligando o código à seção "Estudo do autor".
- As sprints são planejadas em ondas: o roadmap completo existe desde o início, mas os tickets de cada sprint só são detalhados quando ela começa.

## Estudo do autor

**Teoria antes do código:** ownership e borrowing; lifetimes; traits e genéricos; enums e pattern matching; tratamento de erros com Result; módulos, crates e workspaces Cargo. **Pontos do código a revisar:** o enum de eventos e a derivação do estado a partir do log; a máquina de estados com a pilha de decisões pendentes; a composição do sistema de efeitos; a geração de ações válidas compartilhada por jogador e IA tática; os tipos serde do módulo e o validador; o uso da seed no gerador de números aleatórios.

## Roadmap futuro

As versões seguintes ampliam conteúdo, setting e modos de jogo, sem alterar o escopo da 2.0.

1. **2.5:** mais classes, magias, itens e monstros do SRD; setting e história autocontidos próprios substituem a one-shot de teste.
2. **3.0:** ciclo de cinco dias com reinício, inspirado em Majora's Mask, Outer Wilds e Disco Elysium. Ao fim do quinto dia uma catástrofe devasta o cenário; o reinício é total e só o conhecimento do jogador persiste. A rejogabilidade serve para testar o pointcrawl (objeto do dia 1 que libera encontro ou área no dia 2).
3. **4.0:** ingestão de módulos externos e modo Dungeon Master com IA.
4. **Mais adiante:** multiplayer simples, por exemplo via localhost.

**Preparação na 2.0:** o formato do módulo já inclui relógio do mundo e eventos agendados por horário (por exemplo, NPC presente num local só à noite), sem a mecânica de reinício.

**Ideia narrativa (muito futura):** setting inspirado na Cidadela de As Crônicas de Gelo e Fogo, cidade medieval cientificamente mais avançada, com uma instituição de ensino de mestres, origem do nome Dungeon Meister.


## Registro de decisões (planejamento de 2026-11-09)

1. **Repositório:** mesmo repositório, com a tag `v1.0.0` marcando o último estado em Python (`3e2296c`). A `main` da 2.0 remove o Python e os binários, sem reescrever o histórico.
2. **Processo:** agentic-sdlc, com tickets `DM-N` locais e um PR por ticket.
3. **Crates:** arquitetura por domínio, com crates `meister-*` criados sob demanda (`dice`, `rules`, `srd`, `game`, `tactics`, `narration`, `content`, `oracle` e o binário `meister`). O oráculo é um crate puro, e a cadeia de encontro fica em `meister-game`.
4. **Formatos:** TOML para conteúdo escrito à mão, JSON Lines para saves e logs, JSON original do 5e-database para o SRD.
5. **Orçamento de XP:** tabela do SRD 5.2.1 (ver Cadeia de geração).
6. **Interface:** console de texto, com grid em ASCII a partir da Sprint 2, nos submarcos 1 a 3; TUI com ratatui no submarco 4. O console permanece como ferramenta de depuração.
7. **Simulação:** a versão sem interface (`meister sim`) chega na Sprint 4, junto da IA tática; a operação pela TUI chega no submarco 4.
8. **Determinismo:** ChaCha8 com um fluxo por subsistema (regras, IA, oráculo, mundo); a conversão para dN é implementada no projeto, para não depender de mudanças entre versões do `rand`.
9. **Log:** o resolvedor produz eventos e uma única função aplica cada evento ao estado; carregar um save é refazer o fold, sem rolar dados.
10. **IA tática:** recebe apenas uma visão observada montada a partir do log, nunca o estado completo.

### Adiadas para a sprint correspondente

- **Sprint 2:** regra de inclusão de células nos gabaritos de área; se Esconder e atacante não visto entram na 2.0 (relevante para o Nimble Escape do goblin).
- **Sprint 3:** Sculpt Spells (Escola de Evocação, nível 2 do mago) protege aliados da Fireball e reduz o risco de fogo amigo; Hold Person só afeta humanoides, e a IA precisa respeitar isso.
- **Sprint 5:** autoria da one-shot.
- **Sprint 7:** nome, autor e licença do oráculo brasileiro (Risdan); licença das tabelas Ironsworn no Datasworn.
- **Sprint 8:** pontos de vida ao subir de nível (média fixa ou rolagem).
- **Sprint 9:** i18n com mapa próprio ou Fluent, quando entrar o português.
- **4.0:** revisão humana ou revisor por IA no pipeline de conversão de módulos.