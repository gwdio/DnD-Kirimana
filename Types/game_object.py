from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="BaseGameObject")

class BaseGameObject:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        """Default repr uses pretty_rep_short if defined."""
        if hasattr(self, "pretty_rep_short") and callable(self.pretty_rep_short):
            return self.pretty_rep_short()
        return f"<{self.__class__.__name__} name={self.name}>"

    def pretty_rep_short(self) -> str:
        """Override in subclass."""
        return self.name

    def pretty_rep_long(self) -> str:
        """Override in subclass."""
        return self.name

    def to_json(self) -> Dict[str, Any]:
        """Override in subclass. Must return JSON-serializable dict."""
        raise NotImplementedError

    @classmethod
    def from_json(cls: Type[T], data: Dict[str, Any]) -> T:
        """Override in subclass."""
        raise NotImplementedError
