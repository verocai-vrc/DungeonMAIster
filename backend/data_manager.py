import os
import json

# Caminhos para os ficheiros e diretórios
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

def init_data_files():
    """Cria os ficheiros de regras divididos por categoria se não existirem."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    
    equipment_data = {
        "items": {
            "Adaga": {
                "type": "Arma", "name": "Adaga", 
                "description": "Arma corpo-a-corpo simples. 1d4 de dano perfurante.", 
                "status": {"damage": "1d4", "damage_type": "perfurante", "properties": ["acuidade", "leve", "arremesso"]}
            },
            "Arco Longo": {
                "type": "Arma", "name": "Arco Longo", 
                "description": "Arma à distância. 1d8 de dano perfurante.", 
                "status": {"damage": "1d8", "damage_type": "perfurante", "properties": ["munição", "pesado", "duas mãos"]}
            },
            "Machado Grande": {
                "type": "Arma", "name": "Machado Grande", 
                "description": "Machado de um guerreiro furioso. 1d12 de dano cortante.", 
                "status": {"damage": "1d12", "damage_type": "cortante", "properties": ["pesado", "duas mãos"]}
            },
            "Armadura de Couro": {
                "type": "Armadura", "name": "Armadura de Couro", 
                "description": "Armadura leve. CA 11 + Modificador de Destreza.", 
                "status": {"armor_type": "light", "base_ac": 11}
            },
            "Brunea": {
                "type": "Armadura", "name": "Brunea", 
                "description": "Armadura média (escamas). CA 14 + Modificador de Destreza (máx 2). Desvantagem em Furtividade.", 
                "status": {"armor_type": "medium", "base_ac": 14, "stealth_disadvantage": True}
            },
            "Cota de Malha": {
                "type": "Armadura", "name": "Cota de Malha", 
                "description": "Armadura pesada. CA 16. Requer For 13. Desvantagem em Furtividade.", 
                "status": {"armor_type": "heavy", "base_ac": 16, "strength_req": 13, "stealth_disadvantage": True}
            },
            "Placas": {
                "type": "Armadura", "name": "Placas", 
                "description": "Armadura pesada. CA 18. Requer For 15. Desvantagem em Furtividade.", 
                "status": {"armor_type": "heavy", "base_ac": 18, "strength_req": 15, "stealth_disadvantage": True}
            },
            "Escudo": {
                "type": "Escudo", "name": "Escudo", 
                "description": "Concede +2 na sua Classe de Armadura.", 
                "status": {"ac_bonus": 2}
            },
            "Poção de Cura": {
                "type": "Consumível", "name": "Poção de Cura", 
                "description": "Um personagem que beber o líquido deste frasco recupera 2d4+2 pontos de vida.", 
                "status": {"healing": "2d4+2"}
            },
            "Mochila do Aventureiro": {
                "type": "Misc", "name": "Mochila do Aventureiro", 
                "description": "Equipamento contendo cordas, tochas, rações, e outras necessidades de viagem.", 
                "status": {}
            }
        }
    }

    spells_data = {
        "spells_by_level": { "1": ["Mísseis Mágicos", "Curar Ferimentos", "Escudo Arcano"], "2": ["Passo Nebuloso", "Arma Espiritual"] },
        "descriptions": {
            "Mísseis Mágicos": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Ação Principal | Custo: 1 Spell Slot</span>Crias três dardos mágicos brilhantes. Cada dardo atinge uma criatura e causa 1d4+1 de dano de energia.",
            "Curar Ferimentos": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Ação Principal | Custo: 1 Spell Slot</span>Uma criatura que você toca recupera pontos de vida iguais a 1d8 + seu modificador.",
            "Escudo Arcano": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Reação | Custo: 1 Spell Slot</span>Uma barreira invisível aparece e protege você. Ganha +5 de bônus na CA até seu próximo turno.",
            "Passo Nebuloso": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Ação Bônus | Custo: 1 Spell Slot</span>Você é cercado por névoa e teletransporta-se até 9 metros.",
            "Arma Espiritual": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Ação Bônus | Custo: 1 Spell Slot</span>Você cria uma arma flutuante espectral que atinge uma criatura."
        }
    }

    abilities_data = { "features": [], "descriptions": { "Ataque Furtivo": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passiva</span>Você sabe como atacar sutilmente. Causa dano extra se tiver vantagem." } }

    races_data = {
        "races": {
            "Humano": { "attributes": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1}, "features": ["Deslocamento 9m"] },
            "Elfo": { "attributes": {"dexterity": 2}, "features": ["Visão no Escuro", "Ancestralidade Feérica", "Transe"] },
            "Anão": { "attributes": {"constitution": 2}, "features": ["Visão no Escuro", "Resiliência Anã", "Treinamento Anão"] },
            "Halfling": { "attributes": {"dexterity": 2}, "features": ["Sorte", "Bravura", "Agilidade Halfling"] },
            "Orc": { "attributes": {"strength": 2, "constitution": 1}, "features": ["Visão no Escuro", "Ataque Selvagem", "Resistência Implacável"] }
        },
        "descriptions": { "Ataque Selvagem": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passiva</span>Acertos críticos causam dano extra massivo.", "Resistência Implacável": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passiva | 1/Descanso Longo</span>Quando cai para 0 HP, pode escolher cair para 1 HP em vez disso (1/descanso longo)." }
    }

    classes_data = {
        "classes": {
            "Bárbaro": { "hit_dice": 12, "proficiencies": ["Atletismo", "Intimidação"], "features": { "1": ["Fúria", "Defesa sem Armadura"], "2": ["Ataque Temerário"], "3": ["Caminho Primitivo"] } },
            "Guerreiro": { "hit_dice": 10, "proficiencies": ["Acrobacia", "Sobrevivência"], "features": { "1": ["Estilo de Luta", "Retomar o Fôlego"], "2": ["Surto de Ação"], "3": ["Arquétipo Marcial"] } },
            "Ladino": { "hit_dice": 8, "proficiencies": ["Furtividade", "Prestidigitação", "Enganação"], "features": { "1": ["Ataque Furtivo", "Gíria de Ladrão", "Especialização"], "2": ["Ação Astuta"], "3": ["Arquétipo Rogino"] } },
            "Mago": { "hit_dice": 6, "proficiencies": ["Arcanismo", "História"], "features": { "1": ["Conjuração", "Recuperação Arcana"], "2": ["Tradição Arcana"], "3": ["Truques Adicionais"] } },
            "Clérigo": { "hit_dice": 8, "proficiencies": ["Religião", "Medicina"], "features": { "1": ["Conjuração", "Domínio Divino"], "2": ["Canalizar Divindade (1/descanso)"], "3": ["Magias de Domínio"] } },
            "Feiticeiro": { "hit_dice": 6, "proficiencies": ["Arcanismo", "Enganação"], "features": { "1": ["Conjuração", "Origem Feiticeira"], "2": ["Fonte de Magia"], "3": ["Metamágica"] } }
        },
        "descriptions": { "Fúria": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Ação Bônus | Custo: 1 Fúria</span>Em batalha, você luta com ferocidade primitiva.", "Defesa sem Armadura": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passiva</span>Enquanto não usar armadura, CA = 10 + Mod DES + Mod CON." }
    }

    def write_json_merge(file_path, default_data):
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f: json.dump(default_data, f, ensure_ascii=False, indent=4)
        else:
            with open(file_path, "r", encoding="utf-8") as f: current_data = json.load(f)
            updated = False
            for key, val in default_data.items():
                if key not in current_data:
                    current_data[key] = val; updated = True
                elif isinstance(val, dict):
                    if not isinstance(current_data.get(key), dict):
                        current_data[key] = val; updated = True
                    else:
                        for subkey, subval in val.items():
                            if subkey not in current_data[key] or (key == "descriptions" and "<span" in subval and "<span" not in current_data[key].get(subkey, "")):
                                current_data[key][subkey] = subval; updated = True
            if updated:
                with open(file_path, "w", encoding="utf-8") as f: json.dump(current_data, f, ensure_ascii=False, indent=4)

    for fp, dat in [(EQUIPMENT_FILE, equipment_data), (SPELLS_FILE, spells_data), (ABILITIES_FILE, abilities_data), (RACES_FILE, races_data), (CLASSES_FILE, classes_data)]:
        write_json_merge(fp, dat)

def load_character():
    if os.path.exists(CHAR_FILE):
        try:
            with open(CHAR_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception as e: print(f"Erro ao carregar ficha salva: {e}")
    return { "name": "Tharok", "race": "Humano", "character_class": "Bárbaro", "level": 1, "xp": 0, "location": "Taverna do Pônei Saltitante", "attributes": { "strength": 16, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 10, "charisma": 12 }, "max_hp": 14, "current_hp": 14, "armor_class": 14, "inventory": ["Machado Grande", "Poção de Cura"], "features": ["Deslocamento 9m", "Fúria", "Defesa sem Armadura"], "spells": [], "resources": {"Fúria": {"current": 2, "max": 2}}, "spell_slots": {}, "action_economy": {"main": True, "bonus": True, "reaction": True}, "in_combat": False, "initiative_order": [] }

def save_character(state):
    try:
        with open(CHAR_FILE, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar ficha: {e}")