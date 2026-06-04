from pydantic import BaseModel, Field, computed_field
import math
from typing import List, Dict, Any

class Attributes(BaseModel):
    """Model of the base D&D 5e ability scores."""
    strength: int = Field(default=10, ge=1, le=30, description="Strength")
    dexterity: int = Field(default=10, ge=1, le=30, description="Dexterity")
    constitution: int = Field(default=10, ge=1, le=30, description="Constitution")
    intelligence: int = Field(default=10, ge=1, le=30, description="Intelligence")
    wisdom: int = Field(default=10, ge=1, le=30, description="Wisdom")
    charisma: int = Field(default=10, ge=1, le=30, description="Charisma")

    @computed_field
    @property
    def str_mod(self) -> int: return math.floor((self.strength - 10) / 2)

    @computed_field
    @property
    def dex_mod(self) -> int: return math.floor((self.dexterity - 10) / 2)

    @computed_field
    @property
    def con_mod(self) -> int: return math.floor((self.constitution - 10) / 2)

    @computed_field
    @property
    def int_mod(self) -> int: return math.floor((self.intelligence - 10) / 2)

    @computed_field
    @property
    def wis_mod(self) -> int: return math.floor((self.wisdom - 10) / 2)

    @computed_field
    @property
    def cha_mod(self) -> int: return math.floor((self.charisma - 10) / 2)

class CharacterSheet(BaseModel):
    """Model of the complete Character Sheet."""
    name: str
    race: str = Field(default="Human", description="Character race")
    character_class: str
    level: int = Field(default=1, ge=1, le=20)
    xp: int = Field(default=0, ge=0, description="Current experience")
    location: str = Field(default="Unknown", description="Character's current location")
    attributes: Attributes = Attributes()
    max_hp: int
    current_hp: int
    armor_class: int
    inventory: List[str] = []
    features: List[str] = []
    spells: List[str] = []
    resources: Dict[str, Any] = Field(default={}, description="Class resources (e.g. Rage: {current: 2, max: 2})")
    spell_slots: Dict[str, Any] = Field(default={}, description="Spell slots per level (e.g. '1': {current: 2, max: 2})")
    action_economy: Dict[str, bool] = Field(default={"main": True, "bonus": True, "reaction": True}, description="Action economy for the turn")
    in_combat: bool = Field(default=False, description="Whether the character is in combat")
    initiative_order: List[str] = Field(default=[], description="Current initiative order")
