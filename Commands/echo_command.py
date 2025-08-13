from typing import Dict, Any
from Types.results import Result
from Types.commands import Command
from Types.prompts import PromptGroup


class EchoCommand:
    name = "echo"
    description = "Echo back a message a given number of times."

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Echo",
            [
                {"name": "message", "question": "What should I echo?", "type": str},
                {"name": "times", "question": "How many times?", "type": int, "default": 1},
            ],
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        msg = params["message"]
        times = params["times"]
        return {
            "ok": True,
            "data": {"output": " ".join([msg] * times)},
        }
