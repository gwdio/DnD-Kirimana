from typing import Dict, Any
from Types.prompts import PromptGroup, Prompt
from Types.results import Result
from GameObjects.accessories import Accessory
from Services.database import DatabaseManager


class MakeAccessoryCommand:
    name = "makeaccessory"
    description = "Create a new accessory and save it to the database."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        # Stage 1: Basic info
        return PromptGroup.from_specs(
            "Create Accessory",
            [
                {"name": "name", "question": "Accessory name?", "type": str},
                {"name": "accessory_type", "question": "Accessory type? (e.g., ring, amulet, bracelet)", "type": str},
                {"name": "rarity", "question": "Rarity? (optional)", "type": str, "default": None, "optional": True},
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        # Stage 2: Ask if stats exist
        more_stats = Prompt(
            "Does this accessory have other stat bonuses? (y/n)",
            str
        ).ask().strip().lower() in {"y", "yes"}

        # Default stats to None if not provided
        stats = {
            "PHY": None, "FIN": None, "COM": None, "MGK": None,
            "CAP": None, "OPT": None, "RR": None, "HP": None,
            "MMAX": None, "CHN": None, "REG": None, "ACC": None, "EVA": None,
            "Other": None
        }

        if more_stats:
            # Ask for all stat bonuses
            stat_prompts = PromptGroup.from_specs(
                "Accessory Stat Bonuses",
                [
                    {"name": "PHY", "question": "Bonus PHY?", "type": int, "default": None, "optional": True},
                    {"name": "FIN", "question": "Bonus FIN?", "type": int, "default": None, "optional": True},
                    {"name": "COM", "question": "Bonus COM?", "type": int, "default": None, "optional": True},
                    {"name": "MGK", "question": "Bonus MGK?", "type": int, "default": None, "optional": True},
                    {"name": "CAP", "question": "Bonus CAP?", "type": int, "default": None, "optional": True},
                    {"name": "OPT", "question": "Bonus OPT?", "type": int, "default": None, "optional": True},
                    {"name": "RR",  "question": "Bonus RR?", "type": int, "default": None, "optional": True},
                    {"name": "HP",  "question": "Bonus HP?", "type": int, "default": None, "optional": True},
                    {"name": "MMAX", "question": "Bonus MMAX?", "type": int, "default": None, "optional": True},
                    {"name": "CHN", "question": "Bonus CHN?", "type": int, "default": None, "optional": True},
                    {"name": "REG", "question": "Bonus REG?", "type": int, "default": None, "optional": True},
                    {"name": "ACC", "question": "Bonus ACC?", "type": int, "default": None, "optional": True},
                    {"name": "EVA", "question": "Bonus EVA?", "type": int, "default": None, "optional": True},
                    {"name": "Other", "question": "Custom stat?", "type": str, "default": None, "optional": True},
                ]
            )
            stats.update(stat_prompts.ask_all())

        # Build accessory
        accessory = Accessory(
            name=params["name"],
            slot=params["accessory_type"],
            rarity=params.get("rarity"),
            **stats
        )

        # Save to DB
        self.db.add_or_replace("Accessories", accessory.name, accessory)

        return {
            "ok": True,
            "message": f"✔ Accessory '{accessory.name}' created and saved to database."
        }
