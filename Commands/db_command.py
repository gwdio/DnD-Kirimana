import json
from typing import Dict, Any
from Types.prompts import Prompt, PromptGroup
from Types.results import Result
from Services.database import DatabaseManager

ROOT_ALIASES = {"root", "~", "home", "data"}
OBJECT_TYPES = ["Players", "Weapons", "Accessories", "Outfits", "Enemies"]

class DbCommand:
    name = "db"
    description = "Database management shell (list/ls, delete/rm, goto/cd, show)."

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.current_type = None  # None = root context

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "DB Command",
            [
                {
                    "name": "initial_action",
                    "question": "DB shell start (or leave empty to enter interactive mode)\n Commands: goto/cd, list/ls, delete/rm, show, rename",
                    "type": str,
                    "default": ""
                }
            ]
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        initial_action = params.get("initial_action", "").strip()
        if initial_action:
            # Run a single action then return
            self._process_action(initial_action)
            return {"ok": True}

        # Otherwise interactive shell
        while True:
            location = self.current_type or "~"
            action = input(f"db[{location}]> ").strip()
            if not action:
                continue
            if action.lower() in {"q", "quit", "exit"}:
                return {"ok": True, "message": "Exiting DB shell."}
            self._process_action(action)

    def _process_action(self, action: str):
        parts = action.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("ls", "list"):
            self._list_items(args)
        elif cmd in ("rm", "delete"):
            self._delete_item(args)
        elif cmd in ("cd", "goto"):
            self._goto_type(args)
        elif cmd == "show":
            self._show_item(args)
        elif cmd in ("save", "commit"):
            self._commit(args)
        elif cmd in ("reload", "revert"):
            self._reload(args)
        else:
            print(f"Unknown DB action '{cmd}'. Valid: list/ls, delete/rm, goto/cd, show")

    def _goto_type(self, args):
        if not args:
            print("⚠ Must provide a folder name.")
            return
        target = " ".join(args)
        resolved = self._resolve_type(target)
        if not resolved:
            print(f"⚠ Unknown folder '{target}'.")
            return
        self.current_type = resolved
        print(f"✔ Current DB type set to '{self.current_type}'.")

    def _list_items(self, args):
        if self.current_type is None:
            # Root context: list folders or the contents of a given folder
            if not args:
                folders = self.db.list_types()
                print("\n".join(folders) if folders else "(no folders)")
                return
            folder_name = " ".join(args)
            resolved = self._resolve_type(folder_name)
            if not resolved:
                print(f"⚠ Unknown folder '{folder_name}'.")
                return
            files = self.db.list_names(resolved)
            print("\n".join(files) if files else "(empty)")
            return

        # Folder context: list files
        files = self.db.list_names(self.current_type)
        print("\n".join(files) if files else "(empty)")

    def _delete_item(self, args):
        if not self.current_type:
            print("⚠ Must be inside a folder context to delete.")
            return
        name = " ".join(args) if args else Prompt("Enter name to delete", str).ask().strip()
        if not name:
            print("⚠ No name provided.")
            return
        self.db.delete(self.current_type, name)

    def _show_item(self, args):
        if self.current_type is None:
            # Root context show
            if not args:
                print("⚠ Must provide a folder name in root context.")
                return
            resolved = self._resolve_type(args[0])
            if not resolved:
                print(f"⚠ Unknown folder '{args[0]}'.")
                return
            files = self.db.list_names(resolved)
            print("\n".join(files) if files else "(empty)")
            return

        # Folder context show
        name = " ".join(args) if args else Prompt("Enter name to show", str).ask().strip()
        if not name:
            print("⚠ No name provided.")
            return
        data = self.db.show(self.current_type, name)
        if data is None:
            print(f"⚠ No such item '{name}'.")
            return
        print(f"=== {self.current_type}/{name} ===")
        if isinstance(data, str):
            print(data)
        else:
            print(json.dumps(data, indent=2))

    def _commit(self, args):
        self.db.commit()

    def _reload(self, args):
        if self.current_type is None:
            # Root context: require a folder and reload everything in it
            if not args:
                print("⚠ Must provide a folder name in root context.")
                return
            resolved = self._resolve_type(args[0])
            if not resolved:
                print(f"⚠ Unknown folder '{args[0]}'.")
                return
            files = self.db.list_items(resolved)
            for key in files:
                self.db.reload(resolved, key)
            print(f"Reloaded {', '.join(files) if files else '(none)'}")
            return

        # Folder context: reload one item (accept typed name with any case)
        name = " ".join(args) if args else Prompt("Enter name to reload", str).ask().strip()
        if not name:
            print("⚠ No name provided.")
            return

        # Resolve to on-disk key case-insensitively for robustness
        keys = self.db.list_items(self.current_type)
        key = next((k for k in keys if k.lower() == name.lower()), name)

        obj = self.db.reload(self.current_type, key)
        if obj is None:
            print(f"⚠ No such item '{name}'.")
            return
        print(f"Reloaded {key}.")

    def _resolve_type(self, inp: str):
        inp_low = inp.lower()
        matches = [t for t in OBJECT_TYPES if t.lower().startswith(inp_low)]
        return matches[0] if len(matches) == 1 else None

    def _check_current_type(self) -> bool:
        if self.current_type is None:
            print("⚠ No current type set. Use 'goto' first.")
            return False
        return True
