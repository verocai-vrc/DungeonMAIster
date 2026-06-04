import os
import json

# Paths to files and directories
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
    """Creates the category-split rules files if they do not exist."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)

    equipment_data = {
        "items": {
            "Dagger": {
                "type": "Weapon", "name": "Dagger",
                "description": "Simple melee weapon. 1d4 piercing damage.",
                "status": {"damage": "1d4", "damage_type": "piercing", "properties": ["finesse", "light", "thrown"]}
            },
            "Longbow": {
                "type": "Weapon", "name": "Longbow",
                "description": "Ranged weapon. 1d8 piercing damage.",
                "status": {"damage": "1d8", "damage_type": "piercing", "properties": ["ammunition", "heavy", "two-handed"]}
            },
            "Greataxe": {
                "type": "Weapon", "name": "Greataxe",
                "description": "The axe of a furious warrior. 1d12 slashing damage.",
                "status": {"damage": "1d12", "damage_type": "slashing", "properties": ["heavy", "two-handed"]}
            },
            "Leather Armor": {
                "type": "Armor", "name": "Leather Armor",
                "description": "Light armor. AC 11 + Dexterity modifier.",
                "status": {"armor_type": "light", "base_ac": 11}
            },
            "Scale Mail": {
                "type": "Armor", "name": "Scale Mail",
                "description": "Medium armor (scales). AC 14 + Dexterity modifier (max 2). Disadvantage on Stealth.",
                "status": {"armor_type": "medium", "base_ac": 14, "stealth_disadvantage": True}
            },
            "Chain Mail": {
                "type": "Armor", "name": "Chain Mail",
                "description": "Heavy armor. AC 16. Requires Str 13. Disadvantage on Stealth.",
                "status": {"armor_type": "heavy", "base_ac": 16, "strength_req": 13, "stealth_disadvantage": True}
            },
            "Plate Armor": {
                "type": "Armor", "name": "Plate Armor",
                "description": "Heavy armor. AC 18. Requires Str 15. Disadvantage on Stealth.",
                "status": {"armor_type": "heavy", "base_ac": 18, "strength_req": 15, "stealth_disadvantage": True}
            },
            "Shield": {
                "type": "Shield", "name": "Shield",
                "description": "Grants +2 to your Armor Class.",
                "status": {"ac_bonus": 2}
            },
            "Potion of Healing": {
                "type": "Consumable", "name": "Potion of Healing",
                "description": "A character who drinks the liquid in this vial regains 2d4+2 hit points.",
                "status": {"healing": "2d4+2"}
            },
            "Explorer's Pack": {
                "type": "Misc", "name": "Explorer's Pack",
                "description": "Gear containing rope, torches, rations, and other travel necessities.",
                "status": {}
            }
        }
    }

    spells_data = {
        "spells_by_level": { "1": ["Magic Missile", "Cure Wounds", "Shield"], "2": ["Misty Step", "Spiritual Weapon"] },
        "descriptions": {
            "Magic Missile": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Action | Cost: 1 Spell Slot</span>You create three glowing magical darts. Each dart hits a creature and deals 1d4+1 force damage.",
            "Cure Wounds": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Action | Cost: 1 Spell Slot</span>A creature you touch regains hit points equal to 1d8 + your modifier.",
            "Shield": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Reaction | Cost: 1 Spell Slot</span>An invisible barrier appears and protects you. You gain a +5 bonus to AC until your next turn.",
            "Misty Step": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Bonus Action | Cost: 1 Spell Slot</span>You are surrounded by mist and teleport up to 30 feet.",
            "Spiritual Weapon": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Bonus Action | Cost: 1 Spell Slot</span>You create a floating spectral weapon that strikes a creature."
        }
    }

    abilities_data = { "features": [], "descriptions": { "Sneak Attack": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passive</span>You know how to strike subtly. You deal extra damage when you have advantage." } }

    races_data = {
        "races": {
            "Human": { "attributes": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1, "charisma": 1}, "features": ["Speed 30 ft."] },
            "Elf": { "attributes": {"dexterity": 2}, "features": ["Darkvision", "Fey Ancestry", "Trance"] },
            "Dwarf": { "attributes": {"constitution": 2}, "features": ["Darkvision", "Dwarven Resilience", "Dwarven Combat Training"] },
            "Halfling": { "attributes": {"dexterity": 2}, "features": ["Lucky", "Brave", "Halfling Nimbleness"] },
            "Half-Orc": { "attributes": {"strength": 2, "constitution": 1}, "features": ["Darkvision", "Savage Attacks", "Relentless Endurance"] }
        },
        "descriptions": { "Savage Attacks": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passive</span>Critical hits deal massive extra damage.", "Relentless Endurance": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passive | 1/Long Rest</span>When you drop to 0 HP, you can choose to drop to 1 HP instead (1/long rest)." }
    }

    classes_data = {
        "classes": {
            "Barbarian": { "hit_dice": 12, "proficiencies": ["Athletics", "Intimidation"], "features": { "1": ["Rage", "Unarmored Defense"], "2": ["Reckless Attack"], "3": ["Primal Path"] } },
            "Fighter": { "hit_dice": 10, "proficiencies": ["Acrobatics", "Survival"], "features": { "1": ["Fighting Style", "Second Wind"], "2": ["Action Surge"], "3": ["Martial Archetype"] } },
            "Rogue": { "hit_dice": 8, "proficiencies": ["Stealth", "Sleight of Hand", "Deception"], "features": { "1": ["Sneak Attack", "Thieves' Cant", "Expertise"], "2": ["Cunning Action"], "3": ["Roguish Archetype"] } },
            "Wizard": { "hit_dice": 6, "proficiencies": ["Arcana", "History"], "features": { "1": ["Spellcasting", "Arcane Recovery"], "2": ["Arcane Tradition"], "3": ["Additional Cantrips"] } },
            "Cleric": { "hit_dice": 8, "proficiencies": ["Religion", "Medicine"], "features": { "1": ["Spellcasting", "Divine Domain"], "2": ["Channel Divinity (1/rest)"], "3": ["Domain Spells"] } },
            "Sorcerer": { "hit_dice": 6, "proficiencies": ["Arcana", "Deception"], "features": { "1": ["Spellcasting", "Sorcerous Origin"], "2": ["Font of Magic"], "3": ["Metamagic"] } }
        },
        "descriptions": { "Rage": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Bonus Action | Cost: 1 Rage</span>In battle, you fight with primal ferocity.", "Unarmored Defense": "<span class='text-purple-400 font-bold text-[10px] uppercase block mb-1'>⚡ Passive</span>While not wearing armor, AC = 10 + DEX Mod + CON Mod." }
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
        except Exception as e: print(f"Error loading saved sheet: {e}")
    return { "name": "Tharok", "race": "Human", "character_class": "Barbarian", "level": 1, "xp": 0, "location": "The Prancing Pony Tavern", "attributes": { "strength": 16, "dexterity": 14, "constitution": 15, "intelligence": 8, "wisdom": 10, "charisma": 12 }, "max_hp": 14, "current_hp": 14, "armor_class": 14, "inventory": ["Greataxe", "Potion of Healing"], "features": ["Speed 30 ft.", "Rage", "Unarmored Defense"], "spells": [], "resources": {"Rage": {"current": 2, "max": 2}}, "spell_slots": {}, "action_economy": {"main": True, "bonus": True, "reaction": True}, "in_combat": False, "initiative_order": [] }

def save_character(state):
    try:
        with open(CHAR_FILE, "w", encoding="utf-8") as f: json.dump(state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving sheet: {e}")
