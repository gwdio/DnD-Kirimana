from typing import Optional, Union, List, Dict, Any
from .players import Player
from Types.stats import BaseStats
from Types.game_object import BaseGameObject
from Services.database import DatabaseManager
from .weapons import Weapon
from .accessories import Accessory
from .outfits import Outfit


class Enemy(Player):
    """
    Enemy is identical to Player in mechanics but has extra descriptive fields.
    """

    def __init__(
        self,
        name: str,
        level: int,
        species: str,
        faction: str,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        position: Optional[str] = None,
        note: Optional[str] = None,
        PHY: Optional[int] = None,
        FIN: Optional[int] = None,
        COM: Optional[int] = None,
        MGK: Optional[int] = None,
        CAP: Optional[int] = None,
        OPT: Optional[int] = None,
        RR: Optional[int] = None,
        Other: Optional[Union[str, List[str]]] = None
    ):
        # Store extra descriptors
        self.species = species
        self.faction = faction
        self.gender = gender
        self.age = age
        self.position = position
        self.note = note

        super().__init__(
            name=name,
            level=level,
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
        parts = [f"LV {self.level} {self.species} of {self.faction}"]
        if self.position:
            parts.append(f"{self.position} {self.name}")
        else:
            parts.append(self.name)
        if self.gender:
            parts.append(self.gender)
        if self.age is not None:
            parts.append(str(self.age))
        base_str = ", ".join(parts)
        if self.note:
            return f"{base_str}: {self.note}"
        return base_str

    def pretty_rep_long(self) -> str:
        return (
            f"{self.pretty_rep_short()}\n\n"
            f"Stats:\n"
            f"  PHY: {self.stats.PHY}  FIN: {self.stats.FIN}  COM: {self.stats.COM}  MGK: {self.stats.MGK}\n"
            f"  CAP: {self.stats.CAP}  OPT: {self.stats.OPT}  RR: {self.stats.RR}\n"
            f"  HP: {self.stats.HP}    MMAX: {self.stats.MMAX}  CHN: {self.stats.CHN}  REG: {self.stats.REG}"
        )

    def to_json(self) -> Dict[str, Any]:
        """Include descriptors + player data."""
        data = super().to_json()
        data.update({
            "species": self.species,
            "faction": self.faction,
            "gender": self.gender,
            "age": self.age,
            "position": self.position,
            "note": self.note
        })
        return data

    @classmethod
    def from_json(cls, data: dict, db: "DatabaseManager" = None) -> "Enemy":
        stats_obj = BaseStats.from_json(data.get("stats", {}))
        enemy = cls(
            name=data["name"],
            level=data["level"],
            species=data["species"],
            faction=data["faction"],
            gender=data.get("gender"),
            age=data.get("age"),
            position=data.get("position"),
            note=data.get("note"),
            PHY=stats_obj.PHY,
            FIN=stats_obj.FIN,
            COM=stats_obj.COM,
            MGK=stats_obj.MGK,
            CAP=stats_obj.CAP,
            OPT=stats_obj.OPT,
            RR=stats_obj.RR,
            Other=stats_obj.Other
        )
        enemy.stats = stats_obj

        if db:
            weapon_name = data.get("weapon")
            if weapon_name:
                weapon_obj = db.load_object("Weapons", weapon_name)
                if weapon_obj:
                    enemy.weapon = weapon_obj

            outfit_name = data.get("outfit")
            if outfit_name:
                outfit_obj = db.load_object("Outfits", outfit_name)
                if outfit_obj:
                    enemy.outfit = outfit_obj

            accessories_list = data.get("accessories", [])
            for i, acc_name in enumerate(accessories_list):
                if acc_name:
                    acc_obj = db.load_object("Accessories", acc_name)
                    if acc_obj:
                        enemy.accessories[i] = acc_obj

        return enemy
