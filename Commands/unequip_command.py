from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager
from GameObjects.players import Player

class UnequipCommand:
    name = "unequip"
    description = "Unequip an item from a player or enemy."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Unequip",
            [
                {"name": "target", "question": "Target name?", "type": str},
                {"name": "item_type", "question": "Item type? (weapon, outfit, accessory)", "type": str},
            ]
        )

    def execute(self, params) -> Result:
        target_name = params["target"]
        item_type = params["item_type"].lower()

        target = self.db.get("Players", target_name) or self.db.get("Enemies", target_name)
        if not target:
            return {"ok": False, "error": f"No player or enemy named '{target_name}'."}

        if item_type == "weapon":
            target.unequip_weapon()
        elif item_type == "outfit":
            target.unequip_outfit()
        elif item_type == "accessory":
            slot = Prompt("Accessory slot (0-3)", int).ask()
            target.unequip_accessory(slot)
        else:
            return {"ok": False, "error": f"Unknown item type '{item_type}'."}

        obj_type = "Players" if isinstance(target, Player) else "Enemies"
        self.db.mark_dirty(obj_type, target.name)
        return {"ok": True, "message": f"Unequipped {item_type} from {target.name}."}
