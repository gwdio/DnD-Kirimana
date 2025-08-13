# orchestrator.py

import difflib
from typing import Optional, List
from .registry import CommandRegistry


class Orchestrator:
    PROMPT = "cmd> "

    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry

    def _print_banner(self) -> None:
        print("=" * 64)
        print(" Kirimana Helper CLI • type 'help' for commands, 'exit' to quit ")
        print("=" * 64)

    def _print_help(self) -> None:
        print("\nAvailable commands:")
        for name, desc in self.registry.list_commands().items():
            print(f"  {name:<16} {desc}")
        print("\nBuilt-ins: help, exit, quit")

    def _suggest(self, unknown: str) -> None:
        candidates = difflib.get_close_matches(unknown, self.registry.list_commands().keys(), n=3, cutoff=0.5)
        if candidates:
            print("Did you mean:", ", ".join(candidates))

    def run(self, argv: Optional[List[str]] = None) -> None:
        self._print_banner()
        if argv and len(argv) > 0:
            # one-shot mode: treat argv as a single command line
            self._dispatch_line(" ".join(argv))
            return
        while True:
            try:
                line = input(self.PROMPT)
            except (EOFError, KeyboardInterrupt):
                print("\nbye")
                break
            if not line.strip():
                continue
            if not self._dispatch_line(line):
                break

    def _dispatch_line(self, line: str) -> bool:
        try:
            parts = line.split()
        except ValueError as e:
            print(f"Parse error: {e}")
            return True

        if not parts:
            return True
        cmd_name, *rest = parts
        cmd_name = cmd_name.lower()

        # built-ins
        if cmd_name in {"exit", "quit", "q"}:
            print("bye")
            return False
        if cmd_name == "help":
            self._print_help()
            return True

        # known command?
        cmd = self.registry.resolve(cmd_name)
        if not cmd:
            print(f"Unknown command: '{cmd_name}'")
            self._suggest(cmd_name)
            return True

        # ask for parameters via PromptGroup
        group = cmd.build_prompts()
        if group is not None:
            try:
                params = group.ask_all()
            except Exception as e:
                print(f"Input aborted: {e}")
                return True
        else:
            params = {}  # No prompts needed

        # execute
        try:
            result = cmd.execute(params)
        except Exception as e:
            print(f"✖ Execution error: {e}")
            return True

        # render result
        if result.get("ok", False):
            if result.get("message"):  # message takes priority
                print(result["message"])
            elif "data" in result and result["data"]:
                for k, v in result["data"].items():
                    print(f"  {k}: {v}")
            else:
                print("✔ Success")
        else:
            print("✖ " + (result.get("error") or "Unknown error"))
        return True
