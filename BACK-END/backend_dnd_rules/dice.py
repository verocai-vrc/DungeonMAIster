import random
import re
from typing import Dict, Any

def roll_dice(expression: str) -> Dict[str, Any]:
    """
    Avalia uma expressão de dados de RPG (ex: '1d20+5', '2d6', '1d10-1') 
    e retorna o resultado validado no backend.
    """
    # Normaliza a expressão (remove espaços e passa para minúsculas)
    expression = expression.lower().replace(" ", "")
    
    # Regex para capturar <quantidade>d<faces><+/-modificador>
    match = re.match(r'^(\d+)d(\d+)([\+\-]\d+)?$', expression)
    
    if not match:
        raise ValueError(f"Expressão de dados inválida: {expression}")
    
    num_dice = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    
    return {
        "expression": expression,
        "rolls": rolls,
        "modifier": modifier,
        "total": total
    }