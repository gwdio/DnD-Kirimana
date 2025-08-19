from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Sequence

from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Types.stats import to_modifier
from Services.database import DatabaseManager
from GameObjects.players import Player
from GameObjects.enemies import Enemy

C_CONST = 3.5  # c in scaling

# -------------------------
# Small, readable helpers
# -------------------------

def S(o):  # stats object (BaseStats)
    return getattr(o, "stats")

def n(x, d=0.0):  # numeric with default
    return d if x is None else float(x)

def level(o) -> int:
    return int(getattr(o, "level", getattr(o, "Level", 0)) or 0)

def finm(o) -> int:
    return to_modifier(int(n(S(o).FIN, 0)))

def commm(o) -> int:
    return to_modifier(int(n(S(o).COM, 0)))

def conductivity_of(o) -> Tuple[Optional[float], Optional[Tuple[float,float,float]]]:
    """Return (scalar, lanes) from o.stats.conductivity."""
    cond = getattr(S(o), "conductivity", None)
    if cond is None:
        return (None, None)
    if isinstance(cond, (int, float)):
        return (float(cond), None)
    if isinstance(cond, Sequence) and not isinstance(cond, (str, bytes)) and len(cond) == 3:
        return (None, (float(cond[0]), float(cond[1]), float(cond[2])))
    return (None, None)

def acc_value(attacker, roll: float, atkm_extra: float, distance: float, extra_reach: float) -> float:
    # ACC = FINM + roll + ATKM (ACC_mod + additional) - max((Distance - (reach + extra reach)), 0)/10
    st = S(attacker)
    atkm_total = n(getattr(st, "ATKM", 0.0)) + n(getattr(st, "ACC_mod", 0.0)) + n(atkm_extra, 0.0)
    reach_total = n(getattr(st, "reach", 0.0)) + n(extra_reach, 0.0)
    penalty = max(distance - reach_total, 0.0) / 10.0
    return finm(attacker) + float(roll) + atkm_total - penalty

def eva_value(attacker, defender) -> float:
    # EVA = 5 + FINM_def + (def_level - att_level)
    return 5.0 + finm(defender) + (level(defender) - level(attacker))

def scaling(acc: float, eva: float) -> float:
    return (max(acc - eva, 0.0) + C_CONST) / 20.0

def effective_phy(attacker, extra_phy: float, physical_component: bool) -> float:
    if not physical_component:
        return 0.0
    st = S(attacker)
    return n(getattr(st, "PHY", 0.0)) + n(extra_phy, 0.0)

def effective_opt(mana_spent: float, cond_scalar: float) -> float:
    return n(mana_spent, 0.0) * n(cond_scalar, 0.0)

def env_damage_raw(eff_phy: float, eff_opt: float) -> float:
    # FX_mult omitted (default 1.0 as per spec)
    return 1.5 * eff_phy + 3.0 * eff_opt

def parse_scalings(s: Optional[str]) -> List[float]:
    if not s: return [1.0]
    s = s.strip()
    if not s: return [1.0]
    if "," in s:
        return [float(p.strip()) for p in s.split(",") if p.strip()]
    return [float(s)]

# -------------------------
# Command
# -------------------------

@dataclass
class HitBundle:
    hit: bool
    acc: float
    eva: float
    sc: float
    sc14: float
    dmg: int
    env: float

class AttackCommand:
    name = "attack"
    description = "Resolve a standard attack or counter using the game’s formulas."

    def __init__(self, db: DatabaseManager):
        self.db = db

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs("Attack", [
            {"name": "attacker", "question": "Attacker name?", "type": str},
            {"name": "target", "question": "Target name?", "type": str},
            {"name": "sophistication", "question": "Sophistication (L/M/H)?", "type": str, "default": "M"},
            {"name": "counter", "question": "Is this a counter? (y/n)", "type": bool, "default": False},
        ])

    # Case-insensitive key resolve for dirty-marking
    def _key_match(self, obj_type: str, name: str) -> str:
        lower = name.strip().lower()
        for k in self.db.list_items(obj_type):
            if k.lower() == lower:
                return k
        return name

    def execute(self, params: Dict[str, Any]) -> Result:
        rng = random.Random()

        attacker_name = params["attacker"].strip()
        target_name = params["target"].strip()
        soph = (params.get("sophistication") or "M").upper()
        is_counter = bool(params.get("counter", False))

        atk = self.db.get("Players", attacker_name) or self.db.get("Enemies", attacker_name)
        dfn = self.db.get("Players", target_name) or self.db.get("Enemies", target_name)
        if not atk or not dfn:
            return {"ok": False, "error": "Attacker or target not found."}

        atk_type = "Players" if not isinstance(atk, Enemy) else "Enemies"
        dfn_type = "Players" if not isinstance(dfn, Enemy) else "Enemies"
        atk_key = self._key_match(atk_type, attacker_name)
        dfn_key = self._key_match(dfn_type, target_name)

        # --- Inputs common to both paths ---
        physical = Prompt("Physical component? (y/n)", bool, default=False).ask()
        mana_spent = Prompt("Mana spent (optional)", float, default=0.0, optional=True).ask() or 0.0

        # Conductivity prompt: only stats; ask lane if 3-tuple and mana > 0
        cond_scalar, cond_lanes = conductivity_of(atk)
        cond_used = 0.0
        if mana_spent > 0:
            if cond_lanes is not None:
                lane = Prompt("Conductivity lane for mana (L/M/H)", str, default="M").ask().strip().upper()
                idx = {"L": 0, "M": 1, "H": 2}.get(lane, 1)
                cond_used = cond_lanes[idx]
            elif cond_scalar is not None:
                cond_used = cond_scalar
            else:
                cond_used = float(Prompt("Conductivity (scalar)", float, default=1.0).ask() or 1.0)

        # Sophistication
        atkm_extra = 0.0
        extra_phy = 0.0
        extra_reach = 0.0
        add_scalings: List[float] = [1.0]

        if soph in ("M", "H"):
            atkm_extra = float(Prompt("Attack accuracy modifier (additional)", float,
                                      default=0.0, optional=True).ask() or 0.0)
        if soph == "H":
            extra_phy = float(Prompt("Extra PHY (int, optional)", int, default=0, optional=True).ask() or 0)
        distance = float(Prompt("Distance (default 0)", float, default=0.0).ask() or 0.0)
        if soph == "H":
            extra_reach = float(Prompt("Extra reach (int, optional)", int, default=0, optional=True).ask() or 0)

        # Rolls
        acc_roll = Prompt("Accuracy roll (optional; blank = d20)", float, default=None, optional=True).ask()
        if acc_roll is None:
            acc_roll = rng.randint(1, 20)

        wants_counterattack = False
        com_roll = None
        if is_counter:
            wants_counterattack = bool(Prompt("Counterattack? (y/n)", bool, default=True).ask())
            com_roll = Prompt("Your COM roll for counter (optional; blank = d20)", float,
                              default=None, optional=True).ask()
            if com_roll is None:
                com_roll = rng.randint(1, 20)

        if soph in ("M", "H"):
            add_raw = Prompt("Additional scaling (float or comma-separated floats, optional)",
                             str, default="", optional=True).ask()
            if add_raw:
                add_scalings = parse_scalings(add_raw)

        def bundle(attacker, defender, roll_for_acc: float, dist: float) -> HitBundle:
            acc = acc_value(attacker, roll_for_acc, atkm_extra, dist, extra_reach)
            eva = eva_value(attacker, defender)
            if acc <= eva:
                eff_phy = effective_phy(attacker, extra_phy, physical)
                eff_opt = effective_opt(mana_spent, cond_used)
                return HitBundle(False, acc, eva, 0.0, 0.0, 0, env_damage_raw(eff_phy, eff_opt))

            sc = scaling(acc, eva)
            acc14 = acc_value(attacker, 14.0, atkm_extra, dist, extra_reach)
            sc14 = scaling(acc14, eva)

            eff_phy = effective_phy(attacker, extra_phy, physical)
            eff_opt = effective_opt(mana_spent, cond_used)
            base = 2.5 * eff_phy + 2.0 * eff_opt

            mult = sc
            for m in add_scalings:
                mult *= float(m)

            dmg = max(0, int(round(base * mult)))
            return HitBundle(True, acc, eva, sc, sc14, dmg, env_damage_raw(eff_phy, eff_opt))

        msgs: List[str] = []
        deal_damage = bool(Prompt("Deal damage? (y/n)", bool, default=False).ask())

        # -------------------------
        # Standard attack
        # -------------------------
        if not is_counter:
            b = bundle(atk, dfn, acc_roll, distance)
            if b.hit:
                msgs.append(f"{getattr(atk,'name',attacker_name)} hit {getattr(dfn,'name',target_name)} and deals {b.dmg} damage (ACC roll: {acc_roll})")
                msgs.append(f"damage potential: ({b.sc:.3f} / {b.sc14:.3f})")
            else:
                msgs.append(f"{getattr(atk,'name',attacker_name)} missed {getattr(dfn,'name',target_name)} (ACC roll: {acc_roll})")
                msgs.append(f"miss index: {(b.acc - b.eva):.3f}")
            msgs.append(f"environmental damage (raw): {b.env:.2f}")

            if deal_damage and b.hit and b.dmg > 0:
                if hasattr(dfn, "apply_damage"):
                    dfn.apply_damage(b.dmg)
                else:
                    cur = getattr(dfn, "hp_current", None)
                    if isinstance(cur, (int, float)):
                        setattr(dfn, "hp_current", max(0, cur - b.dmg))
                self.db.mark_dirty(dfn_type, dfn_key)
                rem = getattr(dfn, "hp_current", None)
                if isinstance(rem, (int, float)) and rem <= 0:
                    msgs.append(f"{getattr(dfn,'name',target_name)} should be dead")

            return {"ok": True, "message": "\n".join(msgs)}

        # -------------------------
        # Counter
        # -------------------------
        enemy_acc = acc_value(atk, acc_roll, atkm_extra, distance, extra_reach)
        counter_check = n(com_roll, 0.0) + commm(dfn) + (5.0 if not wants_counterattack else 0.0)
        success = counter_check > enemy_acc

        if success:
            if wants_counterattack:
                # Counterattack uses nat 20 at point blank
                b = bundle(dfn, atk, 20.0, 0.0)
                msgs.append(
                    f"{getattr(dfn,'name',target_name)} countered {getattr(atk,'name',attacker_name)}'s attack and deals {b.dmg} damage "
                    f"(ACC roll: {acc_roll}, COM roll: {com_roll})"
                )
                msgs.append(f"environmental damage (raw): {b.env:.2f}")

                if deal_damage and b.dmg > 0:
                    if hasattr(atk, "apply_damage"):
                        atk.apply_damage(b.dmg)
                    else:
                        cur = getattr(atk, "hp_current", None)
                        if isinstance(cur, (int, float)):
                            setattr(atk, "hp_current", max(0, cur - b.dmg))
                    self.db.mark_dirty(atk_type, atk_key)
                    rem = getattr(atk, "hp_current", None)
                    if isinstance(rem, (int, float)) and rem <= 0:
                        msgs.append(f"{getattr(atk,'name',attacker_name)} should be dead")
            else:
                msgs.append(f"{getattr(dfn,'name',target_name)} countered {getattr(atk,'name',attacker_name)} successfully")
            return {"ok": True, "message": "\n".join(msgs)}

        # Counter failed: EVA for damage scaling is min(FINM + ΔLevel, 0)
        fail_eva = min(finm(dfn) + (level(dfn) - level(atk)), 0)
        sc = (max(enemy_acc - fail_eva, 0.0) + C_CONST) / 20.0

        eff_phy = effective_phy(atk, extra_phy, physical)
        eff_opt = effective_opt(mana_spent, cond_used)
        base = 2.5 * eff_phy + 2.0 * eff_opt

        mult = sc
        for m in add_scalings:
            mult *= float(m)

        dmg = max(0, int(round(base * mult)))
        msgs.append(
            f"{getattr(dfn,'name',target_name)} failed to counter {getattr(atk,'name',attacker_name)}'s attack and takes {dmg} damage "
            f"(ACC roll: {acc_roll}, COM roll: {com_roll})"
        )
        msgs.append(f"fail index: {(enemy_acc - counter_check):.3f}")
        msgs.append(f"environmental damage (raw): {env_damage_raw(eff_phy, eff_opt):.2f}")

        if deal_damage and dmg > 0:
            if hasattr(dfn, "apply_damage"):
                dfn.apply_damage(dmg)
            else:
                cur = getattr(dfn, "hp_current", None)
                if isinstance(cur, (int, float)):
                    setattr(dfn, "hp_current", max(0, cur - dmg))
            self.db.mark_dirty(dfn_type, dfn_key)
            rem = getattr(dfn, "hp_current", None)
            if isinstance(rem, (int, float)) and rem <= 0:
                msgs.append(f"{getattr(dfn,'name',target_name)} should be dead")

        return {"ok": True, "message": "\n".join(msgs)}
