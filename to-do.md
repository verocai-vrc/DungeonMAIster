# DungeonMAIster - Exhaustive Feature List (To-Do)
## Misc Functionalities
- [] Hardcoded DND 5e ruleset for the AI to consult: rules, item and descriptions, classes and races, spells, etc
- [] Ruleset selection dropdown menu (future versions)
- [] Display current memorized module in the system page after ingestion
- [] persistent campaign save feature to continue games
= [] 

### Phase 1: Foundation and Base Infrastructure
- [ ] Set up the main backend server (FastAPI).
- [ ] Establish real-time bidirectional communication (WebSockets) between client and server.
- [ ] Create the user interface (HTML/JS/Tailwind CSS) split into panels (Chat on the left, Sheet/Mechanics on the right).
- [ ] Implement the structural logic of the `AIGameMaster` class for receiving and returning chat messages.
- [ ] Create a WebSocket connection-state indicator in the frontend (Connected/Disconnected).
- [ ] Build the data flow loop (Frontend sends action -> Backend processes -> RAG acts -> AI decides -> Tool execution -> Return to Frontend).

### Phase 2: RAG Engine and the Game Master's Brain
- [ ] Implement integration with a local LLM using Ollama (e.g. Llama3).
- [ ] Create a script (ingest.py) to read and ingest adventure modules and rulebooks in PDF.
- [ ] Split the PDF text into "chunks" (smaller, indexable fragments).
- [ ] Generate embeddings using `HuggingFaceEmbeddings` and store them in a local vector database (ChromaDB).
- [ ] Configure the system (Retriever) to dynamically retrieve context from the RAG before the AI formulates responses.
- [ ] Create the feature for the user to upload new PDF modules in real time from the "System" tab in the UI.
- [ ] Inject strict "anti-gaslight" rules into the AI's base prompt (the player cannot invent items/spells that are not on the sheet).

### Phase 3: Character Sheet and D&D 5e Math
- [ ] Create the data models (JSON/Pydantic structures) for the sheet (Name, Race, Class, HP, AC, Attributes, etc).
- [ ] Implement hardcoded logic to automatically calculate ability modifiers (e.g. Mod = floor((Score - 10) / 2)).
- [ ] Implement logic to calculate max HP based on class, level and constitution modifier.
- [ ] Implement Armor Class (AC) calculation based on equipped armor, shields and dexterity.
- [ ] Load the structured game rules into the frontend (Races, Classes, Equipment, Spells and Abilities database).
- [ ] Create the modal window for creating and editing the Character Sheet.
- [ ] Automate the injection of abilities and proficiencies into the sheet based on the chosen class, race and level.
- [ ] Display organized tabs for Sheet, Inventory and System.
- [ ] Develop dynamic "Tooltips" on inventory and spells that show descriptions/damage dice on hover.

### Phase 4: Dice Engine and d20 System
- [ ] Implement a dice interpreter/engine in the backend that can roll math expressions (e.g. `1d20+3`).
- [ ] Process native dice commands sent by the player in the chat (e.g. `/roll 1d20`).
- [ ] Process narrative intents bundled with the player's roll (e.g. `/rollSTR I try to push the door`).
- [ ] Create quick visual buttons on the character sheet ("Quick Roll") to test attributes.
- [ ] Implement a routine so the AI Game Master can request risk rolls through the `[REQUEST_ROLL]` tag.
- [ ] Convert the Game Master's check request into a visual interface (buttons) for the player to choose the skill/attribute to use.
- [ ] Send the exact results of the player's rolled dice directly into the AI Game Master's narrative to process and narrate.

### Phase 5: Memory and History Management
- [ ] Implement Short-Term Memory (context injected with the last N exchanged messages).
- [ ] Implement the `/compact` command to close sessions, asking the AI to summarize the active chat history.
- [ ] Implement Episodic Memory, continuously injecting the summary of previous sessions into the AI's mind.
- [ ] Implement a "Lore" system and Semantic Memory (`/lore add` and `/lore clear` commands) to pin unchangeable facts.
- [ ] Ensure all memory layers are saved and loaded via `JSON` files (Campaign Saves).

### Phase 6: Game Master Automation (Tags and Tool Calling)
- [ ] **HP Modification:** AI uses `[MODIFY_HP:-X]` for damage and `[MODIFY_HP:+X]` for healing, reflecting it visually in the chat and saving it to the sheet.
- [ ] **Movement:** AI uses `[CHANGE_LOCATION:Place]` to change the current location, improving RAG searches (context awareness).
- [ ] **Experience Gain:** AI uses `[ADD_XP:X]` to award XP and automate the Level Up system when the threshold is reached.
- [ ] **Automatic Inventory:** AI uses `[ADD_ITEM:Item]` to drop loot from the narrative directly into the player's inventory (JSON).
- [ ] **Combat Management:** AI uses `[START_COMBAT:Enemies]` to roll initiative and organize the turn order automatically.
- [ ] **End of Combat:** AI uses `[END_COMBAT]` to disable the battle state.
- [ ] **Dialogue (NPCs):** AI uses `[NPC:Name]Speech[/NPC]` tags to generate visually highlighted speech bubbles in the chat.
- [ ] **Resource Management:** AI uses `[USE_RESOURCE:Name]` to deduct the player's limited class resources (e.g. Rage, Channel Divinity) and validate them.
- [ ] **Spell Slot Management:** AI uses `[USE_SPELL_SLOT:Level]` to deduct and validate spell use according to the sheet's slots.
- [ ] **Combat Action Economy:** AI strictly validates the use of the Action, Bonus Action and Reactions (`[USE_ACTION:main]`, etc.).
- [ ] **Turn Management:** AI uses `[RESET_TURN]` to return the action economy to the player when a new turn begins.
- [ ] **Rests and Recovery:** AI uses `[RESTORE_ALL]` on a Long Rest to recharge HP, spells and resources to the maximum.

### Phase 7: User Meta-Commands
- [ ] Implement a help screen or generic `/help` command to list the commands.
- [ ] Implement chat shortcuts for the player to force actions and rolls (e.g. Enter submits the chat).
