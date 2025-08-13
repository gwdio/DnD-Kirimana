from __future__ import annotations
from typing import Dict, Any
from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager
from GameObjects.players import Player
from GameObjects.enemies import Enemy

class DamageCommand:
    name = "damage"
    description = "Deal raw damage to a target (player or enemy). Usage: damage <target> <amount>"

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        # Supports interactive use when args are missing
        return PromptGroup.from_specs("Damage", [
            {"name": "target", "question": "Target name?", "type": str},
            {"name": "amount", "question": "Damage amount?", "type": float},
        ])

    def _resolve_key_ci(self, obj_type: str, name: str) -> str:
        """Case-insensitive disk key resolution for mark_dirty/commit."""
        lower = name.strip().lower()
        for k in self.db.list_items(obj_type):
            if k.lower() == lower:
                return k
        return name

    def execute(self, params: Dict[str, Any]) -> Result:
        target_name = (params.get("target") or "").strip()
        try:
            amount = float(params.get("amount"))
        except Exception:
            return {"ok": False, "error": "Invalid or missing damage amount."}

        # Find target in Players first, then Enemies
        obj = self.db.get("Players", target_name)
        obj_type = "Players"
        if not obj:
            obj = self.db.get("Enemies", target_name)
            obj_type = "Enemies" if obj else obj_type

        if not obj:
            return {"ok": False, "error": f"No such target '{target_name}' in Players or Enemies."}

        # Apply damage using the helper on the object
        if not hasattr(obj, "take_damage"):
            return {"ok": False, "error": f"Target '{target_name}' has no take_damage() method. Please add it."}

        outcome = obj.take_damage(amount)
        before = outcome["before"]
        after = outcome["after"]
        dead = bool(outcome["dead"])

        # Persist
        key = self._resolve_key_ci(obj_type, target_name)
        self.db.mark_dirty(obj_type, key)

        # Message
        display_name = getattr(obj, "name", target_name)
        msg_lines = [f"{display_name} took {amount:g} damage. HP: {before:g} → {after:g}"]
        if dead:
            msg_lines.append(f"{display_name} should be dead")

        return {"ok": True, "message": "\n".join(msg_lines)}
