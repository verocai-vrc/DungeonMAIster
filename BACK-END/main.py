from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from models import CharacterSheet, Attributes

# Inicialização da aplicação FastAPI
app = FastAPI(title="DungeonMAIster API", description="Motor TTRPG com IA para Solo RPG")

class AIGameMaster:
    """
    Classe base para o Mestre de Jogo IA. 
    Na Fase 1, atua apenas como um Echo para testar a comunicação via WebSocket.
    """
    def __init__(self):
        # Futuramente, inicializaremos aqui a memória, RAG e o modelo LLM
        pass
    
    def process_message(self, message: str) -> str:
        """
        Processa a mensagem do jogador.
        Por enquanto, devolve apenas um echo indicando que a mensagem foi recebida.
        """
        return f"Mestre IA (Echo): Recebi a tua ação -> '{message}'"

# Instanciamos o Mestre de Jogo
ai_dm = AIGameMaster()

@app.get("/")
async def root():
    """Endpoint de teste básico para verificar se o servidor HTTP está a correr."""
    return {"status": "online", "message": "O servidor DungeonMAIster está a correr. Conecta-te via ws://localhost:8000/ws"}

@app.get("/api/character", response_model=CharacterSheet)
async def get_character():
    """Endpoint REST para devolver um modelo em JSON de uma ficha de personagem D&D 5e."""
    attributes = Attributes(
        strength=16,
        dexterity=14,
        constitution=15,
        intelligence=8,
        wisdom=10,
        charisma=12
    )
    return CharacterSheet(
        name="Tharok",
        character_class="Bárbaro",
        level=1,
        attributes=attributes,
        max_hp=14,
        current_hp=14,
        armor_class=14,
        inventory=["Machado Grande", "Poção de Cura"]
    )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Endpoint WebSocket para comunicação bidirecional em tempo real."""
    await websocket.accept()
    print("Um jogador conectou-se ao chat.")
    try:
        while True:
            data = await websocket.receive_text()
            response = ai_dm.process_message(data)
            await websocket.send_text(response)
    except WebSocketDisconnect:
        print("O jogador desconectou-se do chat.")