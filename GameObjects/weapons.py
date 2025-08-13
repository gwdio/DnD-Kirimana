from typing import Optional, Union, List, Tuple, Dict, Any
from Types.stats import BaseStats
from Types.game_object import BaseGameObject

class Weapon(BaseGameObject):
    def __init__(
        self,
        name: str,
        weapon_type: str,
        rarity: Optional[str] = None,
        PHY_mod: Optional[int] = None,
        ACC_mod: Optional[int] = None,
        reach: Optional[int] = None,
        weight: Optional[str] = None,
        conductivity: Optional[Union[float, Tuple[float, float, float]]] = None,
        control: Optional[int] = None,
        damage_type: Optional[Union[str, List[str]]] = None,
        ATKM: Optional[int] = None,
        # Optional extra stats (for rare weapons with bonuses)
        PHY: Optional[int] = None,
        FIN: Optional[int] = None,
        COM: Optional[int] = None,
        MGK: Optional[int] = None,
        CAP: Optional[int] = None,
        OPT: Optional[int] = None,
        RR: Optional[int] = None,
        Other: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(name)
        self.weapon_type = weapon_type
        self.rarity = rarity

        # All stats, both weapon-specific and general, are stored in BaseStats
        self.stats = BaseStats(
            PHY_mod=PHY_mod,
            ACC_mod=ACC_mod,
            reach=reach,
            weight=weight,
            conductivity=conductivity,
            control=control,
            damage_type=damage_type,
            ATKM=ATKM,
            PHY=PHY,
            FIN=FIN,
            COM=COM,
            MGK=MGK,
            CAP=CAP,
            OPT=OPT,
            RR=RR,
            Other=Other
        )


    def pretty_rep_short(self) -> str:
        return f"{self.name} [{self.weapon_type}] (Rarity: {self.rarity or 'Common'})"

    def pretty_rep_long(self) -> str:
        lines = [
            f"{self.name} — {self.weapon_type} (Rarity: {self.rarity or 'Common'})",
            f"Mods:",
            f"  PHY_mod: {self.stats.PHY_mod}  ACC_mod: {self.stats.ACC_mod}  Reach: {self.stats.reach}m",
            f"  Weight: {self.stats.weight or 'Unknown'}  Conductivity: {self.stats.conductivity or 'N/A'}",
            f"  Control: {self.stats.control}  Damage Type: {self.stats.damage_type or 'N/A'}",
            f"  ATKM: {self.stats.ATKM}"
        ]
        # Stat bonuses
        bonuses = {k: v for k, v in self.stats.to_json().items() if v not in (0, None)}
        if bonuses:
            lines.append("Stat Bonuses:")
            for k, v in bonuses.items():
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "weapon_type": self.weapon_type,
            "rarity": self.rarity,
            "stats": self.stats.to_json()
        }

    @classmethod
    def from_json(cls, data: dict, db=None) -> "Weapon":
        stats_obj = BaseStats.from_json(data.get("stats", {}))
        w = cls(
            name=data["name"],
            weapon_type=data["weapon_type"],
            rarity=data.get("rarity"),
        )
        # Preserve everything exactly as saved (includes PHY_mod, ACC_mod, reach, weight, conductivity, control, damage_type, ATKM, etc.)
        w.stats = stats_obj
        return w