from typing import Dict, Any, List, Tuple
import random
import re
from Types.results import Result
from Types.prompts import PromptGroup

class DiceRollerCommand:
    name = "dice"
    description = "Roll dice using flexible input formats. Continuous mode if no input."

    def build_prompts(self) -> PromptGroup:
        return PromptGroup.from_specs(
            "Dice Roller",
            [
                {
                    "name": "input",
                    "question": "Enter dice roll expression (leave blank for continuous mode)",
                    "type": str,
                    "default": ""
                },
            ],
        )

    def execute(self, params: Dict[str, Any]) -> Result:
        expr = params.get("input", "").strip()
        if not expr:
            # Continuous mode
            print("🎲 Continuous dice mode. Type 'exit', 'quit', or 'q' to leave.")
            while True:
                expr = input("dice> ").strip()
                if expr.lower() in ("exit", "quit", "q"):
                    break
                if not expr:
                    continue
                self._roll_and_print(expr)
            return {"ok": True, "message": "Exited continuous dice mode."}

        # One-shot mode
        return self._roll_and_return(expr)

    def _roll_and_return(self, expr: str) -> Result:
        dice_groups, rolls, total_sum = self._parse_and_roll(expr)
        message, data = self._format_output(dice_groups, rolls, total_sum)
        return {"ok": True, "message": message, "data": data}

    def _roll_and_print(self, expr: str):
        dice_groups, rolls, total_sum = self._parse_and_roll(expr)
        message, _ = self._format_output(dice_groups, rolls, total_sum)
        print(message)

    def _parse_and_roll(self, expr: str) -> Tuple[Dict[str, List[int]], List[int], int]:
        expr = expr.replace(" ", "")
        token_pattern = re.compile(r"([+-]?\d*d?\d+)")
        tokens = token_pattern.findall(expr)

        dice_groups: Dict[str, List[int]] = {}
        rolls: List[int] = []
        total_sum = 0

        for token in tokens:
            sign = 1
            if token.startswith("+"):
                token = token[1:]
            elif token.startswith("-"):
                token = token[1:]
                sign = -1

            if "d" in token:
                num_str, sides_str = token.split("d", 1)
                num = int(num_str) if num_str else 1
                sides = int(sides_str)
                for _ in range(num):
                    roll = random.randint(1, sides)
                    rolls.append(roll * sign)
                    dice_groups.setdefault(f"d{sides}", []).append(roll * sign)
                    total_sum += roll * sign
            else:
                mod = int(token) * sign
                rolls.append(mod)
                dice_groups.setdefault("modifiers", []).append(mod)
                total_sum += mod

        return dice_groups, rolls, total_sum

    def _format_output(self, dice_groups: Dict[str, List[int]], rolls: List[int], total_sum: int) -> Tuple[str, Dict[str, Any]]:
        data: Dict[str, Any] = {}
        message_lines: List[str] = []

        dice_only = {k: v for k, v in dice_groups.items() if k != "modifiers"}
        has_modifier = "modifiers" in dice_groups

        if len(dice_only) == 1:
            dice_type, results = next(iter(dice_only.items()))
            n = len(results)

            if n == 1:
                message_lines.append(f"{dice_type} roll: {results[0]}")
                data = {"roll": results[0]}
            elif n <= 3:
                msg = ", ".join(f"{dice_type} roll{i + 1}: {r}" for i, r in enumerate(results))
                message_lines.append(msg)
                data = {f"roll{i + 1}": r for i, r in enumerate(results)}
                message_lines.append(f"Sum: {sum(results) + sum(dice_groups.get('modifiers', []))}")
                data["sum"] = sum(results) + sum(dice_groups.get("modifiers", []))
            else:
                message_lines.append(f"Raw: {', '.join(map(str, results))}")
                message_lines.append(f"Sorted: {sorted(results)}")
                message_lines.append(f"Max: {max(results)}")
                message_lines.append(f"Min: {min(results)}")
                message_lines.append(f"Sum: {sum(results) + sum(dice_groups.get('modifiers', []))}")
                data = {
                    "raw": results,
                    "sorted": sorted(results),
                    "max": max(results),
                    "min": min(results),
                    "sum": sum(results) + sum(dice_groups.get("modifiers", [])),
                }
        else:
            for dice_type, results in dice_only.items():
                message_lines.append(f"{dice_type} rolls: {', '.join(map(str, results))}")
                data[dice_type] = results
            message_lines.append(f"Sum: {sum(rolls)}")
            data["sum"] = sum(rolls)

        if has_modifier and "sum" not in data:
            message_lines.append(f"Sum: {sum(rolls)}")
            data["sum"] = sum(rolls)

        return "\n".join(message_lines), data
