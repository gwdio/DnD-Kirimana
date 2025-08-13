from math import floor
from typing import Optional, Union, List, Tuple


def to_modifier(stat: int) -> int:
    return floor((stat - 10) / 2)

class BaseStats:
    def __init__(
        self,
        # Core base stats
        PHY: Optional[int] = None,
        FIN: Optional[int] = None,
        COM: Optional[int] = None,
        MGK: Optional[int] = None,

        # Magic substats
        CAP: Optional[int] = None,
        OPT: Optional[int] = None,
        RR: Optional[int] = None,

        # Derived/computed stats
        HP: Optional[int] = None,
        MMAX: Optional[int] = None,
        CHN: Optional[int] = None,
        REG: Optional[int] = None,
        ACC: Optional[int] = None,
        EVA: Optional[int] = None,

        # Weapon stats
        PHY_mod: Optional[int] = None,
        ACC_mod: Optional[int] = None,
        reach: Optional[int] = None,
        weight: Optional[str] = None,
        conductivity: Optional[Union[float, Tuple[float, float, float]]] = None,
        control: Optional[int] = None,
        damage_type: Optional[Union[str, List[str]]] = None,
        ATKM: Optional[int] = None,

        # Resource tracking
        hp_current: Optional[int] = None,
        mana_current: Optional[int] = None,

        # Specialty stats
        Other: Optional[Union[str, List[str]]] = None
    ):
        # Store all directly on self
        for k, v in locals().items():
            if k != "self":
                setattr(self, k, v)

    def apply_modifier(self, **kwargs):
        """Apply stat changes (additive) to existing values."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                curr = getattr(self, k)
                if curr is None:
                    setattr(self, k, v)
                elif isinstance(curr, (int, float)) and isinstance(v, (int, float)):
                    setattr(self, k, curr + v)
                elif isinstance(curr, list) and isinstance(v, list):
                    setattr(self, k, curr + v)
                else:
                    setattr(self, k, v)  # overwrite if incompatible type

    def remove_modifier(self, **kwargs):
        """Apply stat changes (additive) to existing values."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                curr = getattr(self, k)
                if isinstance(curr, (int, float)) and isinstance(v, (int, float)):
                    setattr(self, k, curr - v)
                elif isinstance(curr, list) and isinstance(v, list):
                    setattr(self, k, curr.remove(v))
                else:
                    setattr(self, k, None)  # overwrite if incompatible type

    def to_json(self):
        return {k: getattr(self, k) for k in self.__dict__}

    @classmethod
    def from_json(cls, data: dict) -> "BaseStats":
        """Create a BaseStats object from JSON/dict data."""
        return cls(**data)

    def __repr__(self):
        return f"BaseStats({self.to_json()})"

