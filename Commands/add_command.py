from typing import Dict, Any
from Types.results import Result
from Types.commands import Command
from Types.prompts import PromptGroup

class AddCommand:
    name = "add"
    description = "Add two numbers together."

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Addition",
            [
                {"name": "a", "question": "First number?", "type": float},
                {"name": "b", "question": "Second number?", "type": float},
            ],
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        a = params["a"]
        b = params["b"]
        return {
            "ok": True,
            "message": f"Sum of {a} and {b} is {a + b}",
            "data": {"sum": a + b},
        }
