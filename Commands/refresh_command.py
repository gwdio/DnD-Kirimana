from typing import Dict, Any
from Types.prompts import PromptGroup
from Types.results import Result
from GameObjects.players import Player
from GameObjects.enemies import Enemy
from Services.database import DatabaseManager

SINGULAR_MAP = {
    "Players": "Player",
    "Enemies": "Enemy",
    "Weapons": "Weapon",
    "Accessories": "Accessory",
    "Outfits": "Outfit"
}

class RefreshCommand:
    name = "refresh"
    description = "Recalculate stats and reapply equips for a target or all players/enemies."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Refresh Command",
            [
                {"name": "target", "question": "Target name? (leave blank for all)", "type": str, "default": ""}
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        target_name = params.get("target", "").strip()

        affected = []
        if not target_name:
            for folder, cls in (("Players", Player), ("Enemies", Enemy)):
                for name in self.db.list_items(folder):
                    obj = self.db.load(folder, name, cls=cls)
                    if obj:
                        obj.refresh()
                        self.db.save(obj, folder, obj.name)
                        folder_display = SINGULAR_MAP.get(folder, folder.rstrip("s"))
                        affected.append(f"{folder_display}: {obj.name}")
        else:
            obj = self.db.load("Players", target_name, cls=Player)
            if not obj:
                obj = self.db.load("Enemies", target_name, cls=Enemy)
            if obj:
                obj.refresh()
                folder = "Players" if isinstance(obj, Player) else "Enemies"
                self.db.save(obj, folder, obj.name)
                folder_display = SINGULAR_MAP.get(folder, folder.rstrip("s"))
                affected.append(f"{folder_display}: {obj.name}")
            else:
                return {"ok": False, "error": f"No player or enemy named '{target_name}' found."}

        return {"ok": True, "message": f"✔ Refreshed: {', '.join(affected)}"}
