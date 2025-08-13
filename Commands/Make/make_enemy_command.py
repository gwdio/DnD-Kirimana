import random
from typing import Dict, Any
from Types.prompts import PromptGroup
from Types.results import Result
from GameObjects.enemies import Enemy
from Services.database import DatabaseManager

# Descriptor mapping table
STAT_TIERS = {
    "ABYSMAL":  {"PHY": 1, "FIN": 1, "COM": 1, "MGK": 1, "CAP": 2,  "OPT": 1,  "RR": 1},
    "VERY LOW": {"PHY": 3, "FIN": 3, "COM": 3, "MGK": 5, "CAP": 3,  "OPT": 2,  "RR": 3},
    "LOW":      {"PHY": 6, "FIN": 6, "COM": 6, "MGK": 7, "CAP": 4,  "OPT": 3,  "RR": 3},
    "MID LOW":  {"PHY": 9, "FIN": 9, "COM": 9, "MGK": 10,"CAP": 5,  "OPT": 4,  "RR": 4},
    "MEDIOCRE": {"PHY": 12,"FIN": 11,"COM": 12,"MGK": 15,"CAP": 6,  "OPT": 6,  "RR": 6},
    "MID HIGH": {"PHY": 15,"FIN": 15,"COM": 15,"MGK": 18,"CAP": 7,  "OPT": 7,  "RR": 7},
    "HIGH":     {"PHY": 18,"FIN": 18,"COM": 18,"MGK": 24,"CAP": 8,  "OPT": 8,  "RR": 8},
    "VERY HIGH":{"PHY": 20,"FIN": 20,"COM": 20,"MGK": 27,"CAP": 10, "OPT": 10, "RR": 10},
    "EX":       {"PHY": 30,"FIN": 30,"COM": 30,"MGK": 45,"CAP": 16, "OPT": 16, "RR": 16},
    "EX+":      {"PHY": 50,"FIN": 50,"COM": 50,"MGK": 87,"CAP": 30, "OPT": 30, "RR": 30}
}

# Aliases
TIER_ALIASES = {
    "T": "ABYSMAL", "FFF": "ABYSMAL",
    "VL": "VERY LOW", "FF": "VERY LOW",
    "L": "LOW", "F": "LOW",
    "ML": "MID LOW", "D": "MID LOW",
    "M": "MEDIOCRE", "C": "MEDIOCRE",
    "MH": "MID HIGH", "B": "MID HIGH",
    "H": "HIGH", "A": "HIGH",
    "VH": "VERY HIGH", "S": "VERY HIGH",
    "X": "EX+", "SSS": "EX+",
    "E": "EX", "SS": "EX",
    "EX": "EX",
    "EX+": "EX+"
}

STAT_GUIDE = """
Enter stat as number or descriptor:
Abysmal/T/FFF, Very Low/VL/FF, Low/L/F, Mid Low/ML/D, Mediocre/M/C,
Mid High/MH/B, High/H/A, Very High/VH/S, EX/E/SS, EX+/X/SSS.
Use + or - to blend with the next higher/lower tier.
Example: FF+ = between Very Low and Low, FF- = between Abysmal and Very Low.
"""

def parse_stat_value(val: str, stat_name: str) -> int:
    """Parse a stat descriptor or numeric input with tier aliases, blending, and special cases."""
    val = val.strip().upper()

    # Direct number
    if val.isdigit():
        return int(val)

    # Alias sets
    abysmal_aliases = {"ABYSMAL", "T", "FFF"}
    ex_aliases = {"EX", "E", "SS"}
    ex_plus_aliases = {"EX+", "X", "SSS"}

    # 1️⃣ Abysmal floor case
    if val in {f"{alias}-" for alias in abysmal_aliases}:
        return 0

    # 2️⃣ EX+ 30% boost case: SSS+, X+, EX++
    if val in {f"{alias}+" for alias in ex_plus_aliases} or val == "EX++":
        base_val = STAT_TIERS["EX+"][stat_name]
        return int(round(base_val * 1.3))

    # 3️⃣ EX+ exact tier (no blending)
    if val in ex_plus_aliases:
        return STAT_TIERS["EX+"][stat_name]

    # 4️⃣ EX → EX+ blend case: E+, SS+ (but not EX+)
    if val in {f"{alias}+" for alias in ex_aliases}:
        base_val = STAT_TIERS["EX"][stat_name]
        target_val = STAT_TIERS["EX+"][stat_name]
        avg_val = (base_val + target_val) / 2
        return int(avg_val) if random.random() < 0.5 else int(round(avg_val))

    # Normal blending handling
    blend = 0
    if val.endswith("+"):
        blend = 1
        val = val[:-1]
    elif val.endswith("-"):
        blend = -1
        val = val[:-1]

    # Resolve alias to tier name
    tier_name = TIER_ALIASES.get(val, val)
    if tier_name not in STAT_TIERS:
        raise ValueError(f"Unknown stat tier: {val}")

    base_val = STAT_TIERS[tier_name][stat_name]

    # Standard blend logic
    if blend != 0:
        tiers = list(STAT_TIERS.keys())
        idx = tiers.index(tier_name)
        target_idx = max(0, min(len(tiers)-1, idx + blend))
        target_val = STAT_TIERS[tiers[target_idx]][stat_name]
        avg_val = (base_val + target_val) / 2
        return int(avg_val) if random.random() < 0.5 else int(round(avg_val))

    return base_val



class MakeEnemyCommand:
    name = "makeenemy"
    description = "Create a new enemy and save it to the database."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        print(STAT_GUIDE)  # Only display once at start
        return PromptGroup.from_specs("Basic Enemy Info", [
            {"name": "enemy_class", "question": "Enemy class? (grunt/other)", "type": str},
            {"name": "name", "question": "Enemy name?", "type": str},
            {"name": "species", "question": "Species?", "type": str},
            {"name": "faction", "question": "Faction?", "type": str}
        ])

    def execute(self, params: Dict[str, Any]) -> Result:
        enemy_class = params["enemy_class"].strip().lower()

        if enemy_class == "grunt":
            stage2 = PromptGroup.from_specs("Grunt Stats", [
                {"name": "level", "question": "Level?", "type": int},
                {"name": "PHY", "question": "PHY", "type": str},
                {"name": "FIN", "question": "FIN", "type": str},
                {"name": "COM", "question": "COM", "type": str},
                {"name": "CAP", "question": "CAP", "type": str},
                {"name": "OPT", "question": "OPT", "type": str},
                {"name": "RR", "question": "RR", "type": str},
            ])
            stat_inputs = stage2.ask_all()

        else:
            stage2 = PromptGroup.from_specs("Full Enemy Stats", [
                {"name": "level", "question": "Level?", "type": int},
                {"name": "PHY", "question": "PHY", "type": str},
                {"name": "FIN", "question": "FIN", "type": str},
                {"name": "COM", "question": "COM", "type": str},
                {"name": "CAP", "question": "CAP", "type": str},
                {"name": "OPT", "question": "OPT", "type": str},
                {"name": "RR", "question": "RR", "type": str},
                {"name": "gender", "question": "Gender?", "type": str, "default": "", "optional": True},
                {"name": "age", "question": "Age?", "type": int, "default": None, "optional": True},
                {"name": "position", "question": "Position?", "type": str, "default": "", "optional": True},
                {"name": "note", "question": "Note?", "type": str, "default": "", "optional": True}
            ])
            stat_inputs = stage2.ask_all()

        # Derive MGK
        cap_val = parse_stat_value(stat_inputs["CAP"], "CAP") if isinstance(stat_inputs["CAP"], str) else \
        stat_inputs["CAP"]
        opt_val = parse_stat_value(stat_inputs["OPT"], "OPT") if isinstance(stat_inputs["OPT"], str) else \
        stat_inputs["OPT"]
        rr_val = parse_stat_value(stat_inputs["RR"], "RR") if isinstance(stat_inputs["RR"], str) else stat_inputs[
            "RR"]
        stat_inputs["MGK"] = cap_val + opt_val + rr_val - 3

        # Parse descriptor values for all relevant stats
        for key in ("PHY", "FIN", "COM", "MGK", "CAP", "OPT", "RR"):
            if key in stat_inputs and isinstance(stat_inputs[key], str) and stat_inputs[key].strip():
                stat_inputs[key] = parse_stat_value(stat_inputs[key], key)

        # Build Enemy
        enemy = Enemy(
            name=params["name"],
            level=stat_inputs["level"],
            species=params["species"],
            faction=params["faction"],
            gender=stat_inputs.get("gender") or None,
            age=stat_inputs.get("age"),
            position=stat_inputs.get("position") or None,
            note=stat_inputs.get("note") or None,
            PHY=stat_inputs.get("PHY"),
            FIN=stat_inputs.get("FIN"),
            COM=stat_inputs.get("COM"),
            MGK=stat_inputs.get("MGK"),
            CAP=stat_inputs.get("CAP"),
            OPT=stat_inputs.get("OPT"),
            RR=stat_inputs.get("RR")
        )

        self.db.add_or_replace("Enemies", enemy.name, enemy)
        return {"ok": True, "message": f"✔ Enemy '{enemy.name}' created and saved to database."}
