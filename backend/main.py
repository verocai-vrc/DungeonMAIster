import os
import json
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from backend.dnd_rules.models import CharacterSheet
from backend.data_manager import (
    init_data_files, load_character, save_character, 
    PDF_DIR, DB_DIR, ABILITIES_FILE, SPELLS_FILE, EQUIPMENT_FILE, RACES_FILE, CLASSES_FILE, BASE_DIR
)
from backend.ai_engine.master import AIGameMaster
from backend.rag_system.ingest import ingest_single_pdf, ingest_rules_md

init_data_files()
player_character_state = load_character()
ai_dm = AIGameMaster(DB_DIR)

# Gera o Markdown das regras a partir do JSON e ingere-o no RAG (idempotente)
print("A sincronizar o ruleset D&D 5e hardcoded com o RAG...")
ingest_rules_md(ai_dm.db)
app = FastAPI(title="DungeonMAIster API", description="Motor TTRPG com IA para Solo RPG")

@app.get("/api/rules")
async def get_rules():
    with open(ABILITIES_FILE, "r", encoding="utf-8") as f: abilities = json.load(f)
    with open(SPELLS_FILE, "r", encoding="utf-8") as f: spells = json.load(f)
    with open(EQUIPMENT_FILE, "r", encoding="utf-8") as f: equipment = json.load(f)
    with open(RACES_FILE, "r", encoding="utf-8") as f: races = json.load(f)
    with open(CLASSES_FILE, "r", encoding="utf-8") as f: classes = json.load(f)
    
    descriptions = {}
    descriptions.update(abilities.get("descriptions", {}))
    descriptions.update(spells.get("descriptions", {}))
    descriptions.update(races.get("descriptions", {}))
    descriptions.update(classes.get("descriptions", {}))
    
    # Extrai descrições embutidas na nova estrutura de itens
    eq_items = equipment.get("items", {})
    for item_name, item_data in eq_items.items():
        if "description" in item_data:
            descriptions[item_name] = item_data["description"]
    
    return {
        "races": races.get("races", {}),
        "classes": classes.get("classes", {}),
        "spells": spells.get("spells_by_level", {}),
        "equipment": eq_items,
        "descriptions": descriptions
    }

@app.get("/api/character", response_model=CharacterSheet)
async def get_character():
    return CharacterSheet(**player_character_state)

@app.post("/api/character")
async def update_character(character: CharacterSheet):
    global player_character_state
    player_character_state = character.dict()
    save_character(player_character_state)
    return {"status": "success", "message": "Ficha atualizada com sucesso"}

@app.post("/api/upload_module")
async def upload_module(file: UploadFile = File(...)):
    file_path = os.path.join(PDF_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Converter PDF → Markdown limpo → chunks por cabeçalho → guardar no Chroma
    ingest_single_pdf(file_path, ai_dm.db)
    
    # 4. Avisar a memória da IA sobre a nova campanha
    ai_dm.chat_history.append(f"Sistema: O módulo de campanha '{file.filename}' foi carregado. O Mestre agora baseia-se nesta história.")
    
    return {"status": "success", "message": f"Módulo {file.filename} carregado e memorizado com sucesso!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Um jogador conectou-se ao chat.")
    try:
        while True:
            data = await websocket.receive_text()
            response = ai_dm.process_message(data, player_character_state, save_character)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("O jogador desconectou-se do chat.")

# Montar a pasta frontend para servir os ficheiros HTML, CSS e JS na raiz (http://localhost:8000)
app.mount("/", StaticFiles(directory=os.path.join(BASE_DIR, "frontend"), html=True), name="frontend")