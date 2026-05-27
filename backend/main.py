import os
import re
import json
import shutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from backend.dnd_rules.models import CharacterSheet, Attributes
from backend.dnd_rules.dice import roll_dice
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Caminhos para o banco de dados RAG
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data", "db")
SAVE_DIR = os.path.join(BASE_DIR, "data", "saves")
CHAR_FILE = os.path.join(SAVE_DIR, "character.json")
PDF_DIR = os.path.join(BASE_DIR, "data", "pdf_modules")
EQUIPMENT_FILE = os.path.join(BASE_DIR, "data", "equipment.json")
SPELLS_FILE = os.path.join(BASE_DIR, "data", "spells.json")
ABILITIES_FILE = os.path.join(BASE_DIR, "data", "abilities.json")
RACES_FILE = os.path.join(BASE_DIR, "data", "races.json")
CLASSES_FILE = os.path.join(BASE_DIR, "data", "classes.json")

os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

def init_data_files():
    """Cria os ficheiros de regras divididos por categoria se não existirem."""
    
    equipment_data = {
        "items": [
            "Adaga", "Arco Curto", "Arco Longo", "Besta Leve", "Besta Pesada",
            "Espada Curta", "Espada Longa", "Machado de Batalha", "Machado Grande",
            "Maça", "Martelo de Guerra", "Rapieira", "Armadura de Couro",
            "Cota de Malha", "Brunea", "Placas", "Escudo", "Poção de Cura",
            "Corda (15m)", "Tocha", "Mochila do Aventureiro", "Rações (1 dia)"
        ],
        "armor": {
            "Armadura de Couro": {"type": "light", "base": 11},
            "Brunea": {"type": "medium", "base": 14},
            "Cota de Malha": {"type": "heavy", "base": 16},
            "Placas": {"type": "heavy", "base": 18},
            "Escudo": {"type": "shield", "bonus": 2}
        },
        "descriptions": {
            "Machado Grande": "Machado de um lenhador qualquer... ou de um guerreiro furioso. 1d12 de dano cortante. Pesado, duas mãos.",
            "Adaga": "Arma corpo-a-corpo simples. 1d4 de dano perfurante. Acuidade, leve, arremesso (distância 6/18m).",
            "Poção de Cura": "Um personagem que beber o líquido vermelho deste frasco recupera 2d4+2 pontos de vida.",
            "Armadura de Couro": "Armadura leve. CA 11 + Modificador de Destreza.",
            "Brunea": "Armadura média (escamas). CA 14 + Modificador de Destreza (máx 2). Desvantagem em Furtividade.",
            "Cota de Malha": "Armadura pesada. CA 16. Requer For 13. Desvantagem em Furtividade.",
            "Placas": "Armadura pesada. CA 18. Requer For 15. Desvantagem em Furtividade.",
            "Escudo": "Concede +2 na sua Classe de Armadura."
        }
    }

    spells_data = {
        "spells_by_level": {
            "1": ["Mísseis Mágicos", "Curar Ferimentos", "Escudo Arcano"],
            "2": ["Passo Nebuloso", "Arma Espiritual"]
        },
        "descriptions": {
            "Mísseis Mágicos": "Crias três dardos mágicos brilhantes. Cada dardo atinge uma criatura e causa 1d4+1 de dano de energia.",
            "Curar Ferimentos": "Uma criatura que você toca recupera pontos de vida iguais a 1d8 + seu modificador.",
            "Escudo Arcano": "Uma barreira invisível aparece e protege você. Ganha +5 de bônus na CA até seu próximo turno.",
            "Passo Nebuloso": "Você é cercado por névoa e teletransporta-se até 9 metros.",
            "Arma Espiritual": "Você cria uma arma flutuante espectral que atinge uma criatura."
        }
    }

    abilities_data = {
        "features": [],
        "descriptions": {
            "Ataque Furtivo": "Você sabe como atacar sutilmente. Causa dano extra se tiver vantagem."
        }
    }

    races_data = {
        "races": {
            "Humano": { "attributes": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1}, "features": ["Deslocamento 9m"] },
            "Elfo": { "attributes": {"dexterity": 2}, "features": ["Visão no Escuro", "Ancestralidade Feérica", "Transe"] },
            "Anão": { "attributes": {"constitution": 2}, "features": ["Visão no Escuro", "Resiliência Anã", "Treinamento Anão"] },
            "Halfling": { "attributes": {"dexterity": 2}, "features": ["Sorte", "Bravura", "Agilidade Halfling"] },
            "Orc": { "attributes": {"strength": 2, "constitution": 1}, "features": ["Visão no Escuro", "Ataque Selvagem", "Resistência Implacável"] }
        },
        "descriptions": {
            "Ataque Selvagem": "Acertos críticos causam dano extra massivo.",
            "Resistência Implacável": "Quando cai para 0 HP, pode escolher cair para 1 HP em vez disso (1/descanso longo)."
        }
    }

    classes_data = {
        "classes": {
            "Bárbaro": { "hit_dice": 12, "proficiencies": ["Atletismo", "Intimidação"], "features": { "1": ["Fúria", "Defesa sem Armadura"], "2": ["Ataque Temerário", "Sentido de Perigo"], "3": ["Caminho Primitivo"] } },
            "Guerreiro": { "hit_dice": 10, "proficiencies": ["Acrobacia", "Sobrevivência"], "features": { "1": ["Estilo de Luta", "Retomar o Fôlego"], "2": ["Surto de Ação"], "3": ["Arquétipo Marcial"] } },
            "Ladino": { "hit_dice": 8, "proficiencies": ["Furtividade", "Prestidigitação", "Enganação"], "features": { "1": ["Ataque Furtivo", "Gíria de Ladrão", "Especialização"], "2": ["Ação Astuta"], "3": ["Arquétipo Rogino"] } },
            "Mago": { "hit_dice": 6, "proficiencies": ["Arcanismo", "História"], "features": { "1": ["Conjuração", "Recuperação Arcana"], "2": ["Tradição Arcana"], "3": ["Truques Adicionais"] } },
            "Clérigo": { "hit_dice": 8, "proficiencies": ["Religião", "Medicina"], "features": { "1": ["Conjuração", "Domínio Divino"], "2": ["Canalizar Divindade (1/descanso)"], "3": ["Magias de Domínio"] } },
            "Feiticeiro": { "hit_dice": 6, "proficiencies": ["Arcanismo", "Enganação"], "features": { "1": ["Conjuração", "Origem Feiticeira"], "2": ["Fonte de Magia"], "3": ["Metamágica"] } }
        },
        "descriptions": {
            "Fúria": "Em batalha, você luta com ferocidade primitiva. No seu turno, você pode entrar em fúria como uma ação bônus, ganhando vantagem em Força e resistência a dano físico.",
            "Defesa sem Armadura": "Enquanto não usar armadura, CA = 10 + Mod DES + Mod CON."
        }
    }

    def write_json_merge(file_path, default_data):
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
            updated = False
            for key, val in default_data.items():
                if key not in current_data:
                    current_data[key] = val
                    updated = True
                elif isinstance(val, dict):
                    for subkey, subval in val.items():
                        if subkey not in current_data[key]:
                            current_data[key][subkey] = subval
                            updated = True
            if updated:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(current_data, f, ensure_ascii=False, indent=4)

    write_json_merge(EQUIPMENT_FILE, equipment_data)
    write_json_merge(SPELLS_FILE, spells_data)
    write_json_merge(ABILITIES_FILE, abilities_data)
    write_json_merge(RACES_FILE, races_data)
    write_json_merge(CLASSES_FILE, classes_data)

init_data_files()

# Inicialização da aplicação FastAPI
app = FastAPI(title="DungeonMAIster API", description="Motor TTRPG com IA para Solo RPG")

# Estado global do personagem (Simulando uma base de dados)
def load_character():
    if os.path.exists(CHAR_FILE):
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar ficha salva: {e}")
            
    return {
        "name": "Tharok",
        "race": "Humano",
        "character_class": "Bárbaro",
        "level": 1,
        "location": "Taverna do Pônei Saltitante",
        "attributes": {
            "strength": 16, "dexterity": 14, "constitution": 15,
            "intelligence": 8, "wisdom": 10, "charisma": 12
        },
        "max_hp": 14,
        "current_hp": 14,
        "armor_class": 14,
        "inventory": ["Machado Grande", "Poção de Cura"],
        "features": ["Deslocamento 9m", "Fúria", "Defesa sem Armadura"]
    }

def save_character():
    try:
        with open(CHAR_FILE, "w", encoding="utf-8") as f:
            json.dump(player_character_state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar ficha: {e}")

player_character_state = load_character()

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
        
        # Inicializar a Memória de Sessão (Histórico de curto prazo)
        self.chat_history = []
        self.session_summary = "A aventura acabou de começar. Nenhum evento anterior para resumir."
        self.campaign_lore = "- O mundo é perigoso e cheio de magia.\n- Tharok procura redenção pelos erros do seu passado."
        
        # Criamos o prompt que orienta a personalidade e a tarefa do LLM
        self.prompt = PromptTemplate(
            template="""És um Mestre de Jogo (Dungeon Master) de D&D 5e experiente, narrativo e criativo. 
Usa o seguinte contexto das regras ou da aventura para resolver a ação do jogador. 
Se o contexto não for útil, usa o teu conhecimento geral de D&D.
Narra as consequências da ação de forma imersiva e em português.

REGRA IMPORTANTE PARA ROLAGENS:
Se a ação do jogador tiver um risco de falha (como atacar, investigar, tentar convencer alguém ou desviar-se de um ataque), NÃO decidas o resultado final imediatamente. 
Descreve a reação inicial e pede ao jogador para rolar os dados, incluindo no final da tua resposta EXATAMENTE a tag [REQUEST_ROLL:xdY+Z] (exemplo: [REQUEST_ROLL:1d20+3]).
Aguarda que o jogador responda com o resultado antes de continuares a história.

REGRA IMPORTANTE PARA PONTOS DE VIDA (HP):
Se o personagem sofrer dano (ataques, armadilhas) ou recuperar vida (poções, descanso), usa a tua ferramenta incluindo EXATAMENTE a tag [MODIFY_HP:-X] para remover vida ou [MODIFY_HP:+X] para curar (exemplo: [MODIFY_HP:-4]).
Aplica esta tag no final da tua resposta.

REGRA IMPORTANTE PARA LOCALIZAÇÃO:
Se a narrativa levar o personagem a viajar ou mudar de cenário, atualiza a localização atual usando EXATAMENTE a tag [CHANGE_LOCATION:Nome do Novo Local]. 
Aplica esta tag no final da tua resposta.

Lore e História do Mundo/Personagem (Factos Eternos):
{lore}

Localização Atual: {location}
Resumo da Campanha até agora:
{session_summary}

Contexto recuperado:
{context}

Histórico recente da conversa:
{chat_history}

Ação do Jogador: {action}

Resposta do Mestre:""",
            input_variables=["lore", "location", "session_summary", "context", "chat_history", "action"]
        )
    
    def process_message(self, message: str) -> str:
        """
        Processa a mensagem do jogador.
        """
        # 0.0 Interceptar comando de ajuda (/help)
        if message.strip().lower() == "/help":
            return """
            <div class='bg-blue-900/50 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>
                ℹ️ <b>Comandos do Sistema (Meta Comandos):</b><br>
                <ul class='list-disc list-inside mt-2 space-y-1 text-sm'>
                    <li><b>/roll &lt;expressão&gt;</b>: Rola dados manuais no sistema (ex: <i>/roll 1d20+3</i>).</li>
                    <li><b>/compact</b>: Lê o histórico atual, gera um resumo da sessão e limpa o chat para libertar memória da IA.</li>
                    <li><b>/lore add &lt;facto&gt;</b>: Grava um facto permanente na memória da IA (ex: <i>/lore add O Rei está enfeitiçado</i>). Digita <b>/lore</b> para ler tudo.</li>
                    <li><b>/help</b>: Exibe este menu de ajuda.</li>
                </ul>
            </div>
            """

        # 0.0.1 Interceptar comando de Lore (/lore)
        if message.strip().lower().startswith("/lore"):
            command_body = message[5:].strip()
            if command_body.lower().startswith("add "):
                new_fact = command_body[4:].strip()
                self.campaign_lore += f"\n- {new_fact}"
                return f"<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore Atualizada:</b> {new_fact}</div>"
            elif command_body.lower() == "clear":
                self.campaign_lore = ""
                return "<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore limpa.</b></div>"
            else:
                lore_html = self.campaign_lore.replace('\n', '<br>') if self.campaign_lore else "Nenhuma lore registada."
                return f"<div class='bg-indigo-900/50 p-4 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore Gravada (Factos Eternos):</b><br><i class='text-sm mt-2 block'>{lore_html}</i></div>"

        # 0.1 Interceptar comando de compactação de memória (/compact)
        if message.strip().lower() == "/compact":
            if not self.chat_history:
                return "<div class='bg-yellow-900/50 p-3 rounded text-yellow-400 font-bold border border-yellow-800'>Nenhum histórico recente para resumir.</div>"
            
            print("A gerar resumo da sessão...")
            history_text = "\n".join(self.chat_history)
            summary_prompt = f"Resume os seguintes eventos da sessão de RPG em 1 ou 2 parágrafos concisos. Foca-te nas ações importantes, locais visitados, resultados dos dados e estado dos personagens:\n\n{history_text}"
            
            new_summary = self.llm.invoke(summary_prompt)
            
            if self.session_summary == "A aventura acabou de começar. Nenhum evento anterior para resumir.":
                self.session_summary = new_summary
            else:
                self.session_summary += f"\n\n{new_summary}"
                
            self.chat_history = [] # Limpa a memória de curto prazo!
            return f"<div class='bg-purple-900/50 p-4 rounded border border-purple-500 text-purple-100 my-2 shadow-lg'>📜 <b>Sessão Resumida e Memória Compactada:</b><br><i class='text-sm'>{new_summary}</i></div>"

        # 0. Interceptar comandos do sistema (como rolagens de dados)
        if message.strip().lower().startswith("/roll "):
            expression = message[6:].strip()
            try:
                result = roll_dice(expression)
                rolls_str = ", ".join(map(str, result["rolls"]))
                mod_str = f"+{result['modifier']}" if result['modifier'] >= 0 else str(result['modifier'])
                if result['modifier'] == 0: mod_str = ""
                
                # Injetar silenciosamente o resultado na memória para a IA saber o que aconteceu!
                system_msg = f"O jogador rolou {result['expression']} e obteve um total de {result['total']}."
                self.chat_history.append(f"Sistema: {system_msg}")
                
                return f"<div class='bg-gray-800 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🎲 <b>Sistema de Rolagem:</b> {result['expression']}<br><b>Dados Roletados:</b> [{rolls_str}] {mod_str} <br><div class='text-2xl font-bold text-green-400 mt-1'>Total = {result['total']}</div></div>"
            except Exception as e:
                return f"<div class='bg-red-900/50 p-3 rounded text-red-400 font-bold border border-red-800'>Erro na rolagem: {str(e)}</div>"

        # 1. Recuperar contexto do PDF
        docs = self.retriever.invoke(message)
        context = "\n".join([doc.page_content for doc in docs])
        
        # 1.5. Preparar o histórico (limitamos às últimas 10 interações para o LLM não se perder/ficar lento)
        history_text = "\n".join(self.chat_history[-10:]) if self.chat_history else "Nenhum histórico recente."
        
        # 2. Gerar a narrativa com o Ollama
        formatted_prompt = self.prompt.format(lore=self.campaign_lore, location=player_character_state["location"], session_summary=self.session_summary, context=context, chat_history=history_text, action=message)
        llm_response = self.llm.invoke(formatted_prompt)
        
        # 2.4 Processar Tool Calling: Modificação de HP
        hp_match = re.search(r'\[MODIFY_HP:([+-]?\d+)\]', llm_response)
        if hp_match:
            try:
                hp_change = int(hp_match.group(1))
                player_character_state["current_hp"] += hp_change
                # Garantir que o HP não passa do máximo nem desce abaixo de 0
                player_character_state["current_hp"] = max(0, min(player_character_state["max_hp"], player_character_state["current_hp"]))
                save_character()
                
                # Criar o bloco visual e substituir a tag
                color = "red" if hp_change < 0 else "green"
                action_text = "Dano Sofrido" if hp_change < 0 else "Cura Recebida"
                hp_block = f"<div class='bg-{color}-900/50 p-3 rounded border border-{color}-500 text-{color}-100 my-2 shadow-lg'>❤️ <b>{action_text}:</b> {abs(hp_change)} <br><b>HP Atual:</b> {player_character_state['current_hp']} / {player_character_state['max_hp']}<br><span class='text-xs text-{color}-300 opacity-75'>(Vai à aba Sistema -> 2. Carregar Ficha)</span></div>"
                
                llm_response = re.sub(r'\[MODIFY_HP:[+-]?\d+\]', hp_block, llm_response)
                
                # Registar silenciosamente na memória o novo HP
                self.chat_history.append(f"Sistema: O HP do jogador foi modificado em {hp_change}. HP atual: {player_character_state['current_hp']}/{player_character_state['max_hp']}.")
            except Exception as e:
                print(f"Erro ao processar HP: {e}")

        # 2.4.2 Processar Tool Calling: Mudança de Localização
        loc_match = re.search(r'\[CHANGE_LOCATION:(.+?)\]', llm_response)
        if loc_match:
            new_location = loc_match.group(1).strip()
            player_character_state["location"] = new_location
            save_character()
            
            loc_block = f"<div class='bg-blue-900/50 p-3 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🗺️ <b>Nova Localização:</b> {new_location}<br><span class='text-xs opacity-75'>(O Mestre atualizou a tua posição no mundo)</span></div>"
            llm_response = re.sub(r'\[CHANGE_LOCATION:.+?\]', loc_block, llm_response)
            self.chat_history.append(f"Sistema: O personagem viajou para {new_location}.")

        # 2.5 Atualizar a memória com a nova interação
        self.chat_history.extend([f"Jogador: {message}", f"Mestre: {llm_response}"])
        
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

@app.get("/api/rules")
async def get_rules():
    """Endpoint REST para devolver a base de dados agregada de regras ao frontend."""
    with open(ABILITIES_FILE, "r", encoding="utf-8") as f: abilities = json.load(f)
    with open(SPELLS_FILE, "r", encoding="utf-8") as f: spells = json.load(f)
    with open(EQUIPMENT_FILE, "r", encoding="utf-8") as f: equipment = json.load(f)
    with open(RACES_FILE, "r", encoding="utf-8") as f: races = json.load(f)
    with open(CLASSES_FILE, "r", encoding="utf-8") as f: classes = json.load(f)
    
    # Combina as descrições dos cinco ficheiros
    descriptions = {}
    descriptions.update(abilities.get("descriptions", {}))
    descriptions.update(spells.get("descriptions", {}))
    descriptions.update(equipment.get("descriptions", {}))
    descriptions.update(races.get("descriptions", {}))
    descriptions.update(classes.get("descriptions", {}))
    
    return {
        "races": races.get("races", {}),
        "classes": classes.get("classes", {}),
        "spells": spells.get("spells_by_level", {}),
        "equipment": equipment.get("items", []),
        "armor": equipment.get("armor", {}),
        "descriptions": descriptions
    }

@app.get("/api/character", response_model=CharacterSheet)
async def get_character():
    """Endpoint REST para devolver um modelo em JSON de uma ficha de personagem D&D 5e."""
    return CharacterSheet(**player_character_state)

@app.post("/api/character")
async def update_character(character: CharacterSheet):
    """Endpoint REST para salvar/atualizar a ficha de personagem."""
    global player_character_state
    player_character_state = character.dict()
    save_character()
    return {"status": "success", "message": "Ficha atualizada com sucesso"}

@app.post("/api/upload_module")
async def upload_module(file: UploadFile = File(...)):
    """Endpoint REST para carregar um módulo de campanha em PDF para o Cérebro da IA."""
    file_path = os.path.join(PDF_DIR, file.filename)
    
    # 1. Salvar o PDF localmente
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 2. Ler e processar o PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(docs)
    
    # 3. Adicionar à base de dados RAG (Chroma)
    ai_dm.db.add_documents(chunks)
    
    # 4. Avisar a memória da IA sobre a nova campanha
    ai_dm.chat_history.append(f"Sistema: O módulo de campanha '{file.filename}' foi carregado. O Mestre agora baseia-se nesta história.")
    
    return {"status": "success", "message": f"Módulo {file.filename} carregado e memorizado com sucesso!"}

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