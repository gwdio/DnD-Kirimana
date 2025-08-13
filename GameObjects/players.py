import math
from typing import Optional, List, Union, Dict, Any
from Types.stats import BaseStats, to_modifier
from Types.game_object import BaseGameObject
from Services.database import DatabaseManager
from .weapons import Weapon
from .accessories import Accessory
from .outfits import Outfit

class Player(BaseGameObject):
    def __init__(
        self,
        name: str,
        level: int,
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
        self.level = level

        # Create base stats and compute derived
        self.stats = BaseStats(
            PHY=PHY,
            FIN=FIN,
            COM=COM,
            MGK=MGK,
            CAP=CAP,
            OPT=OPT,
            RR=RR,
            Other=Other
        )
        self._calculate_derived_stats()

        # Equipment slots
        self.weapon: Optional[Weapon] = None
        self.outfit: Optional[Outfit] = None
        self.accessories: List[Optional[Accessory]] = [None] * 4

    def _calculate_derived_stats(self):
        """Compute and set derived stats from base stats and level."""
        phy = self.stats.PHY or 0
        cap = self.stats.CAP or 0
        opt = self.stats.OPT or 0
        rr = self.stats.RR or 0
        lv = self.level

        # Derived stat formulas
        self.stats.MMAX = round(math.sqrt(cap * lv) * 10)
        self.stats.CHN = round(math.sqrt(opt * lv) * 5)
        self.stats.REG = round(math.sqrt(rr * lv) * 3)
        self.stats.HP = (to_modifier(phy) + 10) * 10 + self.stats.MMAX / 2

        # Initialize current resources
        self.stats.hp_current = int(self.stats.HP)
        self.stats.mana_current = int(self.stats.MMAX)

    def equip_weapon(self, weapon: Weapon):
        self.weapon = weapon
        self.stats.apply_modifier(**weapon.stats.to_json())

    def equip_outfit(self, outfit: Outfit):
        self.outfit = outfit
        self.stats.apply_modifier(**outfit.stats.to_json())

    def equip_accessory(self, accessory: Accessory, slot_index: int):
        if not (0 <= slot_index < 4):
            raise ValueError("Accessory slot index must be between 0 and 3.")
        self.accessories[slot_index] = accessory
        self.stats.apply_modifier(**accessory.stats.to_json())

    def unequip_weapon(self) -> None:
        if self.weapon:
            # remove its bonuses
            self.stats.remove_modifier(**self.weapon.stats.to_json())
            self.weapon = None

    def unequip_outfit(self) -> None:
        if self.outfit:
            self.stats.remove_modifier(**self.outfit.stats.to_json())
            self.outfit = None

    def unequip_accessory(self, slot_index: int) -> None:
        if not (0 <= slot_index < 4):
            raise ValueError("Accessory slot index must be between 0 and 3.")
        acc = self.accessories[slot_index]
        if acc:
            self.stats.remove_modifier(**acc.stats.to_json())
            self.accessories[slot_index] = None

    def apply_effect(self, **modifiers):
        """Apply arbitrary changes to the player's stats (buffs/debuffs)."""
        self.stats.apply_modifier(**modifiers)

    def refresh(self):
        """
        Recalculate derived stats from base stats, then reapply all equipment bonuses.
        """
        # Recalculate derived stats from base (no equips)
        self._calculate_derived_stats()

        # Reapply equipment modifiers
        if self.weapon:
            self.stats.apply_modifier(**self.weapon.stats.to_json())

        if self.outfit:
            self.stats.apply_modifier(**self.outfit.stats.to_json())

        for acc in self.accessories:
            if acc:
                self.stats.apply_modifier(**acc.stats.to_json())


    def pretty_rep_short(self) -> str:
        acc_names = [acc.name if acc else "None" for acc in self.accessories]
        return (
            f"{self.name} (LV {self.level}) | HP {self.stats.HP} | PHY {self.stats.PHY} | "
            f"MMAX {self.stats.MMAX} | CHN {self.stats.CHN} | REG {self.stats.REG}\n"
            f"Equips: Weapon [{self.weapon.name if self.weapon else 'None'}], "
            f"Outfit [{self.outfit.name if self.outfit else 'None'}], "
            f"Accessories [{', '.join(acc_names)}]"
        )

    def pretty_rep_long(self) -> str:
        acc_strs = [
            acc.pretty_rep_short() if acc else "None"
            for acc in self.accessories
        ]
        return (
                f"{self.name} — Level {self.level}\n"
                f"HP: {self.stats.hp_current}/{self.stats.HP} | PHY: {self.stats.PHY} | FIN: {self.stats.FIN} | COM: {self.stats.COM} | MGK: {self.stats.MGK}\n"
                f"CAP: {self.stats.CAP} | OPT: {self.stats.OPT} | RR: {self.stats.RR}\n"
                f"MMAX: {self.stats.MMAX} | CHN: {self.stats.CHN} | REG: {self.stats.REG}\n"
                f"Weapon:\n  {self.weapon.pretty_rep_short() if self.weapon else 'None'}\n"
                f"Outfit:\n  {self.outfit.pretty_rep_short() if self.outfit else 'None'}\n"
                f"Accessories:\n  " + "\n  ".join(acc_strs)
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "stats": self.stats.to_json(),
            "weapon": self.weapon.name if self.weapon else None,
            "outfit": self.outfit.name if self.outfit else None,
            "accessories": [acc.name if acc else None for acc in self.accessories]
        }

    @classmethod
    def from_json(cls, data: dict, db: "DatabaseManager" = None) -> "Player":
        """
        Reconstruct a Player from JSON data.
        If db is provided, equipped items are also loaded.
        """
        # Create player with base stats from saved JSON
        stats_obj = BaseStats.from_json(data.get("stats", {}))
        player = cls(
            name=data["name"],
            level=data["level"],
            PHY=stats_obj.PHY,
            FIN=stats_obj.FIN,
            COM=stats_obj.COM,
            MGK=stats_obj.MGK,
            CAP=stats_obj.CAP,
            OPT=stats_obj.OPT,
            RR=stats_obj.RR,
            Other=stats_obj.Other
        )
        player.stats = stats_obj  # Keep exact stored stats

        # Load equipment if db is provided
        if db:
            # Weapon
            weapon_name = data.get("weapon")
            if weapon_name:
                weapon_obj = db.load_object("Weapons", weapon_name)
                if weapon_obj:
                    player.weapon = weapon_obj

            # Outfit
            outfit_name = data.get("outfit")
            if outfit_name:
                outfit_obj = db.load_object("Outfits", outfit_name)
                if outfit_obj:
                    player.outfit = outfit_obj

            # Accessories
            accessories_list = data.get("accessories", [])
            for i, acc_name in enumerate(accessories_list):
                if acc_name:
                    acc_obj = db.load_object("Accessories", acc_name)
                    if acc_obj:
                        player.accessories[i] = acc_obj

        return player
