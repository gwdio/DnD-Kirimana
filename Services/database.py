import json
from pathlib import Path
from typing import Any, Optional, Type, TypeVar, List

T = TypeVar("T")

class DatabaseManager:
    def __init__(self, base_dir: str = "Data"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _folder_path(self, obj_type: str) -> Path:
        """Return the folder path for the given type."""
        path = self.base_path / obj_type
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save(self, obj: Any, obj_type: str, name: str) -> None:
        """
        Save an object as JSON.
        - obj: must have a to_json() method or be JSON-serializable
        - obj_type: e.g., 'Players', 'Weapons', 'Accessories'
        - name: filename without extension
        """
        folder = self._folder_path(obj_type)
        file_path = folder / f"{name}.json"
        data = obj.to_json() if hasattr(obj, "to_json") else obj
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {obj_type}/{name}.json")

    def load(self, obj_type: str, name: str, cls: Optional[Type[T]] = None) -> Optional[T]:
        """
        Load a JSON file and optionally return a class instance.
        - obj_type: e.g., 'Players', 'Weapons'
        - name: filename without extension
        - cls: if provided, must have a from_json(data: dict) -> instance method
        """
        folder = self._folder_path(obj_type)
        file_path = folder / f"{name}.json"
        if not file_path.exists():
            print(f"No such file: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if cls:
            if hasattr(cls, "from_json") and callable(getattr(cls, "from_json")):
                return cls.from_json(data)
            else:
                raise TypeError(f"{cls.__name__} must have a from_json() method to load from the database.")
        return data

    def load_object(self, obj_type: str, name: str):
        from GameObjects.accessories import Accessory
        from GameObjects.enemies import Enemy
        from GameObjects.outfits import Outfit
        from GameObjects.players import Player
        from GameObjects.weapons import Weapon

        cls_map = {
            "Players": Player,
            "Enemies": Enemy,
            "Weapons": Weapon,
            "Accessories": Accessory,
            "Outfits": Outfit,
        }
        cls = cls_map.get(obj_type)
        return self.load(obj_type, name, cls=cls) if cls else None

    def delete(self, obj_type: str, name: str) -> bool:
        """Delete the JSON file for a given object type and name."""
        file_path = self._folder_path(obj_type) / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            print(f"Deleted {obj_type}/{name}.json")
            return True
        print(f"No such file: {file_path}")
        return False

    def list_types(self) -> List[str]:
        """List all top-level types (subfolders) in the data directory."""
        return [p.name for p in self.base_path.iterdir() if p.is_dir()]

    def list_names(self, obj_type: str) -> List[str]:
        """List all objects of a type using their short representation if possible."""
        folder = self._folder_path(obj_type)
        results = []
        for file_path in folder.glob("*.json"):
            name = file_path.stem
            cls = self._resolve_class_for_type(obj_type)
            if cls:
                try:
                    data = self.load(obj_type, name)
                    obj = cls.from_json(data, db=self) if "db" in cls.from_json.__code__.co_varnames else cls.from_json(
                        data)
                    if hasattr(obj, "pretty_rep_short"):
                        results.append(obj.pretty_rep_short())
                        continue
                except Exception:
                    pass
            results.append(name)
        return results

    def show(self, obj_type: str, name: str) -> str:
        """
        Show detailed object info.
        Uses pretty_rep_long() if available, otherwise falls back to JSON.
        """
        cls = self._resolve_class_for_type(obj_type)
        data = self.load(obj_type, name)
        if not data:
            return f"No such {obj_type} named '{name}'."
        if cls:
            try:
                obj = cls.from_json(data, db=self) if "db" in cls.from_json.__code__.co_varnames else cls.from_json(
                    data)
                if hasattr(obj, "pretty_rep_long"):
                    return obj.pretty_rep_long()
            except Exception as e:
                return f"Error loading {obj_type}/{name}: {e}"
        return json.dumps(data, indent=2)

    def _resolve_class_for_type(self, obj_type: str):
        """Map folder names to their class types."""
        from GameObjects.players import Player
        from GameObjects.enemies import Enemy
        from GameObjects.weapons import Weapon
        from GameObjects.accessories import Accessory
        from GameObjects.outfits import Outfit
        mapping = {
            "Players": Player,
            "Enemies": Enemy,
            "Weapons": Weapon,
            "Accessories": Accessory,
            "Outfits": Outfit
        }
        return mapping.get(obj_type)

    def list_items(self, obj_type: str) -> List[str]:
        """
        List all object names for the given type, using actual stored file names.
        This is used internally so that operations like load/delete work reliably.
        """
        folder = self._folder_path(obj_type)
        return [p.stem for p in folder.glob("*.json")]

