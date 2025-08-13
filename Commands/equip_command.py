from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager
from GameObjects.players import Player
from GameObjects.weapons import Weapon
from GameObjects.accessories import Accessory
from GameObjects.outfits import Outfit

class EquipCommand:
    name = "equip"
    description = "Equip an item to a player or enemy."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Equip",
            [
                {"name": "target", "question": "Target name?", "type": str},
                {"name": "item_type", "question": "Item type? (weapon, outfit, accessory)", "type": str},
            ]
        )

    def execute(self, params) -> Result:
        target_name = params["target"]
        item_type = params["item_type"].lower()

        # Load target (check players first, then enemies)
        target = self.db.load_object("Players", target_name) or self.db.load_object("Enemies", target_name)
        if not target:
            return {"ok": False, "error": f"No player or enemy named '{target_name}'."}

        # Prompt for item name
        item_name = Prompt("Item name?", str).ask().strip()
        if not item_name:
            return {"ok": False, "error": "No item name given."}

        # Load item
        if item_type == "weapon":
            item = self.db.load_object("Weapons", item_name)
            if not isinstance(item, Weapon):
                return {"ok": False, "error": f"'{item_name}' is not a weapon."}
            target.equip_weapon(item)

        elif item_type == "outfit":
            item = self.db.load_object("Outfits", item_name)
            if not isinstance(item, Outfit):
                return {"ok": False, "error": f"'{item_name}' is not an outfit."}
            target.equip_outfit(item)

        elif item_type == "accessory":
            # Ask for slot if accessory
            slot = Prompt("Accessory slot (0-3, optional)", int, default=None, optional=True).ask()
            item = self.db.load_object("Accessories", item_name)
            if not isinstance(item, Accessory):
                return {"ok": False, "error": f"'{item_name}' is not an accessory."}
            target.equip_accessory(item, slot or 0)

        else:
            return {"ok": False, "error": f"Unknown item type '{item_type}'."}

        # Save target back to DB
        obj_type = "Players" if isinstance(target, Player) else "Enemies"
        self.db.save(target, obj_type, target.name)
        return {"ok": True, "message": f"Equipped {item_name} to {target.name}."}
