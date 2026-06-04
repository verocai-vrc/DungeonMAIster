# **Master Document: AI-Powered TTRPG Engine (D\&D 5e)**

## **1\. Project Overview**

**Goal:** Develop a tabletop RPG (TTRPG) engine for a single player (Solo RPG), focused strictly on the rules system of *Dungeons & Dragons 5th Edition (D\&D 5e)*.

**The AI's Role:** Act in real time as the Game Master (Dungeon Master \- DM), organizing the narrative, managing encounters, dialogue, and validating ability checks and combat based on the D\&D 5e rules.

**Distribution Model:** Local Web Application (runs in the user's browser, but the server is hosted on the user's own machine, ensuring privacy, zero external network lag, and easing future expansion to multiplayer).

## **2\. Technology Stack (Architecture)**

### **2.1 Backend (Engine and Logic)**

* **Primary Language:** Python 3.x  
* **Web Server:** FastAPI  
* **Communication:** WebSockets (for real-time, bidirectional communication between the player and the AI Game Master, simulating continuous typing).

### **2.2 Frontend (User Interface)**

* **Base:** HTML5, CSS3, Vanilla JavaScript.  
* **Styling:** Tailwind CSS (via CDN initially) for a clean, fast and responsive interface, split into panels (Chat, Character Sheet, Dice Rolling).

### **2.3 Artificial Intelligence and RAG Module**

* **AI Orchestrator:** LangChain or LlamaIndex (to build the Game Master's thinking pipeline).  
* **Local Processing (Primary):** Ollama (running roleplay- and instruction-focused models such as Llama-3 or Mistral, ensuring zero cost and offline execution).  
* **Cloud Processing (Fallback):** Integration with external APIs (e.g. OpenAI, Google Gemini) triggered by entering an API key in the system settings.  
* **Vector Database (RAG):** ChromaDB or FAISS.  
  * **Purpose:** Store the D\&D 5e rulebooks and adventure modules (PDFs). The AI will query this database before answering to avoid hallucinations and apply rules correctly.

## **3\. Suggested Folder Structure**

To ease implementation via AI agents, the project should follow this modular structure:

my\_rpg\_ai/  
├── backend/  
│   ├── main.py              \# FastAPI entry point and WebSocket routes  
│   ├── ai\_engine/           \# Game Master logic (Langchain, Prompts, Ollama/API connection)  
│   ├── dnd\_rules/           \# Hardcoded D\&D logic (modifier and damage calculation)  
│   └── rag\_system/          \# PDF processing and ChromaDB queries  
├── frontend/  
│   ├── index.html           \# Main player interface  
│   ├── css/                 \# Custom styles  
│   └── js/                  \# Panel logic (WebSockets, sheet updates)  
├── data/                      
│   ├── prompts/             \# Markdown (.md) files with the Game Master's personalities  
│   ├── saves/               \# JSON files with saved campaign data  
│   ├── pdf\_modules/         \# Original adventure and supplement PDFs  
│   └── db/                  \# Vector database (ChromaDB)  
├── docs/                    \# Project documentation (including this GDD)  
└── requirements.txt         \# List of Python dependencies

## **4\. Core Features (Implementation Roadmap)**

### **Phase 1: Chat Foundation (Communication)**

* \[ \] Set up a basic FastAPI server.  
* \[ \] Create the HTML/JS interface with a chat area and an input field.  
* \[ \] Establish the WebSocket connection.  
* \[ \] Implement the AIGameMaster class to receive messages and return simple text responses.

### **Phase 2: The RAG Engine (The Game Master's Knowledge)**

* \[ \] Implement a script to read rule and adventure PDFs.  
* \[ \] Break the text into fragments (chunks) and create embeddings.  
* \[ \] Save the embeddings in the local ChromaDB with metadata (Rule vs. Adventure).  
* \[ \] Configure the AI to fetch context from the vector database.

### **Phase 3: Character Sheet and d20 System**

* \[ \] Create the data structure (JSON/Pydantic models) for the D\&D 5e Sheet.  
* \[ \] Implement a frontend system to display and edit the sheet.  
* \[ \] Develop the bidirectional "Dice Roller" engine.

### **Phase 4: Memory Management and Expansions**

* \[ \] Implement the session-closing and compaction routine (/compact).  
* \[ \] Create the context injector (dynamic assembly of the Session's Initial Prompt).  
* \[ \] Implement loading and switching of Campaign Modules (Active Module).

## **5\. Prompt and Personality Management (The Game Master's Brain)**

### **5.1. Markdown (.md) File Approach**

The base prompts (System Prompts) will be stored in the data/prompts/ folder as Markdown files. The backend will read the contents of these files at server startup.

### **5.2. The Game Master's "Skills" (Tool Calling / Function Calling)**

The Game Master will be instructed that it has the following tools at its disposal:

1. **consult\_rules(topic: str)**: Searches ChromaDB.  
2. **modify\_player\_hp(value: int, type: str)**: Updates the Character Sheet (damage/healing).  
3. **add\_inventory(item: str)**: Injects items into the Sheet's JSON.  
4. **roll\_hidden\_dice(expression: str)**: Allows rolling dice in secret.  
5. **advance\_chapter(new\_location: str)**: Updates the RAG script status.

## **6\. Character Sheet Structure (D\&D 5e)**

The character sheet will be the game's mathematical source of truth, stored in JSON and managed by Pydantic Models on the backend. The engine will calculate modifiers automatically: Modifier \= floor((Score \- 10\) / 2).

## **7\. Dice Rolling System and AI Interaction**

### **7.1 AI-Requested Roll (Game Master)**

The AI generates the hidden tag \[REQUEST\_ROLL:stealth\]. The frontend hides the tag, generates a button, the player clicks, the die is rolled mathematically, and \<SYSTEM\_ROLL\> Stealth: 18 is returned to the AI to process.

### **7.2 Player's Voluntary Roll (Proactive Action)**

The player clicks "Attack" in the interface. The frontend rolls the attack and damage dice and sends them simultaneously with the text description for the Game Master to narrate the result.

## **8\. Memory System and Campaign Saving (Saves)**

Memory is divided into three layers to optimize token usage (Context Limit):

1. **Short-Term Memory (Current Session):** Log of the last N messages.  
2. **Episodic Memory (Summaries):** Narrative generated after the /compact command.  
3. **Semantic Memory (Lore):** Isolated facts (NPCs, Quests).  
   *The /compact command:* Closes the session, asks the AI to summarize the text, stores the data in JSON, and clears the active chat.

## **9\. RAG System and Adventure Ingestion (PDF Modules)**

The system ingests PDFs, categorizing chunks with metadata (e.g. type: plot\_location).

The AI tracks the player's Current Location and uses it as a filter in ChromaDB, ensuring it reads the right part of the adventure (e.g. The Tavern) without hallucinating the ending (e.g. The Boss's Castle). The AI is instructed to improvise coherently in the gray areas where the PDF has no information.

## **10\. Interface Layout (UX/UI)**

The web interface (SPA \- Single Page Application) should be designed with Tailwind CSS and divided cleanly:

* **Left Panel (65% of the screen):** Dedicated to the "World". Contains the Chat history and the input bar to describe actions.  
* **Right Panel (35% of the screen):** Dedicated to the "Mechanics". A system of *Tabs* alternating between:  
  * **Sheet Tab:** Attributes, HP, AC and Skills.  
  * **Inventory Tab:** Spells, weapons and items.  
  * **System Tab:** Buttons to load PDFs, switch API or close the session (/compact).

## **11\. The Main Game Loop (Data Flow)**

Whenever the player types an action, this is the exact cycle that happens in milliseconds:

1. Frontend sends the action via WebSocket \-\>  
2. Backend receives it. Identifies the player's Current Location \-\>  
3. RAG System searches ChromaDB using the action \+ location and extracts the context \-\>  
4. AI Engine assembles the prompt: \[Sheet JSON\] \+ \[Memory\] \+ \[RAG Context\] \+ \[Action\] \-\>  
5. LLM (Ollama/API) processes and decides whether it needs to trigger a Tool (Skill) \-\>  
6. Backend executes the Tool (e.g. update health) if needed, and forwards the final narrative via WebSocket \-\>  
7. Frontend prints the text on screen (typewriter effect) and updates the graphical interface.

## **12\. Startup Instructions for the AI Agent (Vibe-Coding)**

**Hello, Autonomous Agent / Copilot\!**

If you are reading this document to begin the implementation, your goal is to **strictly follow Phase 1**.

Please start by:

1. Creating the basic directory structure described in Section 3\.  
2. Writing backend/main.py with a FastAPI server configured for WebSockets.  
3. Writing a prototype in frontend/index.html with the panels mentioned in Section 10\.  
4. Implementing a simple echo: everything the player types in the chat should be returned by the server (still without real AI, just to test the WebSocket connection).  
   Wait for the user's *feedback* before moving on to the Ollama/LangChain integration.
