"""
Base service manager providing common functionality for all services.
"""
from typing import Any
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session


class BaseService:
    """Base service class with common utilities and patterns."""

    def __init__(self):
        """Initialize base service."""
        pass

    @staticmethod
    def round_amount(value: float) -> float:
        """Round monetary amounts to 2 decimal places."""
        return float(
            Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    @staticmethod
    def serialize_dict(data: dict[str, Any] | None) -> dict[str, Any]:
        """Serialize a dictionary for audit logging or storage."""
        if data is None:
            return {}
        return data
