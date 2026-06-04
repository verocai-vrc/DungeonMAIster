# DungeonMAIster - Lista Exaustiva de Funcionalidades (To-Do)
## Misc Functionalities
- [] Hardcoded DND 5e ruleset for the AI to consult: rules, item and descriptions, classes and races, spells, etc
- [] Ruleset selection dropdown menu (future versions)
- [] Display current memorized module in the system page after ingestion
- [] persistent campaign save feature to continue games
= [] 

### Fase 1: Fundação e Infraestrutura Base
- [ ] Configurar o servidor backend principal (FastAPI).
- [ ] Estabelecer conexão bidirecional em tempo real (WebSockets) entre cliente e servidor.
- [ ] Criar a interface de utilizador (HTML/JS/Tailwind CSS) dividida em painéis (Chat à esquerda, Ficha/Mecânicas à direita).
- [ ] Implementar a lógica estrutural da classe `AIGameMaster` para receção e devolução de mensagens no chat.
- [ ] Criar sistema de identificação de estado da conexão WebSocket no frontend (Conectado/Desconectado).
- [ ] Construir o loop de data flow (Frontend envia ação -> Backend processa -> RAG atua -> IA decide -> Execução de ferramentas -> Retorno ao Frontend).

### Fase 2: Motor RAG e Cérebro do Mestre
- [ ] Implementar integração com LLM local usando o Ollama (ex: Llama3).
- [ ] Criar script (ingest.py) para leitura e ingestão de módulos de aventuras e manuais de regras em PDF.
- [ ] Segmentar os textos dos PDFs em "chunks" (fragmentos menores e indexáveis).
- [ ] Gerar embeddings usando `HuggingFaceEmbeddings` e armazenar numa base de dados vetorial local (ChromaDB).
- [ ] Configurar o sistema (Retriever) para recuperar dinamicamente o contexto do RAG antes da IA formular as respostas.
- [ ] Criar a funcionalidade para o utilizador fazer upload de novos módulos PDF em tempo real pela aba de "Sistema" na UI.
- [ ] Injetar, no prompt base da IA, regras rígidas "anti-gaslight" (o jogador não pode inventar itens/magias que não estão na ficha).

### Fase 3: Ficha de Personagem e Matemática D&D 5e
- [ ] Criar os modelos de dados (estruturas JSON/Pydantic) para a ficha (Nome, Raça, Classe, HP, CA, Atributos, etc).
- [ ] Implementar lógica hardcoded para cálculo automático dos modificadores de atributos (ex: Mod = floor((Valor - 10) / 2)).
- [ ] Implementar lógica de cálculo de HP máximo baseado na classe, nível e modificador de constituição.
- [ ] Implementar cálculo da Classe de Armadura (CA) com base em armaduras, escudos e destreza equipados.
- [ ] Carregar no frontend as regras do jogo estruturadas (banco de Raças, Classes, Equipamentos, Magias e Habilidades).
- [ ] Criar a janela modal para criação e edição da Ficha de Personagem.
- [ ] Automatizar a injeção de habilidades e proficiências na ficha com base na classe, raça e nível escolhidos.
- [ ] Exibir separadores organizados para Ficha, Inventário e Sistema.
- [ ] Desenvolver "Tooltips" dinâmicos no inventário e magias que exibam as descrições/dados de dano ao passar o rato (hover).

### Fase 4: Motor de Rolagem de Dados e Sistema d20
- [ ] Implementar no backend um interpretador/motor de dados que consiga rolar expressões matemáticas (ex: `1d20+3`).
- [ ] Processar comandos nativos de dados enviados pelo jogador no chat (ex: `/roll 1d20`).
- [ ] Processar intenções narrativas conjuntas à rolagem do jogador (ex: `/rollFOR Tento empurrar a porta`).
- [ ] Criar botões visuais rápidos na ficha de personagem ("Quick Roll") para testar os atributos.
- [ ] Implementar rotina para que o Mestre IA possa solicitar rolagens de risco através da tag `[REQUEST_ROLL]`.
- [ ] Converter a solicitação de teste do Mestre numa interface visual (botões) para o jogador escolher a perícia/atributo a usar.
- [ ] Enviar os resultados exatos dos dados rolados pelo jogador diretamente para a narrativa do Mestre IA processar e narrar.

### Fase 5: Gestão de Memória e Histórico
- [ ] Implementar Memória de Curto Prazo (contexto injetado com as últimas N mensagens trocadas).
- [ ] Implementar comando `/compact` para encerrar sessões, solicitando à IA para resumir o histórico de chat ativo.
- [ ] Implementar Memória Episódica, injetando o resumo das sessões anteriores continuamente na mente da IA.
- [ ] Implementar sistema de "Lore" e Memória Semântica (comandos `/lore add` e `/lore clear`) para fixar fatos inalteráveis.
- [ ] Garantir que todas as camadas de memória são guardadas e carregadas via ficheiros `JSON` (Saves da Campanha).

### Fase 6: Automação do Mestre (Tags e Tool Calling)
- [ ] **Modificação de HP:** IA usar `[MODIFY_HP:-X]` para dano e `[MODIFY_HP:+X]` para cura, refletindo visualmente no chat e salvando na ficha.
- [ ] **Deslocamento:** IA usar `[CHANGE_LOCATION:Local]` para alterar a localização atual, melhorando as buscas RAG (context awareness).
- [ ] **Ganho de Experiência:** IA usar `[ADD_XP:X]` para distribuir XP e automatizar sistema de Level Up caso alcance o limite tabelado.
- [ ] **Inventário Automático:** IA usar `[ADD_ITEM:Item]` para depositar saques/loot da narrativa diretamente no inventário (JSON) do jogador.
- [ ] **Gestão de Combate:** IA usar `[START_COMBAT:Inimigos]` para rolar iniciativas e organizar a ordem de turnos de forma automatizada.
- [ ] **Fim de Combate:** IA usar `[END_COMBAT]` para desativar o estado de batalha.
- [ ] **Diálogos (NPCs):** IA usar tags `[NPC:Nome]Falas[/NPC]` para gerar balões de conversação visualmente destacados no chat.
- [ ] **Gestão de Recursos:** IA usar `[USE_RESOURCE:Nome]` para abater recursos limitados da classe do jogador (ex: Fúria, Canalizar Divindade) e validá-los.
- [ ] **Gestão de Espaços de Magia:** IA usar `[USE_SPELL_SLOT:Nível]` para abater e validar o uso de magias de acordo com os slots da ficha.
- [ ] **Economia de Ação em Combate:** IA validar estritamente o uso de Ação Principal, Ação Bônus e Reações (`[USE_ACTION:main]`, etc.).
- [ ] **Gestão de Turnos:** IA usar `[RESET_TURN]` para devolver a economia de ação ao jogador quando um novo turno começa.
- [ ] **Descansos e Recuperação:** IA usar `[RESTORE_ALL]` aquando de um Descanso Longo para recarregar HP, magias e recursos ao máximo.

### Fase 7: Meta-Comandos de Utilizador
- [ ] Implementar ecrã de ajuda ou comando genérico `/help` para listar os comandos.
- [ ] Implementar atalhos de chat para o jogador forçar as ações e rolamentos (ex: enter submeter o chat).