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

class RestCommand:
    name = "rest"
    description = "Restore HP and Mana for a target or all players/enemies."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Rest Command",
            [
                {"name": "target", "question": "Target name? (leave blank for all)", "type": str, "default": ""}
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        target_name = params.get("target", "").strip()

        def rest_entity(entity):
            entity.stats.hp_current = int(entity.stats.HP)
            entity.stats.mana_current = int(entity.stats.MMAX)

        affected = []
        if not target_name:
            for folder, cls in (("Players", Player), ("Enemies", Enemy)):
                for name in self.db.list_items(folder):
                    obj = self.db.get(folder, name)
                    if obj:
                        rest_entity(obj)
                        self.db.mark_dirty(folder, obj.name)
                        folder_display = SINGULAR_MAP.get(folder, folder.rstrip("s"))
                        affected.append(f"{folder_display}: {obj.name}")
        else:
            obj = self.db.get("Players", target_name)
            if not obj:
                obj = self.db.get("Enemies", target_name)
            if obj:
                rest_entity(obj)
                folder = "Players" if isinstance(obj, Player) else "Enemies"
                self.db.mark_dirty(folder, obj.name)
                folder_display = SINGULAR_MAP.get(folder, folder.rstrip("s"))
                affected.append(f"{folder_display}: {obj.name}")
            else:
                return {"ok": False, "error": f"No player or enemy named '{target_name}' found."}

        return {"ok": True, "message": f"✔ Rested: {', '.join(affected)}"}
