from typing import Any


def to_bool(value: Any) -> bool:
    return str(value)[:1].lower() in ("t", "y", "1") or str(value).lower() == "on"
