# DungeonMAIster - Roadmap and To-Do List

This document tracks the development progress of the AI-powered TTRPG engine (D&D 5e) focused on the Solo RPG experience. Tasks are divided according to the project's implementation phases.

## Phase 1: Chat Foundation (Communication)
- [x] Create the basic project directory structure (`backend`, `frontend`, `data`, `docs`).
- [x] Set up the basic FastAPI server (`backend/main.py`).
- [x] Create the HTML/JS/Tailwind interface (`frontend/index.html`) with panels for chat and the character sheet.
- [x] Establish the WebSocket connection between client and server.
- [x] Implement the "Echo" logic (the server returns what the player types to test communication).
- [x] Create the base `AIGameMaster` class to receive and send text messages.

## Phase 2: The RAG Engine (The Game Master's Knowledge)
- [x] Implement a script to ingest and read PDFs (rulebooks and adventures).
- [x] Process the PDF text into *chunks* and generate embeddings.
- [x] Configure and save the embeddings in a local vector database (ChromaDB/FAISS) using metadata.
- [x] Integrate the AI (Ollama/LangChain) to query the RAG database before formulating responses.

## Phase 3: Character Sheet and d20 System
- [x] Design and create the data models (JSON and Pydantic) for the D&D 5e Character Sheet.
- [x] Create the hardcoded math logic in the backend (e.g. automatic ability-modifier calculation).
- [x] Implement the visual system in the frontend to display, update and manage the Sheet and Inventory tabs.
- [x] Develop the bidirectional "Dice Engine" for player rolls and validation.
- [x] Set up handling of the hidden `[REQUEST_ROLL]` tag sent by the AI Game Master to request player checks.

## Phase 4: Memory Management and Expansions (The Game Master's Brain)
- [x] Implement the 3-layer Memory system (Session [x], Summary [x], Lore [x]).
- [x] Create the session-closing routine and the `/compact` command (generates the summary and clears the active chat).
- [x] Develop dynamic context injection for assembling the AI's base prompts.
- [x] Implement the Game Master's "Skills/Tool Calling" system (e.g. `modify_player_hp`, `consult_rules`).
- [x] Add support for loading and switching campaign modules in real time (location-guided RAG script).

# mobileDungeonCard
