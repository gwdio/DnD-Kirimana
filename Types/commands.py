# commands.py
from typing import Protocol, Dict, Any, runtime_checkable
from .results import Result
from .prompts import PromptGroup

@runtime_checkable
class Command(Protocol):
    """
    A command represents an action in the CLI, which requires user inputs and executes business logic.
    """
    name: str
    description: str

    def build_prompts(self) -> "PromptGroup":
        """Return a group of prompts for gathering input for the command."""
        pass

    def execute(self, params: Dict[str, Any]) -> Result:
        """Execute the command with the provided parameters and return a Result."""
        pass
