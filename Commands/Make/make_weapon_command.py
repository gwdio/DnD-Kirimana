from typing import Dict, Any
from Types.prompts import PromptGroup, Prompt
from Types.results import Result
from GameObjects.weapons import Weapon
from Services.database import DatabaseManager


class MakeWeaponCommand:
    name = "makeweapon"
    description = "Create a new weapon and save it to the database."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        # Stage 1: Basic weapon info
        return PromptGroup.from_specs(
            "Create Weapon",
            [
                {"name": "name", "question": "Weapon name?", "type": str},
                {"name": "weapon_type", "question": "Weapon type? (e.g., Sword, Bow, Staff)", "type": str},
                {"name": "rarity", "question": "Rarity? (optional)", "type": str, "default": None, "optional": True},
                {"name": "PHY_mod", "question": "PHY modifier?", "type": int, "default": 0},
                {"name": "ACC_mod", "question": "ACC modifier?", "type": int, "default": 0},
                {"name": "reach", "question": "Reach? (Meters)", "type": int, "default": 1},
                {"name": "weight", "question": "Weight? (e.g., Light, Medium, Heavy)", "type": str, "default": None, "optional": True},
                {"name": "conductivity", "question": "Conductivity? (float or comma-separated triple)", "type": str, "default": None, "optional": True},
                {"name": "control", "question": "Control requirement?", "type": int, "default": 0},
                {"name": "damage_type", "question": "Damage type? (string or comma-separated list)", "type": str, "default": None, "optional": True},
                {"name": "ATKM", "question": "Attack accuracy modifier?", "type": int, "default": 0},
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        # Ask if weapon has other stat bonuses
        more_stats = Prompt(
            "Does this weapon have other stat bonuses? (y/n)",
            str
        ).ask().strip().lower() in {"y", "yes"}

        stats = {
            "PHY": None, "FIN": None, "COM": None, "MGK": None,
            "CAP": None, "OPT": None, "RR": None,
            "Other": None
        }

        if more_stats:
            stat_prompts = PromptGroup.from_specs(
                "Weapon Stat Bonuses",
                [
                    {"name": "PHY", "question": "Bonus PHY? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "FIN", "question": "Bonus FIN? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "COM", "question": "Bonus COM? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "MGK", "question": "Bonus MGK? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "CAP", "question": "Bonus CAP? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "OPT", "question": "Bonus OPT? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "RR",  "question": "Bonus RR? (optional)", "type": int, "default": None, "optional": True},
                    {"name": "Other", "question": "Custom stat (optional)?", "type": str, "default": None, "optional": True},
                ]
            )
            stats.update(stat_prompts.ask_all())

        # Ensure control stat is valid
        if params["control"] < 0:
            params["control"] = 0
            print("⚠ Control stat increased to minimum value of 0.")

        # Parse conductivity
        cond = None
        if params["conductivity"]:
            if isinstance(params["conductivity"], str) and "," in params["conductivity"]:
                parts = params["conductivity"].split(",")
                try:
                    cond = tuple(float(x.strip()) for x in parts)
                except ValueError:
                    print("⚠ Invalid conductivity triple, defaulting to None.")
            else:
                try:
                    cond = float(params["conductivity"])
                except (TypeError, ValueError):
                    print("⚠ Invalid conductivity value, defaulting to None.")

        # Parse damage type
        dmg_type = None
        if params["damage_type"]:
            if isinstance(params["damage_type"], str) and "," in params["damage_type"]:
                dmg_type = [x.strip() for x in params["damage_type"].split(",")]
            else:
                dmg_type = params["damage_type"]

        # Create weapon object
        weapon = Weapon(
            name=params["name"],
            weapon_type=params["weapon_type"],
            rarity=params.get("rarity"),
            PHY_mod=params["PHY_mod"],
            ACC_mod=params["ACC_mod"],
            reach=params["reach"],
            weight=params.get("weight"),
            conductivity=cond,
            control=params["control"],
            damage_type=dmg_type,
            ATKM=params["ATKM"],
            **stats
        )

        # Save to DB
        self.db.save(weapon, "Weapons", weapon.name)

        return {
            "ok": True,
            "message": f"✔ Weapon '{weapon.name}' created and saved to database."
        }
