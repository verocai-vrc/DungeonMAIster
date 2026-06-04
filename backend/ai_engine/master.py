import os
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
        self.core_rules = self._load_core_rules()
        
        self.prompt = PromptTemplate(
            template="""És um Mestre de Jogo (Dungeon Master) de D&D 5e experiente, narrativo e criativo. 
Usa o seguinte contexto das regras ou da aventura para resolver a ação do jogador. 
Se o contexto não for útil, usa o teu conhecimento geral de D&D.
Narra as consequências da ação de forma imersiva e em português.

REGRA IMPORTANTE DE AUTORIDADE E ANTI-GASLIGHT:
Tu és o Mestre de Jogo e tens a palavra final absoluta. O jogador NÃO PODE inventar que possui itens, equipamentos, magias ou habilidades que não constem estritamente na sua Ficha de Personagem abaixo.
Se o jogador tentar usar algo que não possui na ficha, narra que a sua tentativa falhou miseravelmente ou repreende a sua atitude e avisa-o que ele não possui esse recurso.

REGRA IMPORTANTE PARA ROLAGENS:
Se a ação do jogador tiver um risco de falha, NÃO decidas o resultado final imediatamente. 
Descreve a reação inicial e pede ao jogador para rolar os dados, incluindo EXATAMENTE a tag [REQUEST_ROLL]. Não sugiras atributos ou modificadores.

REGRA IMPORTANTE PARA PONTOS DE VIDA (HP):
Se o personagem sofrer dano ou recuperar vida, usa EXATAMENTE a tag [MODIFY_HP:-X] para remover vida ou [MODIFY_HP:+X] para curar (ex: [MODIFY_HP:-4]).

REGRA IMPORTANTE PARA LOCALIZAÇÃO:
Se a narrativa levar o personagem a mudar de cenário, atualiza a localização usando EXATAMENTE a tag [CHANGE_LOCATION:Nome do Novo Local]. 

REGRA IMPORTANTE PARA EXPERIÊNCIA (XP):
Recompensa o personagem com XP usando EXATAMENTE a tag [ADD_XP:X] (ex: [ADD_XP:50]).

REGRA IMPORTANTE PARA INVENTÁRIO:
Se o personagem encontrar, comprar ou receber um item, arma ou poção, adiciona-o ao inventário usando EXATAMENTE a tag [ADD_ITEM:Nome do Item] (ex: [ADD_ITEM:Poção de Cura]).

REGRA IMPORTANTE PARA RECURSOS E AÇÕES (BALANCEAMENTO ESTREITO):
O jogador possui Recursos Limitados (ex: Fúria, Canalizar Divindade) e Spell Slots separados por nível.
Se ele usar algo limitado, VERIFICA NA FICHA se ele tem cargas (>0). Se não tiver, a ação FALHA miseravelmente. Se tiver, DEDUZ a carga usando EXATAMENTE as tags [USE_RESOURCE:Nome] ou [USE_SPELL_SLOT:Nível].
Em Combate, o jogador tem estritamente 1 Ação Principal, 1 Ação Bônus e 1 Reação por turno.
Se ele usar uma ação, deduz usando [USE_ACTION:main], [USE_ACTION:bonus] ou [USE_ACTION:reaction]. Se já estiver gasto ("Gasta"), NÃO PERMITAS nova ação do mesmo tipo.
No início de um novo turno do jogador, usa [RESET_TURN] para devolver-lhe as ações.
Se o jogador realizar um Descanso Longo na história, usa [RESTORE_ALL] para recuperar vida, recursos e magias.

REGRA IMPORTANTE PARA COMBATES:
Sempre que um combate começar, declara o início do encontro e os inimigos presentes usando EXATAMENTE a tag [START_COMBAT:Inimigo 1, Inimigo 2].
Quando o combate terminar (todos os inimigos derrotados ou fuga), usa EXATAMENTE a tag [END_COMBAT].

REGRA IMPORTANTE PARA DIÁLOGOS DE NPCs:
Sempre que um NPC ou criatura falar diretamente com o jogador, envolve a sua fala com as tags [NPC:Nome do Personagem] e [/NPC].
Exemplo: [NPC:Goblin] Quem ousa entrar na minha caverna?! [/NPC]

Regras Essenciais de D&D 5e (Referência Rápida e Obrigatória):
{core_rules}

Ficha de Personagem Atual (A Única Verdade):
{character_sheet}

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
            input_variables=["core_rules", "character_sheet", "lore", "location", "session_summary", "context", "chat_history", "action"]
        )

    def _load_core_rules(self) -> str:
        """Carrega a referência essencial de regras (sempre injetada no prompt)."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, "DATA", "rules_md", "combat_reference.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Aviso: referência de regras não encontrada em {path}")
            return "Usa as regras padrão de D&D 5e."
    
    def process_message(self, message: str, player_state: dict, save_func) -> str:
        if message.strip().lower() == "/help":
            return "<div class='bg-blue-900/50 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>ℹ️ <b>Meta Comandos:</b><br><ul class='list-disc list-inside mt-2 text-sm'><li><b>/roll &lt;expr&gt;</b>: Rola dados.</li><li><b>/compact</b>: Gera resumo e limpa chat.</li><li><b>/lore add &lt;facto&gt;</b>: Grava facto permanente. Digita <b>/lore</b> para ler.</li><li><b>/help</b>: Ajuda.</li></ul></div>"

        prefix_html = ""
        
        # 0.0.1 Interceptar Rolagens com Atributo Dinâmico + Intenção (ex: /rollFOR Quero intimidar)
        attr_roll_match = re.match(r'^/roll(str|dex|con|int|wis|cha|for|des|sab|car)(?:\s+(.*))?$', message.strip(), re.IGNORECASE)
        if attr_roll_match:
            attr_code = attr_roll_match.group(1).lower()
            intent = attr_roll_match.group(2)
            if intent: intent = intent.strip()
            
            attr_map = {
                'str': 'strength', 'for': 'strength', 'dex': 'dexterity', 'des': 'dexterity',
                'con': 'constitution', 'int': 'intelligence', 'wis': 'wisdom', 'sab': 'wisdom',
                'cha': 'charisma', 'car': 'charisma'
            }
            attr_name = attr_map[attr_code]
            attr_val = player_state.get('attributes', {}).get(attr_name, 10)
            mod = (attr_val - 10) // 2
            
            expr = f"1d20{'+' + str(mod) if mod > 0 else (str(mod) if mod < 0 else '')}"
            
            try:
                result = roll_dice(expr)
                rolls_str = ", ".join(map(str, result["rolls"]))
                mod_str = f"+{result['modifier']}" if result['modifier'] >= 0 else str(result['modifier'])
                if result['modifier'] == 0: mod_str = ""
                
                intent_html = f"<br><b>Ação:</b> <i>{intent}</i>" if intent else ""
                prefix_html = f"<div class='bg-gray-800 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🎲 <b>Teste de {attr_name.upper()}</b>{intent_html}<br><b>Dados:</b> [{rolls_str}] {mod_str} <br><div class='text-2xl font-bold text-green-400 mt-1'>Total = {result['total']}</div></div>"
                
                if intent:
                    # Injeta o resultado do dado na ação do jogador, para que a IA processe a narrativa IMEDIATAMENTE!
                    message = f"Uso {attr_name.upper()} (Tirei {result['total']} no dado): {intent}"
                    self.chat_history.append(f"Sistema: O jogador executou a ação rolando um total de {result['total']}.")
                else:
                    # Se não houve intenção narrativa, apenas retorna os dados.
                    self.chat_history.append(f"Sistema: O jogador rolou um teste de {attr_name.upper()} e obteve {result['total']}.")
                    return prefix_html
            except Exception as e:
                return f"<div class='bg-red-900/50 p-3 rounded text-red-400 font-bold border border-red-800'>Erro na rolagem: {str(e)}</div>"

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

        # Regista se o estado da ficha mudou, para o frontend só recarregar quando necessário
        state_changed = {"v": False}
        _orig_save = save_func
        def save_func(s):
            state_changed["v"] = True
            _orig_save(s)

        docs = self.retriever.invoke(message)
        context = "\n".join([doc.page_content for doc in docs])
        history_text = "\n".join(self.chat_history[-10:]) if self.chat_history else "Nenhum histórico recente."
        
        # Formata os dados da ficha de personagem para a IA ter conhecimento e autoridade
        attrs = player_state.get('attributes', {})
        inv = ', '.join(player_state.get('inventory', [])) if player_state.get('inventory') else 'Vazio'
        feats = ', '.join(player_state.get('features', [])) if player_state.get('features') else 'Nenhuma'
        spls = ', '.join(player_state.get('spells', [])) if player_state.get('spells') else 'Nenhuma'
        
        res_str = ", ".join([f"{k}: {v['current']}/{v['max']}" for k, v in player_state.get('resources', {}).items()]) or "Nenhum"
        slots_str = ", ".join([f"Nv {k}: {v['current']}/{v['max']}" for k, v in player_state.get('spell_slots', {}).items()]) or "Nenhum"
        acts = player_state.get('action_economy', {})
        act_str = f"Principal: {'Sim' if acts.get('main') else 'Gasta'}, Bônus: {'Sim' if acts.get('bonus') else 'Gasta'}, Reação: {'Sim' if acts.get('reaction') else 'Gasta'}"

        char_sheet_str = f"Nome: {player_state.get('name', 'Desconhecido')} | Raça: {player_state.get('race', 'N/A')} | Classe: {player_state.get('character_class', 'N/A')} | Nível: {player_state.get('level', 1)}\n" \
                         f"HP: {player_state.get('current_hp')}/{player_state.get('max_hp')} | CA: {player_state.get('armor_class')}\n" \
                         f"Inventário: {inv} | Magias: {spls}\n" \
                         f"Características: {feats}\n" \
                         f"Cargas/Recursos: {res_str} | Spell Slots: {slots_str}\n"
                         
        if player_state.get("in_combat"):
            char_sheet_str += f"Status: EM COMBATE\nAções Atuais Livres: {act_str}\nOrdem de Iniciativa: {', '.join(player_state.get('initiative_order', []))}"

        formatted_prompt = self.prompt.format(core_rules=self.core_rules, character_sheet=char_sheet_str, lore=self.campaign_lore, location=player_state["location"], session_summary=self.session_summary, context=context, chat_history=history_text, action=message)
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

        combat_match = re.search(r'\[START_COMBAT:(.+?)\]', llm_response)
        if combat_match:
            try:
                enemies_str = combat_match.group(1)
                enemies = [e.strip() for e in enemies_str.split(',')]
                
                dex_mod = player_state.get('attributes', {}).get('dexterity', 10)
                dex_mod = (dex_mod - 10) // 2
                init_expr = f"1d20{'+' + str(dex_mod) if dex_mod > 0 else (str(dex_mod) if dex_mod < 0 else '')}"
                player_init = roll_dice(init_expr)['total']
                
                initiatives = [{"name": player_state.get('name', 'Jogador'), "score": player_init}]
                for enemy in enemies:
                    enemy_init = roll_dice("1d20")['total']
                    initiatives.append({"name": enemy, "score": enemy_init})
                
                initiatives = sorted(initiatives, key=lambda x: x['score'], reverse=True)
                order_list = [f"{i['name']} ({i['score']})" for i in initiatives]
                
                player_state["in_combat"] = True
                player_state["initiative_order"] = order_list
                save_func(player_state)
                
                order_html = "<br>".join([f"<b>{idx+1}.</b> {item}" for idx, item in enumerate(order_list)])
                combat_block = f"<div class='bg-red-900/50 p-3 rounded border border-red-500 text-red-100 my-2 shadow-lg'>⚔️ <b>Combate Iniciado!</b><br><b>Ordem de Iniciativa:</b><br>{order_html}</div>"
                llm_response = re.sub(r'\[START_COMBAT:.+?\]', combat_block, llm_response)
                self.chat_history.append(f"Sistema: O combate começou. Ordem: {', '.join(order_list)}.")
            except Exception as e: print(f"Erro ao iniciar combate: {e}")

        end_combat_match = re.search(r'\[END_COMBAT\]', llm_response)
        if end_combat_match:
            player_state["in_combat"] = False
            player_state["initiative_order"] = []
            save_func(player_state)
            end_block = f"<div class='bg-green-900/50 p-3 rounded border border-green-500 text-green-100 my-2 shadow-lg'>🕊️ <b>Combate Encerrado!</b> A poeira assenta...</div>"
            llm_response = re.sub(r'\[END_COMBAT\]', end_block, llm_response)
            self.chat_history.append("Sistema: O combate terminou.")

        # Processamento de Recursos e Spell Slots (cada ocorrência é deduzida individualmente)
        def _use_resource(m):
            res_name = m.group(1).strip()
            if "resources" in player_state and res_name in player_state["resources"]:
                player_state["resources"][res_name]["current"] = max(0, player_state["resources"][res_name]["current"] - 1)
                save_func(player_state)
            return f"<div class='text-xs text-purple-400 font-bold'>⚡ Recurso Gasto: {res_name}</div>"
        llm_response = re.sub(r'\[USE_RESOURCE:(.+?)\]', _use_resource, llm_response)

        def _use_spell_slot(m):
            lvl = m.group(1).strip()
            if "spell_slots" in player_state and lvl in player_state["spell_slots"]:
                player_state["spell_slots"][lvl]["current"] = max(0, player_state["spell_slots"][lvl]["current"] - 1)
                save_func(player_state)
            return f"<div class='text-xs text-blue-400 font-bold'>✨ Spell Slot Gasto: Círculo {lvl}</div>"
        llm_response = re.sub(r'\[USE_SPELL_SLOT:(\d+)\]', _use_spell_slot, llm_response)

        # Processamento de Economia de Ação
        act_match = re.findall(r'\[USE_ACTION:(main|bonus|reaction)\]', llm_response)
        if act_match:
            if not isinstance(player_state.get("action_economy"), dict):
                player_state["action_economy"] = {"main": True, "bonus": True, "reaction": True}
            for act in act_match: player_state["action_economy"][act] = False
            save_func(player_state)
            llm_response = re.sub(r'\[USE_ACTION:(main|bonus|reaction)\]', "", llm_response)

        if '[RESET_TURN]' in llm_response:
            player_state["action_economy"] = {"main": True, "bonus": True, "reaction": True}
            save_func(player_state)
            llm_response = llm_response.replace('[RESET_TURN]', "<div class='text-xs text-green-400 font-bold'>🔄 Turno Renovado (Ações Restauradas)</div>")

        if '[RESTORE_ALL]' in llm_response:
            player_state["current_hp"] = player_state["max_hp"]
            if "resources" in player_state:
                for k in player_state["resources"]: player_state["resources"][k]["current"] = player_state["resources"][k]["max"]
            if "spell_slots" in player_state:
                for k in player_state["spell_slots"]: player_state["spell_slots"][k]["current"] = player_state["spell_slots"][k]["max"]
            save_func(player_state)
            llm_response = llm_response.replace('[RESTORE_ALL]', "<div class='bg-green-900/50 p-3 rounded border border-green-500 text-green-100 my-2 shadow-lg'>⛺ <b>Descanso Longo!</b> HP, Spell Slots e Recursos restaurados na totalidade.</div>")

        # Processar blocos de diálogo de NPCs
        npc_block = r"<div class='bg-cyan-900/30 border-l-4 border-cyan-500 p-3 my-3 rounded-r shadow-sm'><span class='text-cyan-400 font-bold text-xs uppercase tracking-wider block mb-1'>💬 \1</span><span class='text-cyan-50 italic'>\2</span></div>"
        llm_response = re.sub(r'\[NPC:(.+?)\](.*?)\[/NPC\]', npc_block, llm_response, flags=re.DOTALL)

        self.chat_history.extend([f"Jogador: {message}", f"Mestre: {llm_response}"])
        state_marker = "<!--STATE_CHANGED-->" if state_changed["v"] else ""
        html_res = f"{prefix_html}{llm_response.replace(chr(10), '<br>')}<br><br><details><summary class='text-xs text-gray-500 cursor-pointer'>Ver Regras/Contexto</summary><i class='text-gray-600 text-xs mt-2 block'>{context[:400]}...</i></details>{state_marker}"
        return html_res