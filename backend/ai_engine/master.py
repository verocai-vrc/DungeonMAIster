import re
from backend.dnd_rules.dice import roll_dice
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

class AIGameMaster:
    """Classe base para o Mestre de Jogo IA com integração RAG."""
    def __init__(self, db_dir):
        print("A carregar o Cérebro do Mestre (Embeddings e Base de Dados RAG)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = Chroma(persist_directory=db_dir, embedding_function=self.embeddings)
        self.retriever = self.db.as_retriever(search_kwargs={"k": 3})
        
        print("A acordar o Mestre IA (Ollama - llama3)...")
        self.llm = Ollama(model="llama3")
        
        self.chat_history = []
        self.session_summary = "A aventura acabou de começar. Nenhum evento anterior para resumir."
        self.campaign_lore = "- O mundo é perigoso e cheio de magia.\n- Tharok procura redenção pelos erros do seu passado."
        
        self.prompt = PromptTemplate(
            template="""És um Mestre de Jogo (Dungeon Master) de D&D 5e experiente, narrativo e criativo. 
Usa o seguinte contexto das regras ou da aventura para resolver a ação do jogador. 
Se o contexto não for útil, usa o teu conhecimento geral de D&D.
Narra as consequências da ação de forma imersiva e em português.

REGRA IMPORTANTE PARA ROLAGENS:
Se a ação do jogador tiver um risco de falha, NÃO decidas o resultado final imediatamente. 
Descreve a reação inicial e pede ao jogador para rolar os dados, incluindo EXATAMENTE a tag [REQUEST_ROLL:xdY+Z] (ex: [REQUEST_ROLL:1d20+3]).

REGRA IMPORTANTE PARA PONTOS DE VIDA (HP):
Se o personagem sofrer dano ou recuperar vida, usa EXATAMENTE a tag [MODIFY_HP:-X] para remover vida ou [MODIFY_HP:+X] para curar (ex: [MODIFY_HP:-4]).

REGRA IMPORTANTE PARA LOCALIZAÇÃO:
Se a narrativa levar o personagem a mudar de cenário, atualiza a localização usando EXATAMENTE a tag [CHANGE_LOCATION:Nome do Novo Local]. 

REGRA IMPORTANTE PARA EXPERIÊNCIA (XP):
Recompensa o personagem com XP usando EXATAMENTE a tag [ADD_XP:X] (ex: [ADD_XP:50]).

REGRA IMPORTANTE PARA INVENTÁRIO:
Se o personagem encontrar, comprar ou receber um item, arma ou poção, adiciona-o ao inventário usando EXATAMENTE a tag [ADD_ITEM:Nome do Item] (ex: [ADD_ITEM:Poção de Cura]).

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
    
    def process_message(self, message: str, player_state: dict, save_func) -> str:
        if message.strip().lower() == "/help":
            return "<div class='bg-blue-900/50 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>ℹ️ <b>Meta Comandos:</b><br><ul class='list-disc list-inside mt-2 text-sm'><li><b>/roll &lt;expr&gt;</b>: Rola dados.</li><li><b>/compact</b>: Gera resumo e limpa chat.</li><li><b>/lore add &lt;facto&gt;</b>: Grava facto permanente. Digita <b>/lore</b> para ler.</li><li><b>/help</b>: Ajuda.</li></ul></div>"

        if message.strip().lower().startswith("/lore"):
            command_body = message[5:].strip()
            if command_body.lower().startswith("add "):
                new_fact = command_body[4:].strip(); self.campaign_lore += f"\n- {new_fact}"
                return f"<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore Atualizada:</b> {new_fact}</div>"
            elif command_body.lower() == "clear":
                self.campaign_lore = ""; return "<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore limpa.</b></div>"
            else:
                lore_html = self.campaign_lore.replace('\n', '<br>') if self.campaign_lore else "Nenhuma lore registada."
                return f"<div class='bg-indigo-900/50 p-4 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore Gravada:</b><br><i class='text-sm mt-2 block'>{lore_html}</i></div>"

        if message.strip().lower() == "/compact":
            if not self.chat_history: return "<div class='bg-yellow-900/50 p-3 rounded text-yellow-400 font-bold border border-yellow-800'>Nenhum histórico recente.</div>"
            print("A gerar resumo da sessão...")
            new_summary = self.llm.invoke(f"Resume os eventos focando nas ações e estado:\n\n{chr(10).join(self.chat_history)}")
            if self.session_summary == "A aventura acabou de começar. Nenhum evento anterior para resumir.": self.session_summary = new_summary
            else: self.session_summary += f"\n\n{new_summary}"
            self.chat_history = []; return f"<div class='bg-purple-900/50 p-4 rounded border border-purple-500 text-purple-100 my-2 shadow-lg'>📜 <b>Memória Compactada:</b><br><i class='text-sm'>{new_summary}</i></div>"

        if message.strip().lower().startswith("/roll "):
            expression = message[6:].strip()
            try:
                result = roll_dice(expression)
                rolls_str = ", ".join(map(str, result["rolls"]))
                mod_str = f"+{result['modifier']}" if result['modifier'] >= 0 else str(result['modifier'])
                if result['modifier'] == 0: mod_str = ""
                self.chat_history.append(f"Sistema: O jogador rolou {result['expression']} e obteve {result['total']}.")
                return f"<div class='bg-gray-800 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🎲 <b>Rolagem:</b> {result['expression']}<br><b>Dados:</b> [{rolls_str}] {mod_str} <br><div class='text-2xl font-bold text-green-400 mt-1'>Total = {result['total']}</div></div>"
            except Exception as e: return f"<div class='bg-red-900/50 p-3 rounded text-red-400 font-bold border border-red-800'>Erro na rolagem: {str(e)}</div>"

        docs = self.retriever.invoke(message)
        context = "\n".join([doc.page_content for doc in docs])
        history_text = "\n".join(self.chat_history[-10:]) if self.chat_history else "Nenhum histórico recente."
        
        formatted_prompt = self.prompt.format(lore=self.campaign_lore, location=player_state["location"], session_summary=self.session_summary, context=context, chat_history=history_text, action=message)
        llm_response = self.llm.invoke(formatted_prompt)
        
        hp_match = re.search(r'\[MODIFY_HP:([+-]?\d+)\]', llm_response)
        if hp_match:
            try:
                hp_change = int(hp_match.group(1)); player_state["current_hp"] += hp_change
                player_state["current_hp"] = max(0, min(player_state["max_hp"], player_state["current_hp"]))
                save_func(player_state)
                color = "red" if hp_change < 0 else "green"; action_text = "Dano Sofrido" if hp_change < 0 else "Cura Recebida"
                hp_block = f"<div class='bg-{color}-900/50 p-3 rounded border border-{color}-500 text-{color}-100 my-2 shadow-lg'>❤️ <b>{action_text}:</b> {abs(hp_change)} <br><b>HP Atual:</b> {player_state['current_hp']} / {player_state['max_hp']}</div>"
                llm_response = re.sub(r'\[MODIFY_HP:[+-]?\d+\]', hp_block, llm_response)
                self.chat_history.append(f"Sistema: O HP do jogador modificou {hp_change}. Atual: {player_state['current_hp']}/{player_state['max_hp']}.")
            except Exception as e: print(f"Erro ao processar HP: {e}")

        loc_match = re.search(r'\[CHANGE_LOCATION:(.+?)\]', llm_response)
        if loc_match:
            new_loc = loc_match.group(1).strip(); player_state["location"] = new_loc; save_func(player_state)
            loc_block = f"<div class='bg-blue-900/50 p-3 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🗺️ <b>Nova Localização:</b> {new_loc}</div>"
            llm_response = re.sub(r'\[CHANGE_LOCATION:.+?\]', loc_block, llm_response)
            self.chat_history.append(f"Sistema: O personagem viajou para {new_loc}.")

        xp_match = re.search(r'\[ADD_XP:(\d+)\]', llm_response)
        if xp_match:
            try:
                gained_xp = int(xp_match.group(1)); player_state["xp"] = player_state.get("xp", 0) + gained_xp
                cur_lvl = player_state["level"]; new_lvl = cur_lvl
                xp_table = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]
                for i, th in enumerate(xp_table):
                    if player_state["xp"] >= th: new_lvl = i + 1
                next_xp = str(xp_table[new_lvl]) if new_lvl < 20 else "Máx"
                level_up_msg = f"<br>🌟 <b>SUBIU DE NÍVEL!</b> Alcançaste o Nível {new_lvl}!" if new_lvl > cur_lvl else ""
                if new_lvl > cur_lvl: player_state["level"] = new_lvl; self.chat_history.append(f"Sistema: Nível {new_lvl}.")
                save_func(player_state)
                xp_block = f"<div class='bg-yellow-900/50 p-3 rounded border border-yellow-500 text-yellow-100 my-2 shadow-lg'>✨ <b>Experiência Recebida:</b> {gained_xp} XP<br><b>XP Total:</b> {player_state['xp']} / {next_xp} {level_up_msg}</div>"
                llm_response = re.sub(r'\[ADD_XP:\d+\]', xp_block, llm_response)
            except Exception as e: print(f"Erro XP: {e}")

        item_match = re.search(r'\[ADD_ITEM:(.+?)\]', llm_response)
        if item_match:
            try:
                new_item = item_match.group(1).strip()
                if "inventory" not in player_state: player_state["inventory"] = []
                player_state["inventory"].append(new_item)
                save_func(player_state)
                
                item_block = f"<div class='bg-emerald-900/50 p-3 rounded border border-emerald-500 text-emerald-100 my-2 shadow-lg'>🎒 <b>Item Recebido:</b> {new_item}<br><span class='text-xs opacity-75'>(Adicionado automaticamente ao teu inventário)</span></div>"
                llm_response = re.sub(r'\[ADD_ITEM:.+?\]', item_block, llm_response)
                self.chat_history.append(f"Sistema: O jogador recebeu o item '{new_item}'.")
            except Exception as e: print(f"Erro ao processar Item: {e}")

        self.chat_history.extend([f"Jogador: {message}", f"Mestre: {llm_response}"])
        html_res = f"{llm_response.replace(chr(10), '<br>')}<br><br><details><summary class='text-xs text-gray-500 cursor-pointer'>Ver Regras/Contexto</summary><i class='text-gray-600 text-xs mt-2 block'>{context[:400]}...</i></details>"
        return html_res