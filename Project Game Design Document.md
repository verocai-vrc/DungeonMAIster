# **Documento Mestre: Motor TTRPG com IA (D\&D 5e)**

## **1\. Visão Geral do Projeto**

**Objetivo:** Desenvolver um motor de RPG de mesa (TTRPG) para um jogador (Solo RPG), focado estritamente no sistema de regras do *Dungeons & Dragons 5ª Edição (D\&D 5e)*.

**Papel da IA:** Atuar em tempo real como o Mestre de Jogo (Dungeon Master \- DM), organizando a narrativa, gerenciando encontros, diálogos, e validando testes de atributos e combates com base nas regras do D\&D 5e.

**Modelo de Distribuição:** Aplicação Web Local (Roda no navegador do utilizador, mas o servidor é hospedado na própria máquina, garantindo privacidade, zero lag de rede externa e facilitando expansão futura para multiplayer).

## **2\. Stack Tecnológica (Arquitetura)**

### **2.1 Backend (Motor e Lógica)**

* **Linguagem Principal:** Python 3.x  
* **Servidor Web:** FastAPI  
* **Comunicação:** WebSockets (Para comunicação em tempo real e bidirecional entre o jogador e o Mestre de IA, simulando digitação contínua).

### **2.2 Frontend (Interface do Utilizador)**

* **Base:** HTML5, CSS3, Vanilla JavaScript.  
* **Estilização:** Tailwind CSS (via CDN inicialmente) para uma interface limpa, rápida e responsiva, dividida em painéis (Chat, Ficha de Personagem, Rolagem de Dados).

### **2.3 Módulo de Inteligência Artificial e RAG**

* **Orquestrador de IA:** LangChain ou LlamaIndex (Para criar o pipeline de pensamento do Mestre).  
* **Processamento Local (Principal):** Ollama (Rodando modelos focados em roleplay e instrução, como Llama-3 ou Mistral, garantindo custo zero e execução offline).  
* **Processamento em Nuvem (Fallback):** Integração com APIs externas (ex: OpenAI, Google Gemini) acionadas mediante inserção de chave API nas configurações do sistema.  
* **Banco de Dados Vetorial (RAG):** ChromaDB ou FAISS.  
  * **Propósito:** Armazenar os manuais de regras do D\&D 5e e módulos de aventuras (PDFs). A IA consultará este banco antes de responder para evitar alucinações e aplicar regras corretamente.

## **3\. Estrutura de Pastas Sugerida**

Para facilitar a implementação via agentes de IA, o projeto deve seguir esta estrutura modular:

meu\_rpg\_ai/  
├── backend/  
│   ├── main.py              \# Ponto de entrada do FastAPI e rotas WebSocket  
│   ├── ai\_engine/           \# Lógica do Mestre (Langchain, Prompts, Conexão Ollama/API)  
│   ├── dnd\_rules/           \# Lógica hardcoded de D\&D (cálculo de modificadores, dano)  
│   └── rag\_system/          \# Processamento de PDFs e consultas ao ChromaDB  
├── frontend/  
│   ├── index.html           \# Interface principal do jogador  
│   ├── css/                 \# Estilos customizados  
│   └── js/                  \# Lógica do painel (WebSockets, atualização da ficha)  
├── data/                      
│   ├── prompts/             \# Ficheiros Markdown (.md) com as personalidades do Mestre  
│   ├── saves/               \# Ficheiros JSON com os dados das campanhas salvas  
│   ├── pdf\_modules/         \# PDFs originais de aventuras e suplementos  
│   └── db/                  \# Banco de dados vetorial (ChromaDB)  
├── docs/                    \# Documentação do projeto (Incluindo este GDD)  
└── requirements.txt         \# Lista de dependências do Python

## **4\. Funcionalidades Principais (Roadmap de Implementação)**

### **Fase 1: Fundação do Chat (Comunicação)**

* \[ \] Configurar servidor FastAPI básico.  
* \[ \] Criar a interface HTML/JS com área de chat e campo de input.  
* \[ \] Estabelecer conexão via WebSocket.  
* \[ \] Implementar a classe AIGameMaster para receber mensagens e devolver respostas textuais simples.

### **Fase 2: O Motor RAG (Conhecimento do Mestre)**

* \[ \] Implementar script para ler PDFs de regras e aventuras.  
* \[ \] Quebrar o texto em fragmentos (chunks) e criar embeddings.  
* \[ \] Salvar os embeddings no ChromaDB local com metadados (Regra vs. Aventura).  
* \[ \] Configurar a IA para buscar o contexto no banco de dados vetorial.

### **Fase 3: Ficha de Personagem e Sistema d20**

* \[ \] Criar estrutura de dados (JSON/Modelos Pydantic) para a Ficha de D\&D 5e.  
* \[ \] Implementar sistema no frontend para exibir e editar a ficha.  
* \[ \] Desenvolver o "Motor de Dados" (Dice Roller) bidirecional.

### **Fase 4: Gestão de Memória e Expansões**

* \[ \] Implementar a rotina de encerramento e compactação de sessão (/compact).  
* \[ \] Criar o injetor de contexto (Montagem dinâmica do Prompt Inicial da Sessão).  
* \[ \] Implementar carregamento e troca de Módulos de Campanha (Módulo Ativo).

## **5\. Gerenciamento de Prompts e Personalidade (O Cérebro do Mestre)**

### **5.1. Abordagem de Ficheiros Markdown (.md)**

Os prompts base (System Prompts) serão armazenados na pasta data/prompts/ como ficheiros Markdown. O backend lerá o conteúdo destes ficheiros no arranque do servidor.

### **5.2. "Skills" do Mestre (Tool Calling / Function Calling)**

O Mestre será instruído de que tem à sua disposição as seguintes ferramentas:

1. **consultar\_regras(topico: str)**: Pesquisa no ChromaDB.  
2. **modificar\_hp\_jogador(valor: int, tipo: str)**: Atualiza a Ficha do Personagem (dano/cura).  
3. **adicionar\_inventario(item: str)**: Injeta itens no JSON da Ficha.  
4. **rolar\_dados\_ocultos(expressao: str)**: Permite rolar dados em segredo.  
5. **avancar\_capitulo(novo\_local: str)**: Atualiza o status do Roteiro RAG.

## **6\. Estrutura da Ficha de Personagem (D\&D 5e)**

A ficha do personagem será a fonte da verdade matemática do jogo, armazenada em JSON e gerida por Modelos Pydantic no backend. O motor calculará modificadores de forma automática: Modificador \= floor((Valor \- 10\) / 2).

## **7\. Sistema de Rolagem de Dados e Interação com a IA**

### **7.1 Rolagem Solicitada pela IA (Mestre)**

A IA gera a tag oculta \[REQUEST\_ROLL:furtividade\]. O frontend esconde a tag, gera um botão, o jogador clica, rola o dado matematicamente e devolve \<SYSTEM\_ROLL\> Furtividade: 18 para a IA processar.

### **7.2 Rolagem Voluntária do Jogador (Ação Proativa)**

O jogador clica em "Atacar" na interface. O frontend rola o dado de ataque e dano e envia simultaneamente com a descrição de texto para o Mestre narrar o resultado.

## **8\. Sistema de Memória e Salvamento da Campanha (Saves)**

A memória é dividida em três camadas para otimizar o uso de tokens (Context Limit):

1. **Memória de Curto Prazo (Sessão Atual):** Log das últimas N mensagens.  
2. **Memória Episódica (Resumos):** Narrativa gerada após o comando /compact.  
3. **Memória Semântica (Lore):** Fatos isolados (NPCs, Missões).  
   *Comando /compact:* Encerra a sessão, pede à IA para resumir o texto, guarda os dados no JSON e limpa o chat ativo.

## **9\. Sistema RAG e Ingestão de Aventuras (Módulos em PDF)**

O sistema ingere PDFs categorizando Chunks com metadados (ex: type: plot\_location).

A IA acompanha a Localização Atual do jogador e usa-a como filtro no ChromaDB, garantindo que lê a parte certa da aventura (ex: A Taverna) sem alucinar o final (ex: O Castelo do Boss). A IA é instruída a improvisar coerentemente nas áreas cinzas onde o PDF não tem informação.

## **10\. Layout da Interface (UX/UI)**

A interface web (SPA \- Single Page Application) deve ser desenhada com Tailwind CSS e dividida de forma limpa:

* **Painel Esquerdo (65% do ecrã):** Dedicado ao "Mundo". Contém o histórico do Chat e a barra de input para descrever ações.  
* **Painel Direito (35% do ecrã):** Dedicado à "Mecânica". Um sistema de *Tabs* (Separadores) alternando entre:  
  * **Aba Ficha:** Atributos, HP, CA e Perícias.  
  * **Aba Inventário:** Magias, armas e itens.  
  * **Aba Sistema:** Botões para carregar PDFs, mudar de API ou encerrar sessão (/compact).

## **11\. O Loop Principal do Jogo (Data Flow)**

Sempre que o jogador digita uma ação, este é o ciclo exato que ocorre em milissegundos:

1. Frontend envia ação via WebSocket \-\>  
2. Backend recebe. Identifica a Localização Atual do jogador \-\>  
3. RAG System pesquisa o ChromaDB usando a ação \+ localização e extrai o contexto \-\>  
4. AI Engine monta o prompt: \[Ficha JSON\] \+ \[Memória\] \+ \[Contexto RAG\] \+ \[Ação\] \-\>  
5. LLM (Ollama/API) processa e decide se precisa acionar uma Tool (Skill) \-\>  
6. Backend executa a Tool (ex: atualizar vida) se necessário, e reencaminha a narrativa final via WebSocket \-\>  
7. Frontend imprime o texto no ecrã (efeito máquina de escrever) e atualiza a interface gráfica.

## **12\. Instruções de Arranque para o Agente de IA (Vibe-Coding)**

**Olá, Agente Autônomo / Copilot\!**

Se estás a ler este documento para iniciar a implementação, o teu objetivo é **estritamente seguir a Fase 1**.

Por favor, começa por:

1. Criar a estrutura básica de diretórios descrita na Secção 3\.  
2. Escrever o backend/main.py com um servidor FastAPI configurado para WebSockets.  
3. Escrever um protótipo em frontend/index.html com os painéis referidos na Secção 10\.  
4. Implementar um echo simples: Tudo o que o jogador digitar no chat deve ser devolvido pelo servidor (ainda sem IA real, apenas para testar a ligação WebSocket).  
   Aguarda o *feedback* do utilizador antes de avançar para a integração com o Ollama/LangChain.