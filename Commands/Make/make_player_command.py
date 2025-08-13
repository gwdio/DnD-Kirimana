from typing import Dict, Any
from Types.prompts import PromptGroup
from Types.results import Result
from GameObjects.players import Player
from Services.database import DatabaseManager  # adjust import

class MakePlayerCommand:
    name = "makeplayer"
    description = "Create a new player and save them to the database."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Create Player",
            [
                {"name": "name", "question": "Player name?", "type": str},
                {"name": "level", "question": "Player level?", "type": int, "default": 1},
                {"name": "PHY", "question": "PHY stat?", "type": int, "default": 1},
                {"name": "FIN", "question": "FIN stat?", "type": int, "default": 1},
                {"name": "COM", "question": "COM stat?", "type": int, "default": 1},
                {"name": "MGK", "question": "MGK stat?", "type": int, "default": 1},
                {"name": "CAP", "question": "CAP stat?", "type": int, "default": 1},
                {"name": "OPT", "question": "OPT stat?", "type": int, "default": 1},
                {"name": "RR",  "question": "RR stat?", "type": int, "default": 1},
                {"name": "Other", "question": "Custom stat?", "type": str, "default": "", "optional": True},
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        # Enforce minimum stats
        for stat in ("PHY", "FIN", "COM", "MGK", "CAP", "OPT", "RR"):
            if params[stat] < 1:
                params[stat] = 1
                print(f"⚠ Stat {stat} increased to minimum value of 1.")

        # CAP+OPT+RR check
        sum_mana_substats = params["CAP"] + params["OPT"] + params["RR"]
        if sum_mana_substats != params["MGK"] + 3:
            print(f"⚠ Warning: CAP+OPT+RR = {sum_mana_substats} does not equal MGK+3 ({params['MGK'] + 3}).")

        # Create and calculate stats
        player = Player(
            name=params["name"],
            level=params["level"],
            PHY=params["PHY"],
            FIN=params["FIN"],
            COM=params["COM"],
            MGK=params["MGK"],
            CAP=params["CAP"],
            OPT=params["OPT"],
            RR=params["RR"],
            Other=params["Other"] or None
        )

        # Save to DB
        self.db.add_or_replace("Players", player.name, player)

        return {
            "ok": True,
            "message": f"✔ Player '{player.name}' created at level {player.level} and saved to database."
        }

