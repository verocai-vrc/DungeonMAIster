import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.dnd_rules.models import CharacterSheet, Attributes
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

# Caminhos para o banco de dados RAG
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data", "db")

# Inicialização da aplicação FastAPI
app = FastAPI(title="DungeonMAIster API", description="Motor TTRPG com IA para Solo RPG")

class AIGameMaster:
    """
    Classe base para o Mestre de Jogo IA com integração RAG.
    """
    def __init__(self):
        print("A carregar o Cérebro do Mestre (Embeddings e Base de Dados RAG)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        # Conecta ao banco de dados Chroma onde guardámos os PDFs
        self.db = Chroma(persist_directory=DB_DIR, embedding_function=self.embeddings)
        # Configura o recuperador (Retriever)
        self.retriever = self.db.as_retriever(search_kwargs={"k": 3})
        
        print("A acordar o Mestre IA (Ollama - llama3)...")
        # Assumimos o uso do modelo 'llama3', mas podes mudar para 'mistral' ou outro que prefiras
        self.llm = Ollama(model="llama3")
        
        # Criamos o prompt que orienta a personalidade e a tarefa do LLM
        self.prompt = PromptTemplate(
            template="""És um Mestre de Jogo (Dungeon Master) de D&D 5e experiente, narrativo e criativo. 
Usa o seguinte contexto das regras ou da aventura para resolver a ação do jogador. 
Se o contexto não for útil, usa o teu conhecimento geral de D&D.
Narra as consequências da ação de forma imersiva e em português.

Contexto recuperado:
{context}

Ação do Jogador: {action}

Resposta do Mestre:""",
            input_variables=["context", "action"]
        )
    
    def process_message(self, message: str) -> str:
        """
        Processa a mensagem do jogador.
        """
        # 1. Recuperar contexto do PDF
        docs = self.retriever.invoke(message)
        context = "\n".join([doc.page_content for doc in docs])
        
        # 2. Gerar a narrativa com o Ollama
        formatted_prompt = self.prompt.format(context=context, action=message)
        llm_response = self.llm.invoke(formatted_prompt)
        
        # 3. Formatar a resposta em HTML para o frontend, mantendo o contexto oculto num "spoiler" para curiosidade
        html_response = f"{llm_response.replace('\n', '<br>')}"
        html_response += f"<br><br><details><summary class='text-xs text-gray-500 cursor-pointer'>Ver Regras/Contexto RAG Utilizado</summary><i class='text-gray-600 text-xs mt-2 block'>{context[:400]}...</i></details>"
        
        return html_response

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