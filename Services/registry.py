# registry.py
from typing import Dict, Optional
from Types.commands import Command

class CommandRegistry:
    """
    The CommandRegistry keeps track of all available commands in the system.
    You can register new commands and resolve them by name.
    """
    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(self, cmd: Command) -> None:
        """Register a new command."""
        if not isinstance(cmd, Command):
            raise TypeError(f"{cmd!r} does not implement Command interface")
        self._commands[cmd.name] = cmd

    def resolve(self, name: str) -> Optional[Command]:
        """Resolve a command by its name."""
        return self._commands.get(name)

    def list_commands(self) -> Dict[str, str]:
        """List all registered commands with their descriptions."""
        return {cmd.name: cmd.description for cmd in self._commands.values()}
