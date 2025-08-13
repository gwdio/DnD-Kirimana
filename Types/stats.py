from math import floor
from typing import Optional, Union, List, Tuple, Any, Iterable
from numbers import Number


def to_modifier(stat: int) -> int:
    return floor((stat - 10) / 2)


def _is_tuple3(x: Any) -> bool:
    return isinstance(x, tuple) and len(x) == 3 and all(isinstance(t, Number) for t in x)

def _to_tuple3(x: Any) -> tuple[Number, Number, Number]:
    # Broadcast scalars; pass through valid 3-tuples
    if _is_tuple3(x):
        return x  # type: ignore[return-value]
    if isinstance(x, Number):
        return (x, x, x)
    raise TypeError("Cannot convert to 3-tuple")

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
            if not hasattr(self, k):
                continue

            curr = getattr(self, k)

            # Ignore no-op inputs
            if v is None:
                continue

            # Tuple logic: if either side is a 3-tuple, do element-wise with broadcast
            if _is_tuple3(curr) or _is_tuple3(v):
                if curr is None:
                    setattr(self, k, _to_tuple3(v))
                else:
                    a = _to_tuple3(curr if curr is not None else 0)
                    b = _to_tuple3(v)
                    setattr(self, k, (a[0]+b[0], a[1]+b[1], a[2]+b[2]))
                continue

            # Plain numbers
            if isinstance(curr, Number) and isinstance(v, Number):
                setattr(self, k, curr + v)
                continue

            # Lists: concatenate
            if isinstance(curr, list) and isinstance(v, list):
                setattr(self, k, curr + v)
                continue

            # If current is None, adopt value
            if curr is None:
                setattr(self, k, v)
                continue

            # Fallback: overwrite if incompatible but not None
            setattr(self, k, v)

    def remove_modifier(self, **kwargs):
        """Remove previously applied stat changes (subtractive)."""
        for k, v in kwargs.items():
            if not hasattr(self, k):
                continue

            curr = getattr(self, k)

            # Ignore no-op inputs
            if v is None:
                continue

            # Tuple logic: if either side is a 3-tuple, do element-wise with broadcast.
            # After subtraction, collapse (a,a,a) -> a
            if _is_tuple3(curr) or _is_tuple3(v):
                if curr is None:
                    # Nothing to subtract from
                    continue
                a = _to_tuple3(curr if curr is not None else 0)
                b = _to_tuple3(v)
                res = (a[0]-b[0], a[1]-b[1], a[2]-b[2])
                if res[0] == res[1] == res[2]:
                    setattr(self, k, res[0])
                else:
                    setattr(self, k, res)
                continue

            # Plain numbers
            if isinstance(curr, Number) and isinstance(v, Number):
                setattr(self, k, curr - v)
                continue

            # Lists: remove one occurrence of each item in v from curr
            if isinstance(curr, list) and isinstance(v, list):
                new_list = list(curr)
                for item in v:
                    try:
                        new_list.remove(item)
                    except ValueError:
                        pass
                setattr(self, k, new_list)
                continue

            # Fallback for incompatible types: clear
            setattr(self, k, None)

    def to_json(self):
        return {k: getattr(self, k) for k in self.__dict__}

    @classmethod
    def from_json(cls, data: dict) -> "BaseStats":
        """Create a BaseStats object from JSON/dict data."""
        return cls(**data)

    def __repr__(self):
        return f"BaseStats({self.to_json()})"

