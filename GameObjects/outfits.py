from typing import Optional, Union, List, Tuple, Dict, Any
from Types.stats import BaseStats
from Types.game_object import BaseGameObject

class Outfit(BaseGameObject):
    def __init__(
        self,
        name: str,
        outfit_type: str,  # e.g., "armor", "robe", "clothing"
        rarity: Optional[str] = None,
        # Any stat this outfit modifies
        PHY: Optional[int] = None,
        FIN: Optional[int] = None,
        COM: Optional[int] = None,
        MGK: Optional[int] = None,
        CAP: Optional[int] = None,
        OPT: Optional[int] = None,
        RR: Optional[int] = None,
        HP: Optional[int] = None,
        MMAX: Optional[int] = None,
        CHN: Optional[int] = None,
        REG: Optional[int] = None,
        ACC: Optional[int] = None,
        EVA: Optional[int] = None,
        PHY_mod: Optional[int] = None,
        ACC_mod: Optional[int] = None,
        reach: Optional[int] = None,
        weight: Optional[str] = None,
        conductivity: Optional[Union[float, Tuple[float, float, float]]] = None,
        control: Optional[int] = None,
        damage_type: Optional[Union[str, List[str]]] = None,
        ATKM: Optional[int] = None,
        hp_current: Optional[int] = None,
        mana_current: Optional[int] = None,
        Other: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(name)
        self.outfit_type = outfit_type
        self.rarity = rarity

        self.stats = BaseStats(
            PHY=PHY, FIN=FIN, COM=COM, MGK=MGK,
            CAP=CAP, OPT=OPT, RR=RR,
            HP=HP, MMAX=MMAX, CHN=CHN, REG=REG,
            ACC=ACC, EVA=EVA,
            PHY_mod=PHY_mod, ACC_mod=ACC_mod, reach=reach,
            weight=weight, conductivity=conductivity, control=control,
            damage_type=damage_type, ATKM=ATKM,
            hp_current=hp_current, mana_current=mana_current,
            Other=Other
        )


    def pretty_rep_short(self) -> str:
        bonuses = {k: v for k, v in self.stats.to_json().items() if v not in (0, None)}
        bonus_str = ", ".join(f"{k} +{v}" for k, v in bonuses.items()) if bonuses else "No modifiers"
        return f"{self.name} [{self.outfit_type}] (Rarity: {self.rarity or 'Common'}) — {bonus_str}"

    def pretty_rep_long(self) -> str:
        lines = [f"{self.name} — {self.outfit_type} (Rarity: {self.rarity or 'Common'})"]
        bonuses = {k: v for k, v in self.stats.to_json().items() if v not in (0, None)}
        if bonuses:
            lines.append("Modifiers:")
            for k, v in bonuses.items():
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "outfit_type": self.outfit_type,
            "rarity": self.rarity,
            "stats": self.stats.to_json()
        }

    @classmethod
    def from_json(cls, data: dict) -> "Outfit":
        stats_obj = BaseStats.from_json(data.get("stats", {}))
        return cls(
            name=data["name"],
            outfit_type=data.get("outfit_type"),
            rarity=data.get("rarity"),
            PHY=stats_obj.PHY,
            FIN=stats_obj.FIN,
            COM=stats_obj.COM,
            MGK=stats_obj.MGK,
            CAP=stats_obj.CAP,
            OPT=stats_obj.OPT,
            RR=stats_obj.RR,
            HP=stats_obj.HP,
            MMAX=stats_obj.MMAX,
            CHN=stats_obj.CHN,
            REG=stats_obj.REG,
            ACC=stats_obj.ACC,
            EVA=stats_obj.EVA,
            Other=stats_obj.Other
        )
