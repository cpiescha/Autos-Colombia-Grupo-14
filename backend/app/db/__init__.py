from typing import Any

from app.db.base import Base
from app.db.exceptions import PersistenceError

__all__ = [
    "Base",
    "PersistenceError",
    "close_stay_by_receipt",
    "correct_parking_spot",
]


def __getattr__(name: str) -> Any:
    """Load database operations lazily to avoid model import cycles."""
    if name == "close_stay_by_receipt":
        from app.db.operations import close_stay_by_receipt

        return close_stay_by_receipt
    if name == "correct_parking_spot":
        from app.db.operations import correct_parking_spot

        return correct_parking_spot
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
