# Commands/make_command.py

from typing import Dict, Any
from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager

# Import all make commands from submodule
from Commands.Make.make_player_command import MakePlayerCommand
from Commands.Make.make_enemy_command import MakeEnemyCommand
from Commands.Make.make_weapon_command import MakeWeaponCommand
from Commands.Make.make_accessory_command import MakeAccessoryCommand
from Commands.Make.make_outfit_command import MakeOutfitCommand


MAKE_COMMANDS = {
    "player": MakePlayerCommand,
    "enemy": MakeEnemyCommand,
    "weapon": MakeWeaponCommand,
    "accessory": MakeAccessoryCommand,
    "outfit": MakeOutfitCommand
}


class MakeCommand:
    name = "make"
    description = "Create a new game object (player, enemy, weapon, accessory, outfit)."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Make Object",
            [
                {
                    "name": "obj_type",
                    "question": "What do you want to make? (player, enemy, weapon, accessory, outfit)",
                    "type": str
                }
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        obj_type = params["obj_type"].strip().lower()

        if obj_type not in MAKE_COMMANDS:
            return {
                "ok": False,
                "error": f"Unknown object type '{obj_type}'. Must be one of: {', '.join(MAKE_COMMANDS.keys())}"
            }

        cmd_cls = MAKE_COMMANDS[obj_type]
        cmd_instance = cmd_cls(self.db)

        # Stage 2: build prompts for the chosen make command
        sub_params = cmd_instance.build_prompts().ask_all()

        # Execute chosen command
        return cmd_instance.execute(sub_params)
