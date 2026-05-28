from pydantic import BaseModel, Field, computed_field
import math
from typing import List, Dict, Any

class Attributes(BaseModel):
    """Modelo dos atributos base de D&D 5e."""
    strength: int = Field(default=10, ge=1, le=30, description="Força")
    dexterity: int = Field(default=10, ge=1, le=30, description="Destreza")
    constitution: int = Field(default=10, ge=1, le=30, description="Constituição")
    intelligence: int = Field(default=10, ge=1, le=30, description="Inteligência")
    wisdom: int = Field(default=10, ge=1, le=30, description="Sabedoria")
    charisma: int = Field(default=10, ge=1, le=30, description="Carisma")

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
    """Modelo da Ficha Completa do Personagem."""
    name: str
    race: str = Field(default="Humano", description="Raça do personagem")
    character_class: str
    level: int = Field(default=1, ge=1, le=20)
    xp: int = Field(default=0, ge=0, description="Experiência atual")
    location: str = Field(default="Desconhecido", description="Localização atual do personagem")
    attributes: Attributes = Attributes()
    max_hp: int
    current_hp: int
    armor_class: int
    inventory: List[str] = []
    features: List[str] = []
    spells: List[str] = []
    resources: Dict[str, Any] = Field(default={}, description="Recursos de classe (ex: Fúria: {current: 2, max: 2})")
    spell_slots: Dict[str, Any] = Field(default={}, description="Espaços de magia por nível (ex: '1': {current: 2, max: 2})")
    action_economy: Dict[str, bool] = Field(default={"main": True, "bonus": True, "reaction": True}, description="Economia de ação no turno")
    in_combat: bool = Field(default=False, description="Indica se o personagem está em combate")
    initiative_order: List[str] = Field(default=[], description="Ordem de iniciativa atual")