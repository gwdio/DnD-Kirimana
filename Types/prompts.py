import json
from typing import List, Dict, Optional, Any, Callable, TypeVar, Generic, Tuple, Union

T = TypeVar("T")

class Prompt(Generic[T]):
    def __init__(
        self,
        question: str,
        type_: Union[type, Callable[[str], T]],
        *,
        name: Optional[str] = None,
        default: Optional[T] = None,
        choices: Optional[List[T]] = None,
        validator: Optional[Callable[[T], Union[bool, Tuple[bool, str]]]] = None,
        formatter: Optional[Callable[[T], str]] = None,
        help_text: Optional[str] = None,
        retries: int = 3,
        optional: bool = False,  # NEW
    ) -> None:
        self.question = question
        self.type_ = type_
        self.name = name or self._infer_name(question)
        self.default = default
        self.choices = choices
        self.validator = validator
        self.formatter = formatter
        self.help_text = help_text
        self.retries = max(1, retries)
        self.optional = optional  # NEW

    def _infer_name(self, q: str) -> str:
        return (
            q.lower()
            .replace("?", "")
            .replace("/", " ")
            .replace("-", " ")
            .strip()
            .replace(" ", "_")
        )

    def _convert(self, s: str) -> T:
        if callable(self.type_) and self.type_ not in (int, float, str, bool):
            return self.type_(s)
        if self.type_ is bool:
            val = s.strip().lower()
            if val in ("y", "yes", "true", "1"): return True
            if val in ("n", "no", "false", "0"): return False
            raise ValueError("Enter yes/no, true/false, y/n, or 1/0")
        if self.type_ is int:
            return int(s)
        if self.type_ is float:
            return float(s)
        if self.type_ is str:
            return s
        if self.type_ is tuple:
            parts = [p.strip() for p in s.split(",")]
            return tuple(parts)
        try:
            return json.loads(s)
        except Exception as e:
            raise ValueError(f"Could not parse value: {e}")

    def _validate(self, v: T) -> Tuple[bool, Optional[str]]:
        if self.choices is not None and v not in self.choices:
            return False, f"Value must be one of: {', '.join(map(str, self.choices))}"
        if self.validator is not None:
            res = self.validator(v)
            if isinstance(res, tuple):
                return res
            return (bool(res), None if res else "Custom validation failed")
        return True, None

    def ask(self, *, input_fn: Callable[[str], str] = input, print_fn: Callable[[str], None] = print) -> T:
        attempts = self.retries
        while attempts:
            default_str = f" [default: {self.default}]" if self.default is not None else ""
            optional_str = " (optional)" if self.optional else ""
            if self.help_text:
                print_fn(f"Hint: {self.help_text}")
            raw = input_fn(f"{self.question}{optional_str}{default_str}: ").strip()

            # Optional handling: empty = None
            if raw == "":
                if self.optional:
                    return None
                elif self.default is not None:
                    return self.default
                else:
                    print_fn("✖ This field is required.")
                    attempts -= 1
                    continue

            try:
                value = self._convert(raw)
            except Exception as e:
                print_fn(f"✖ Invalid input: {e}")
                attempts -= 1
                continue

            ok, msg = self._validate(value)
            if not ok:
                print_fn(f"✖ {msg or 'Invalid value.'}")
                attempts -= 1
                continue

            return value

        raise ValueError(f"Too many invalid attempts for '{self.name}'.")

    @classmethod
    def from_spec(cls, spec: Dict[str, Any]) -> "Prompt":
        return cls(
            question=spec.get("question") or spec.get("q") or "",
            type_=spec.get("type") or str,
            name=spec.get("name"),
            default=spec.get("default"),
            choices=spec.get("choices"),
            validator=spec.get("validator"),
            formatter=spec.get("formatter"),
            help_text=spec.get("help"),
            retries=spec.get("retries", 3),
            optional=spec.get("optional", False),  # NEW
        )


class PromptGroup:
    def __init__(self, name: str, prompts: Optional[List[Prompt[Any]]] = None) -> None:
        self.name = name
        self.prompts: List[Prompt[Any]] = prompts or []
        self._index: Dict[str, Prompt[Any]] = {p.name: p for p in self.prompts}

    def add(self, prompt: Prompt[Any]) -> None:
        self.prompts.append(prompt)
        self._index[prompt.name] = prompt

    def get(self, name: str) -> Prompt[Any]:
        return self._index[name]

    def ask_all(self, *, input_fn: Callable[[str], str] = input, print_fn: Callable[[str], None] = print) -> Dict[str, Any]:
        print_fn(f"\n=== {self.name} ===")
        results: Dict[str, Any] = {}
        for p in self.prompts:
            results[p.name] = p.ask(input_fn=input_fn, print_fn=print_fn)
        return results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "prompts": [
                {
                    "question": p.question,
                    "type": getattr(p.type_, "__name__", str(p.type_)),
                    "name": p.name,
                    "default": p.default,
                    "choices": p.choices,
                    "help": p.help_text,
                    "retries": p.retries,
                }
                for p in self.prompts
            ],
        }

    @classmethod
    def from_specs(
        cls,
        name: str,
        specs: List[Dict[str, Any]],
        *,
        shared: Optional[Dict[str, Any]] = None,
    ) -> "PromptGroup":
        shared = shared or {}
        prompts: List[Prompt[Any]] = []
        for spec in specs:
            merged = {**shared, **spec}
            prompts.append(Prompt.from_spec(merged))
        return cls(name, prompts)

    @classmethod
    def from_mapping(cls, name: str, mapping: Dict[str, Union[Prompt[Any], Dict[str, Any]]]) -> "PromptGroup":
        prompts: List[Prompt[Any]] = []
        for key, val in mapping.items():
            if isinstance(val, Prompt):
                p = val
            else:
                p = Prompt.from_spec({"name": key, **val})
            prompts.append(p)
        return cls(name, prompts)
