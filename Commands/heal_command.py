# Commands/heal_command.py
from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager


class HealCommand:
    name = "heal"
    description = "Heal a target by amount."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs("Heal", [
            {"name": "target", "question": "Target name?", "type": str},
            {"name": "amount", "question": "Heal amount?", "type": float},
        ])

    def _resolve_key_ci(self, t, name):
        low = name.lower()
        for k in self.db.list_items(t):
            if k.lower() == low: return k
        return name

    def execute(self, p) -> Result:
        name = p["target"].strip();
        amt = float(p["amount"])
        obj = self.db.get("Players", name);
        t = "Players"
        if not obj: obj = self.db.get("Enemies", name); t = "Enemies" if obj else t
        if not obj: return {"ok": False, "error": f"No such target '{name}'."}
        if not hasattr(obj, "heal"): return {"ok": False, "error": "Target lacks heal(); add it next to take_damage()."}
        out = obj.heal(amt)
        key = self._resolve_key_ci(t, name)
        self.db.mark_dirty(t, key)
        msg = f"{getattr(obj, 'name', name)} healed {out['healed']:g}. HP: {out['before']:g} → {out['after']:g}"
        return {"ok": True, "message": msg}
