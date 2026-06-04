import random
import re
from typing import Dict, Any

def roll_dice(expression: str) -> Dict[str, Any]:
    """
    Evaluates an RPG dice expression (e.g. '1d20+5', '2d6', '1d10-1')
    and returns the result validated on the backend.
    """
    # Normalize the expression (strip spaces and lowercase it)
    expression = expression.lower().replace(" ", "")

    # Regex to capture <quantity>d<faces><+/-modifier>
    match = re.match(r'^(\d+)d(\d+)([\+\-]\d+)?$', expression)

    if not match:
        raise ValueError(f"Invalid dice expression: {expression}")

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
