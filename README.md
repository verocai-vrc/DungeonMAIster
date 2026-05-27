# DungeonMAIster - Roadmap e To-Do List

Este documento acompanha o progresso de desenvolvimento do Motor TTRPG com IA (D&D 5e) focado na experiência Solo RPG. As tarefas estão divididas de acordo com as fases de implementação do projeto.

## Fase 1: Fundação do Chat (Comunicação)
- [x] Criar a estrutura básica de diretórios do projeto (`backend`, `frontend`, `data`, `docs`).
- [x] Configurar o servidor FastAPI básico (`backend/main.py`).
- [x] Criar a interface HTML/JS/Tailwind (`frontend/index.html`) com painéis para chat e ficha.
- [x] Estabelecer a conexão via WebSocket entre cliente e servidor.
- [x] Implementar a lógica de "Echo" (O servidor devolve o que o jogador digita para testar a comunicação).
- [x] Criar a classe `AIGameMaster` base para receber e enviar mensagens textuais.

## Fase 2: O Motor RAG (Conhecimento do Mestre)
- [x] Implementar script de ingestão e leitura de PDFs (manuais de regras e aventuras).
- [x] Processar o texto dos PDFs em *chunks* e gerar embeddings.
- [x] Configurar e salvar os embeddings num banco de dados vetorial local (ChromaDB/FAISS) usando metadados.
- [x] Integrar a IA (Ollama/LangChain) para consultar o banco de dados RAG antes de formular respostas.

## Fase 3: Ficha de Personagem e Sistema d20
- [x] Desenhar e criar os modelos de dados (JSON e Pydantic) para a Ficha de Personagem D&D 5e.
- [x] Criar a lógica matemática hardcoded no backend (ex: cálculo automático de modificadores de atributo).
- [x] Implementar o sistema visual no frontend para exibir, atualizar e gerir a aba da Ficha e de Inventário.
- [x] Desenvolver o "Motor de Dados" bidirecional para rolagem de jogador e validação.
- [x] Configurar o tratamento da tag oculta `[REQUEST_ROLL]` enviada pelo Mestre IA para solicitar testes do jogador.

## Fase 4: Gestão de Memória e Expansões (O Cérebro do Mestre)
- [x] Implementar o sistema de Memória em 3 camadas (Sessão [x], Resumo [x], Lore [x]).
- [x] Criar a rotina de encerramento de sessão e comando `/compact` (gera o resumo e limpa o chat ativo).
- [x] Desenvolver a injeção dinâmica de contexto para a montagem dos Prompts base da IA.
- [x] Implementar o sistema de "Skills/Tool Calling" do Mestre (ex: `modificar_hp_jogador`, `consultar_regras`).
- [x] Adicionar suporte a carregamento e troca de módulos de campanha em tempo real (Roteiro RAG guiado por localização).