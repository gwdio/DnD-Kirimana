# results.py
from typing import TypedDict, Optional, Dict, Any

class Result(TypedDict, total=False):
    """
    A structured result from command execution.
    Keys:
    - ok: whether the operation was successful
    - message: a message describing the result (e.g., success, failure)
    - error: an error message if the operation failed
    - data: the payload data if any (used for commands that return detailed results)
    """
    ok: bool
    message: Optional[str]
    error: Optional[str]
    data: Optional[Dict[str, Any]]
