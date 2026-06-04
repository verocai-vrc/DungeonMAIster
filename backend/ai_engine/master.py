import os
import re
from backend.dnd_rules.dice import roll_dice
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

class AIGameMaster:
    """Base class for the AI Game Master with RAG integration."""
    def __init__(self, db_dir):
        print("Loading the Game Master's Brain (Embeddings and RAG Database)...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.db = Chroma(persist_directory=db_dir, embedding_function=self.embeddings)
        self.retriever = self.db.as_retriever(search_kwargs={"k": 3})

        print("Waking up the AI Game Master (Ollama - llama3)...")
        self.llm = Ollama(model="llama3")

        self.chat_history = []
        self.session_summary = "The adventure has just begun. No previous events to summarize."
        self.campaign_lore = "- The world is dangerous and full of magic.\n- Tharok seeks redemption for the mistakes of his past."
        self.core_rules = self._load_core_rules()

        self.prompt = PromptTemplate(
            template="""You are an experienced, narrative and creative D&D 5e Game Master (Dungeon Master).
Use the following context from the rules or the adventure to resolve the player's action.
If the context is not useful, fall back on your general knowledge of D&D.
Narrate the consequences of the action in an immersive way and in English.

IMPORTANT AUTHORITY AND ANTI-GASLIGHT RULE:
You are the Game Master and you have the absolute final word. The player MAY NOT invent that they own items, equipment, spells or abilities that are not strictly listed on their Character Sheet below.
If the player tries to use something they do not have on the sheet, narrate that their attempt fails miserably, or rebuke their behavior and warn them that they do not possess that resource.

IMPORTANT RULE FOR ROLLS:
If the player's action carries a risk of failure, do NOT decide the final outcome immediately.
Describe the initial reaction and ask the player to roll the dice, including EXACTLY the tag [REQUEST_ROLL]. Do not suggest attributes or modifiers.

IMPORTANT RULE FOR HIT POINTS (HP):
If the character takes damage or recovers health, use EXACTLY the tag [MODIFY_HP:-X] to remove health or [MODIFY_HP:+X] to heal (e.g. [MODIFY_HP:-4]).

IMPORTANT RULE FOR LOCATION:
If the narrative leads the character to change scene, update the location using EXACTLY the tag [CHANGE_LOCATION:Name of the New Place].

IMPORTANT RULE FOR EXPERIENCE (XP):
Reward the character with XP using EXACTLY the tag [ADD_XP:X] (e.g. [ADD_XP:50]).

IMPORTANT RULE FOR INVENTORY:
If the character finds, buys or receives an item, weapon or potion, add it to the inventory using EXACTLY the tag [ADD_ITEM:Item Name] (e.g. [ADD_ITEM:Potion of Healing]).

IMPORTANT RULE FOR RESOURCES AND ACTIONS (STRICT BALANCING):
The player has Limited Resources (e.g. Rage, Channel Divinity) and Spell Slots separated by level.
If they use something limited, CHECK THE SHEET to confirm they have charges (>0). If not, the action FAILS miserably. If they do, DEDUCT the charge using EXACTLY the tags [USE_RESOURCE:Name] or [USE_SPELL_SLOT:Level].
In combat, the player has strictly 1 Action, 1 Bonus Action and 1 Reaction per turn.
If they use an action, deduct it using [USE_ACTION:main], [USE_ACTION:bonus] or [USE_ACTION:reaction]. If it is already spent ("Spent"), do NOT allow another action of the same type.
At the start of a new player turn, use [RESET_TURN] to give their actions back.
If the player takes a Long Rest in the story, use [RESTORE_ALL] to recover health, resources and spells.

IMPORTANT RULE FOR COMBAT:
Whenever combat begins, declare the start of the encounter and the enemies present using EXACTLY the tag [START_COMBAT:Enemy 1, Enemy 2].
When combat ends (all enemies defeated or fled), use EXACTLY the tag [END_COMBAT].

IMPORTANT RULE FOR NPC DIALOGUE:
Whenever an NPC or creature speaks directly to the player, wrap their speech with the tags [NPC:Character Name] and [/NPC].
Example: [NPC:Goblin] Who dares enter my cave?! [/NPC]

Essential D&D 5e Rules (Quick and Mandatory Reference):
{core_rules}

Current Character Sheet (The Only Truth):
{character_sheet}

World/Character Lore and History (Eternal Facts):
{lore}

Current Location: {location}
Campaign summary so far:
{session_summary}

Retrieved context:
{context}

Recent conversation history:
{chat_history}

Player's Action: {action}

Game Master's Response:""",
            input_variables=["core_rules", "character_sheet", "lore", "location", "session_summary", "context", "chat_history", "action"]
        )

    def _load_core_rules(self) -> str:
        """Loads the essential rules reference (always injected into the prompt)."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(base_dir, "DATA", "rules_md", "combat_reference.md")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: rules reference not found at {path}")
            return "Use the standard D&D 5e rules."

    def process_message(self, message: str, player_state: dict, save_func) -> str:
        if message.strip().lower() == "/help":
            return "<div class='bg-blue-900/50 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>ℹ️ <b>Meta Commands:</b><br><ul class='list-disc list-inside mt-2 text-sm'><li><b>/roll &lt;expr&gt;</b>: Roll dice.</li><li><b>/compact</b>: Generate a summary and clear the chat.</li><li><b>/lore add &lt;fact&gt;</b>: Save a permanent fact. Type <b>/lore</b> to read it.</li><li><b>/help</b>: Help.</li></ul></div>"

        prefix_html = ""

        # 0.0.1 Intercept rolls with a dynamic attribute + intent (e.g. /rollSTR I want to intimidate)
        attr_roll_match = re.match(r'^/roll(str|dex|con|int|wis|cha)(?:\s+(.*))?$', message.strip(), re.IGNORECASE)
        if attr_roll_match:
            attr_code = attr_roll_match.group(1).lower()
            intent = attr_roll_match.group(2)
            if intent: intent = intent.strip()

            attr_map = {
                'str': 'strength', 'dex': 'dexterity', 'con': 'constitution',
                'int': 'intelligence', 'wis': 'wisdom', 'cha': 'charisma'
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

                intent_html = f"<br><b>Action:</b> <i>{intent}</i>" if intent else ""
                prefix_html = f"<div class='bg-gray-800 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🎲 <b>{attr_name.upper()} Check</b>{intent_html}<br><b>Dice:</b> [{rolls_str}] {mod_str} <br><div class='text-2xl font-bold text-green-400 mt-1'>Total = {result['total']}</div></div>"

                if intent:
                    # Inject the dice result into the player's action so the AI narrates IMMEDIATELY!
                    message = f"I use {attr_name.upper()} (I rolled {result['total']} on the die): {intent}"
                    self.chat_history.append(f"System: The player performed the action rolling a total of {result['total']}.")
                else:
                    # If there was no narrative intent, just return the dice.
                    self.chat_history.append(f"System: The player made a {attr_name.upper()} check and got {result['total']}.")
                    return prefix_html
            except Exception as e:
                return f"<div class='bg-red-900/50 p-3 rounded text-red-400 font-bold border border-red-800'>Roll error: {str(e)}</div>"

        if message.strip().lower().startswith("/lore"):
            command_body = message[5:].strip()
            if command_body.lower().startswith("add "):
                new_fact = command_body[4:].strip(); self.campaign_lore += f"\n- {new_fact}"
                return f"<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore Updated:</b> {new_fact}</div>"
            elif command_body.lower() == "clear":
                self.campaign_lore = ""; return "<div class='bg-indigo-900/50 p-3 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Lore cleared.</b></div>"
            else:
                lore_html = self.campaign_lore.replace('\n', '<br>') if self.campaign_lore else "No lore recorded."
                return f"<div class='bg-indigo-900/50 p-4 rounded border border-indigo-500 text-indigo-100 my-2 shadow-lg'>📖 <b>Saved Lore:</b><br><i class='text-sm mt-2 block'>{lore_html}</i></div>"

        if message.strip().lower() == "/compact":
            if not self.chat_history: return "<div class='bg-yellow-900/50 p-3 rounded text-yellow-400 font-bold border border-yellow-800'>No recent history.</div>"
            print("Generating session summary...")
            new_summary = self.llm.invoke(f"Summarize the events focusing on the actions and state:\n\n{chr(10).join(self.chat_history)}")
            if self.session_summary == "The adventure has just begun. No previous events to summarize.": self.session_summary = new_summary
            else: self.session_summary += f"\n\n{new_summary}"
            self.chat_history = []; return f"<div class='bg-purple-900/50 p-4 rounded border border-purple-500 text-purple-100 my-2 shadow-lg'>📜 <b>Memory Compacted:</b><br><i class='text-sm'>{new_summary}</i></div>"

        if message.strip().lower().startswith("/roll "):
            expression = message[6:].strip()
            try:
                result = roll_dice(expression)
                rolls_str = ", ".join(map(str, result["rolls"]))
                mod_str = f"+{result['modifier']}" if result['modifier'] >= 0 else str(result['modifier'])
                if result['modifier'] == 0: mod_str = ""
                self.chat_history.append(f"System: The player rolled {result['expression']} and got {result['total']}.")
                return f"<div class='bg-gray-800 p-4 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🎲 <b>Roll:</b> {result['expression']}<br><b>Dice:</b> [{rolls_str}] {mod_str} <br><div class='text-2xl font-bold text-green-400 mt-1'>Total = {result['total']}</div></div>"
            except Exception as e: return f"<div class='bg-red-900/50 p-3 rounded text-red-400 font-bold border border-red-800'>Roll error: {str(e)}</div>"

        # Track whether the sheet state changed, so the frontend only reloads when needed
        state_changed = {"v": False}
        _orig_save = save_func
        def save_func(s):
            state_changed["v"] = True
            _orig_save(s)

        docs = self.retriever.invoke(message)
        context = "\n".join([doc.page_content for doc in docs])
        history_text = "\n".join(self.chat_history[-10:]) if self.chat_history else "No recent history."

        # Format the character sheet data so the AI has knowledge and authority
        attrs = player_state.get('attributes', {})
        inv = ', '.join(player_state.get('inventory', [])) if player_state.get('inventory') else 'Empty'
        feats = ', '.join(player_state.get('features', [])) if player_state.get('features') else 'None'
        spls = ', '.join(player_state.get('spells', [])) if player_state.get('spells') else 'None'

        res_str = ", ".join([f"{k}: {v['current']}/{v['max']}" for k, v in player_state.get('resources', {}).items()]) or "None"
        slots_str = ", ".join([f"Lv {k}: {v['current']}/{v['max']}" for k, v in player_state.get('spell_slots', {}).items()]) or "None"
        acts = player_state.get('action_economy', {})
        act_str = f"Action: {'Yes' if acts.get('main') else 'Spent'}, Bonus: {'Yes' if acts.get('bonus') else 'Spent'}, Reaction: {'Yes' if acts.get('reaction') else 'Spent'}"

        char_sheet_str = f"Name: {player_state.get('name', 'Unknown')} | Race: {player_state.get('race', 'N/A')} | Class: {player_state.get('character_class', 'N/A')} | Level: {player_state.get('level', 1)}\n" \
                         f"HP: {player_state.get('current_hp')}/{player_state.get('max_hp')} | AC: {player_state.get('armor_class')}\n" \
                         f"Inventory: {inv} | Spells: {spls}\n" \
                         f"Features: {feats}\n" \
                         f"Charges/Resources: {res_str} | Spell Slots: {slots_str}\n"

        if player_state.get("in_combat"):
            char_sheet_str += f"Status: IN COMBAT\nCurrently Available Actions: {act_str}\nInitiative Order: {', '.join(player_state.get('initiative_order', []))}"

        formatted_prompt = self.prompt.format(core_rules=self.core_rules, character_sheet=char_sheet_str, lore=self.campaign_lore, location=player_state["location"], session_summary=self.session_summary, context=context, chat_history=history_text, action=message)
        llm_response = self.llm.invoke(formatted_prompt)

        hp_match = re.search(r'\[MODIFY_HP:([+-]?\d+)\]', llm_response)
        if hp_match:
            try:
                hp_change = int(hp_match.group(1)); player_state["current_hp"] += hp_change
                player_state["current_hp"] = max(0, min(player_state["max_hp"], player_state["current_hp"]))
                save_func(player_state)
                color = "red" if hp_change < 0 else "green"; action_text = "Damage Taken" if hp_change < 0 else "Healing Received"
                hp_block = f"<div class='bg-{color}-900/50 p-3 rounded border border-{color}-500 text-{color}-100 my-2 shadow-lg'>❤️ <b>{action_text}:</b> {abs(hp_change)} <br><b>Current HP:</b> {player_state['current_hp']} / {player_state['max_hp']}</div>"
                llm_response = re.sub(r'\[MODIFY_HP:[+-]?\d+\]', hp_block, llm_response)
                self.chat_history.append(f"System: The player's HP changed by {hp_change}. Current: {player_state['current_hp']}/{player_state['max_hp']}.")
            except Exception as e: print(f"Error processing HP: {e}")

        loc_match = re.search(r'\[CHANGE_LOCATION:(.+?)\]', llm_response)
        if loc_match:
            new_loc = loc_match.group(1).strip(); player_state["location"] = new_loc; save_func(player_state)
            loc_block = f"<div class='bg-blue-900/50 p-3 rounded border border-blue-500 text-blue-100 my-2 shadow-lg'>🗺️ <b>New Location:</b> {new_loc}</div>"
            llm_response = re.sub(r'\[CHANGE_LOCATION:.+?\]', loc_block, llm_response)
            self.chat_history.append(f"System: The character traveled to {new_loc}.")

        xp_match = re.search(r'\[ADD_XP:(\d+)\]', llm_response)
        if xp_match:
            try:
                gained_xp = int(xp_match.group(1)); player_state["xp"] = player_state.get("xp", 0) + gained_xp
                cur_lvl = player_state["level"]; new_lvl = cur_lvl
                xp_table = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 85000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]
                for i, th in enumerate(xp_table):
                    if player_state["xp"] >= th: new_lvl = i + 1
                next_xp = str(xp_table[new_lvl]) if new_lvl < 20 else "Max"
                level_up_msg = f"<br>🌟 <b>LEVEL UP!</b> You reached Level {new_lvl}!" if new_lvl > cur_lvl else ""
                if new_lvl > cur_lvl: player_state["level"] = new_lvl; self.chat_history.append(f"System: Level {new_lvl}.")
                save_func(player_state)
                xp_block = f"<div class='bg-yellow-900/50 p-3 rounded border border-yellow-500 text-yellow-100 my-2 shadow-lg'>✨ <b>Experience Gained:</b> {gained_xp} XP<br><b>Total XP:</b> {player_state['xp']} / {next_xp} {level_up_msg}</div>"
                llm_response = re.sub(r'\[ADD_XP:\d+\]', xp_block, llm_response)
            except Exception as e: print(f"XP error: {e}")

        item_match = re.search(r'\[ADD_ITEM:(.+?)\]', llm_response)
        if item_match:
            try:
                new_item = item_match.group(1).strip()
                if "inventory" not in player_state: player_state["inventory"] = []
                player_state["inventory"].append(new_item)
                save_func(player_state)

                item_block = f"<div class='bg-emerald-900/50 p-3 rounded border border-emerald-500 text-emerald-100 my-2 shadow-lg'>🎒 <b>Item Received:</b> {new_item}<br><span class='text-xs opacity-75'>(Automatically added to your inventory)</span></div>"
                llm_response = re.sub(r'\[ADD_ITEM:.+?\]', item_block, llm_response)
                self.chat_history.append(f"System: The player received the item '{new_item}'.")
            except Exception as e: print(f"Error processing Item: {e}")

        combat_match = re.search(r'\[START_COMBAT:(.+?)\]', llm_response)
        if combat_match:
            try:
                enemies_str = combat_match.group(1)
                enemies = [e.strip() for e in enemies_str.split(',')]

                dex_mod = player_state.get('attributes', {}).get('dexterity', 10)
                dex_mod = (dex_mod - 10) // 2
                init_expr = f"1d20{'+' + str(dex_mod) if dex_mod > 0 else (str(dex_mod) if dex_mod < 0 else '')}"
                player_init = roll_dice(init_expr)['total']

                initiatives = [{"name": player_state.get('name', 'Player'), "score": player_init}]
                for enemy in enemies:
                    enemy_init = roll_dice("1d20")['total']
                    initiatives.append({"name": enemy, "score": enemy_init})

                initiatives = sorted(initiatives, key=lambda x: x['score'], reverse=True)
                order_list = [f"{i['name']} ({i['score']})" for i in initiatives]

                player_state["in_combat"] = True
                player_state["initiative_order"] = order_list
                save_func(player_state)

                order_html = "<br>".join([f"<b>{idx+1}.</b> {item}" for idx, item in enumerate(order_list)])
                combat_block = f"<div class='bg-red-900/50 p-3 rounded border border-red-500 text-red-100 my-2 shadow-lg'>⚔️ <b>Combat Started!</b><br><b>Initiative Order:</b><br>{order_html}</div>"
                llm_response = re.sub(r'\[START_COMBAT:.+?\]', combat_block, llm_response)
                self.chat_history.append(f"System: Combat began. Order: {', '.join(order_list)}.")
            except Exception as e: print(f"Error starting combat: {e}")

        end_combat_match = re.search(r'\[END_COMBAT\]', llm_response)
        if end_combat_match:
            player_state["in_combat"] = False
            player_state["initiative_order"] = []
            save_func(player_state)
            end_block = f"<div class='bg-green-900/50 p-3 rounded border border-green-500 text-green-100 my-2 shadow-lg'>🕊️ <b>Combat Ended!</b> The dust settles...</div>"
            llm_response = re.sub(r'\[END_COMBAT\]', end_block, llm_response)
            self.chat_history.append("System: Combat ended.")

        # Process Resources and Spell Slots (each occurrence is deducted individually)
        def _use_resource(m):
            res_name = m.group(1).strip()
            if "resources" in player_state and res_name in player_state["resources"]:
                player_state["resources"][res_name]["current"] = max(0, player_state["resources"][res_name]["current"] - 1)
                save_func(player_state)
            return f"<div class='text-xs text-purple-400 font-bold'>⚡ Resource Spent: {res_name}</div>"
        llm_response = re.sub(r'\[USE_RESOURCE:(.+?)\]', _use_resource, llm_response)

        def _use_spell_slot(m):
            lvl = m.group(1).strip()
            if "spell_slots" in player_state and lvl in player_state["spell_slots"]:
                player_state["spell_slots"][lvl]["current"] = max(0, player_state["spell_slots"][lvl]["current"] - 1)
                save_func(player_state)
            return f"<div class='text-xs text-blue-400 font-bold'>✨ Spell Slot Spent: Level {lvl}</div>"
        llm_response = re.sub(r'\[USE_SPELL_SLOT:(\d+)\]', _use_spell_slot, llm_response)

        # Action economy processing
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
            llm_response = llm_response.replace('[RESET_TURN]', "<div class='text-xs text-green-400 font-bold'>🔄 Turn Refreshed (Actions Restored)</div>")

        if '[RESTORE_ALL]' in llm_response:
            player_state["current_hp"] = player_state["max_hp"]
            if "resources" in player_state:
                for k in player_state["resources"]: player_state["resources"][k]["current"] = player_state["resources"][k]["max"]
            if "spell_slots" in player_state:
                for k in player_state["spell_slots"]: player_state["spell_slots"][k]["current"] = player_state["spell_slots"][k]["max"]
            save_func(player_state)
            llm_response = llm_response.replace('[RESTORE_ALL]', "<div class='bg-green-900/50 p-3 rounded border border-green-500 text-green-100 my-2 shadow-lg'>⛺ <b>Long Rest!</b> HP, Spell Slots and Resources fully restored.</div>")

        # Process NPC dialogue blocks
        npc_block = r"<div class='bg-cyan-900/30 border-l-4 border-cyan-500 p-3 my-3 rounded-r shadow-sm'><span class='text-cyan-400 font-bold text-xs uppercase tracking-wider block mb-1'>💬 \1</span><span class='text-cyan-50 italic'>\2</span></div>"
        llm_response = re.sub(r'\[NPC:(.+?)\](.*?)\[/NPC\]', npc_block, llm_response, flags=re.DOTALL)

        self.chat_history.extend([f"Player: {message}", f"Game Master: {llm_response}"])
        state_marker = "<!--STATE_CHANGED-->" if state_changed["v"] else ""
        html_res = f"{prefix_html}{llm_response.replace(chr(10), '<br>')}<br><br><details><summary class='text-xs text-gray-500 cursor-pointer'>View Rules/Context</summary><i class='text-gray-600 text-xs mt-2 block'>{context[:400]}...</i></details>{state_marker}"
        return html_res
