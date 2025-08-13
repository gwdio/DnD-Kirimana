import atexit
import json
from pathlib import Path
from typing import Any, Dict, Optional


def _resolve_class_for_type(obj_type: str):
    # late import to avoid circulars
    from GameObjects.players import Player
    from GameObjects.enemies import Enemy
    from GameObjects.weapons import Weapon
    from GameObjects.accessories import Accessory
    from GameObjects.outfits import Outfit
    return {
        "Players": Player, "Enemies": Enemy, "Weapons": Weapon,
        "Accessories": Accessory, "Outfits": Outfit
    }.get(obj_type)


def _key(s: str) -> str:
    return s.strip().lower()


class DatabaseManager:
    def __init__(self, base_dir: str = "Data"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # identity map: { obj_type: { name: obj_instance } }
        self._cache: Dict[str, Dict[str, Any]] = {}
        # dirty set: {(obj_type, name)}
        self._dirty: set[tuple[str, str]] = set()

        # Optional: auto-commit on interpreter exit
        atexit.register(self.commit)

    # ---------- identity helpers ----------
    def _folder_path(self, obj_type: str) -> Path:
        p = self.base_path / obj_type
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---------- public API ----------
    def get(self, obj_type: str, name: str):
        """Return the singleton object for this (type, name), loading if needed."""
        name = _key(name)
        bucket = self._cache.setdefault(obj_type, {})
        if name in bucket:
            return bucket[name]

        # load from disk
        cls = _resolve_class_for_type(obj_type)
        file_path = self._folder_path(obj_type) / f"{name}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        obj = cls.from_json(data, db=self) if cls else data  # always pass db
        bucket[name] = obj
        return obj

    def add_or_replace(self, obj_type: str, name: str, obj: Any):
        """Insert into identity map and mark dirty."""
        name = _key(name)
        self._cache.setdefault(obj_type, {})[name] = obj
        self._dirty.add((obj_type, name))

    def mark_dirty(self, obj_type: str, name: str):
        name = _key(name)
        self._dirty.add((obj_type, name))

    def delete(self, obj_type: str, name: str) -> bool:
        name = _key(name)
        self._cache.setdefault(obj_type, {}).pop(name, None)
        self._dirty.discard((obj_type, name))  # no need to save it
        file_path = self._folder_path(obj_type) / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
            print(f"Deleted {obj_type}/{name}.json")
            return True
        print(f"No such file: {file_path}")
        return False

    def list_items(self, obj_type: str) -> list[str]:
        # list keys on disk (source of truth for available objects)
        folder = self._folder_path(obj_type)
        return [p.stem for p in folder.glob("*.json")]

    def list_names(self, obj_type: str) -> list[str]:
        # pretty short reps for UI
        out = []
        for key in self.list_items(obj_type):
            obj = self.get(obj_type, key)
            out.append(obj.pretty_rep_short() if hasattr(obj, "pretty_rep_short") else key)
        return out

    def list_types(self) -> list[str]:
        """List all top-level types (subfolders) in the data directory."""
        return [p.name for p in self.base_path.iterdir() if p.is_dir()]

    def show(self, obj_type: str, name: str) -> str:
        name = _key(name)
        obj = self.get(obj_type, name)
        if obj is None:
            return f"No such {obj_type} named '{name}'."
        if hasattr(obj, "pretty_rep_long"):
            return obj.pretty_rep_long()
        import pprint
        return pprint.pformat(getattr(obj, "from_json", lambda: {} )(), indent=2)


    # ---------- commit / flush ----------
    def commit(self):
        """Write all dirty objects back to disk (atomic-ish, exception-safe)."""
        if not self._dirty:
            return

        import os, tempfile

        to_commit = list(self._dirty)  # snapshot
        success = 0

        for obj_type, name in to_commit:
            obj = self._cache.get(obj_type, {}).get(name)
            if obj is None:
                # nothing to write; clear this one
                print(f"[commit] WARNING: dirty entry {obj_type}/{name} not in cache")
                self._dirty.discard((obj_type, name))
                continue

            folder = self._folder_path(obj_type)
            final_path = folder / f"{name}.json"

            data = obj.to_json() if hasattr(obj, "to_json") else obj

            # atomic write: to temp file then replace
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=folder, delete=False) as tmp:
                json.dump(data, tmp, indent=2, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_name = tmp.name

            os.replace(tmp_name, final_path)  # atomic on POSIX/NTFS
            self._dirty.discard((obj_type, name))
            success += 1

        print(f"Committed {success} object(s).")

    def reload(self, obj_type: str, name: str, *, if_missing="keep"):
        """
        Reload an item from disk.
        if_missing: "keep" (default) -> leave cached object as-is and return it
                    "none"            -> return None, keep cache intact
                    "raise"           -> raise FileNotFoundError
        Returns the (re)loaded object or None.
        """
        # optional: canonicalize key if you use case-insensitive names
        # name = self._key(name)

        file_path = self._folder_path(obj_type) / f"{name}.json"
        if not file_path.exists():
            if if_missing == "raise":
                raise FileNotFoundError(f"{obj_type}/{name}.json not found")
            if if_missing == "none":
                return None
            # "keep": don't evict; return whatever is in cache (or None)
            return self._cache.get(obj_type, {}).get(name)

        # File exists: evict and repopulate from disk
        self._cache.setdefault(obj_type, {}).pop(name, None)
        obj = self.get(obj_type, name)

        # Reload means "discard unsaved changes"; clear any dirty flag for this key
        self._dirty.discard((obj_type, name))

        return obj

