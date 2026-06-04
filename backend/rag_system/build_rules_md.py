"""
Converte os ficheiros JSON de regras (usados pelo frontend) em Markdown estruturado
e legível para a IA. O Markdown gerado é ingerido no RAG (ChromaDB), permitindo que o
Mestre consulte regras, classes, raças, magias e equipamento de forma autoritária.

Mesma fonte de dados, duas representações:
  - JSON  → frontend (dropdowns, tooltips)
  - Markdown → IA (chunking por cabeçalho + RAG)

Executar: python -m backend.rag_system.build_rules_md
"""
import os
import re
import sys
import html
import json

# Permite execução tanto como módulo (-m) quanto como script direto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.data_manager import (
    BASE_DIR, RACES_FILE, CLASSES_FILE, SPELLS_FILE, EQUIPMENT_FILE, ABILITIES_FILE
)

RULES_MD_DIR = os.path.join(BASE_DIR, "DATA", "rules_md")

_GENERATED_NOTE = "<!-- GERADO AUTOMATICAMENTE por build_rules_md.py — não editar à mão. -->\n\n"

_ATTR_PT = {
    "strength": "Força", "dexterity": "Destreza", "constitution": "Constituição",
    "intelligence": "Inteligência", "wisdom": "Sabedoria", "charisma": "Carisma",
}
_ARMOR_PT = {"light": "leve", "medium": "média", "heavy": "pesada", "shield": "escudo"}


def _clean(text: str) -> str:
    """Remove markup HTML das descrições, preservando o texto e o rótulo do span."""
    if not text:
        return ""
    text = text.replace("</span>", " — ")
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^\s*—\s*", "", text)        # span vazio no início
    text = re.sub(r"\s*—\s*$", "", text)         # separador pendente no fim
    return text


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_classes_md() -> str:
    data = _load(CLASSES_FILE)
    classes = data.get("classes", {})
    descriptions = data.get("descriptions", {})

    lines = [_GENERATED_NOTE, "# Classes de D&D 5e\n"]
    for name, cls in classes.items():
        lines.append(f"## {name}")
        hd = cls.get("hit_dice")
        profs = ", ".join(cls.get("proficiencies", [])) or "—"
        lines.append(f"**Dado de Vida:** d{hd} | **Proficiências de Perícia:** {profs}\n")

        feats_by_level = cls.get("features", {})
        if feats_by_level:
            lines.append("**Características por Nível:**")
            for lvl in sorted(feats_by_level, key=lambda k: int(k)):
                feats = ", ".join(feats_by_level[lvl])
                lines.append(f"- Nível {lvl}: {feats}")
            lines.append("")

        # Detalha apenas as características desta classe que possuem descrição
        all_feats = [f for fs in feats_by_level.values() for f in fs]
        detailed = [(f, descriptions[f]) for f in all_feats if f in descriptions]
        if detailed:
            lines.append("**Detalhes das Características:**")
            for feat, desc in detailed:
                lines.append(f"- **{feat}:** {_clean(desc)}")
            lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_races_md() -> str:
    data = _load(RACES_FILE)
    races = data.get("races", {})
    descriptions = data.get("descriptions", {})

    lines = [_GENERATED_NOTE, "# Raças de D&D 5e\n"]
    for name, race in races.items():
        lines.append(f"## {name}")
        attrs = race.get("attributes", {})
        if attrs:
            bonus = ", ".join(f"{_ATTR_PT.get(k, k)} +{v}" for k, v in attrs.items())
        else:
            bonus = "—"
        lines.append(f"**Bônus de Atributo:** {bonus}\n")

        feats = race.get("features", [])
        if feats:
            lines.append(f"**Traços Raciais:** {', '.join(feats)}\n")

        detailed = [(f, descriptions[f]) for f in feats if f in descriptions]
        if detailed:
            lines.append("**Detalhes dos Traços:**")
            for feat, desc in detailed:
                lines.append(f"- **{feat}:** {_clean(desc)}")
            lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_spells_md() -> str:
    data = _load(SPELLS_FILE)
    by_level = data.get("spells_by_level", {})
    descriptions = data.get("descriptions", {})

    lines = [_GENERATED_NOTE, "# Magias de D&D 5e\n"]
    for lvl in sorted(by_level, key=lambda k: int(k)):
        lines.append(f"## Magias de {lvl}º Círculo")
        for spell in by_level[lvl]:
            desc = _clean(descriptions.get(spell, ""))
            lines.append(f"- **{spell}:** {desc}" if desc else f"- **{spell}**")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _format_item(name: str, item: dict) -> str:
    desc = item.get("description", "").strip()
    status = item.get("status", {}) or {}
    specs = []

    if "damage" in status:
        dmg = status["damage"]
        dtype = status.get("damage_type", "")
        specs.append(f"Dano: {dmg} {dtype}".strip())
    if status.get("properties"):
        specs.append(f"Propriedades: {', '.join(status['properties'])}")
    if "base_ac" in status:
        atype = _ARMOR_PT.get(status.get("armor_type", ""), status.get("armor_type", ""))
        specs.append(f"CA base: {status['base_ac']} (armadura {atype})")
    if status.get("ac_bonus"):
        specs.append(f"Bônus de CA: +{status['ac_bonus']}")
    if status.get("strength_req"):
        specs.append(f"Requer Força {status['strength_req']}")
    if status.get("stealth_disadvantage"):
        specs.append("Desvantagem em Furtividade")
    if status.get("healing"):
        specs.append(f"Cura: {status['healing']}")

    spec_str = f" ({'; '.join(specs)})" if specs else ""
    return f"- **{name}**: {desc}{spec_str}"


def build_equipment_md() -> str:
    data = _load(EQUIPMENT_FILE)
    items = data.get("items", {})

    # Agrupa por tipo numa ordem estável
    groups: dict[str, list[str]] = {}
    for name, item in items.items():
        groups.setdefault(item.get("type", "Outros"), []).append(name)

    type_order = ["Arma", "Armadura", "Escudo", "Consumível", "Misc"]
    type_titles = {"Arma": "Armas", "Armadura": "Armaduras", "Escudo": "Escudos",
                   "Consumível": "Consumíveis", "Misc": "Itens Diversos"}

    ordered = [t for t in type_order if t in groups] + [t for t in groups if t not in type_order]

    lines = [_GENERATED_NOTE, "# Equipamento de D&D 5e\n"]
    for t in ordered:
        lines.append(f"## {type_titles.get(t, t)}")
        for name in groups[t]:
            lines.append(_format_item(name, items[name]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_abilities_md() -> str:
    data = _load(ABILITIES_FILE)
    descriptions = data.get("descriptions", {})
    if not descriptions:
        return ""
    lines = [_GENERATED_NOTE, "# Habilidades Diversas\n", "## Referência de Habilidades"]
    for name, desc in descriptions.items():
        lines.append(f"- **{name}:** {_clean(desc)}")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


_BUILDERS = {
    "classes.md": build_classes_md,
    "races.md": build_races_md,
    "spells.md": build_spells_md,
    "equipment.md": build_equipment_md,
    "abilities.md": build_abilities_md,
}


def build_all_rules_md() -> list[str]:
    """Gera todos os ficheiros Markdown a partir do JSON. Retorna os caminhos escritos."""
    os.makedirs(RULES_MD_DIR, exist_ok=True)
    written = []
    for filename, builder in _BUILDERS.items():
        content = builder()
        if not content.strip():
            continue
        path = os.path.join(RULES_MD_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    print(f"[build_rules_md] {len(written)} ficheiro(s) Markdown gerado(s) em {RULES_MD_DIR}")
    return written


if __name__ == "__main__":
    build_all_rules_md()
