from typing import Any, Generic, TypeVar

from app.schemas.response import ApiResponse

T = TypeVar("T")


def success_response(data: Any = None, message: str | None = None, meta: dict[str, Any] | None = None) -> ApiResponse[Any]:
    """Deprecated: Use ResponseHandler.success() instead."""
    return ApiResponse(success=True, data=data, message=message, meta=meta or {})


def error_response(message: str, errors: dict[str, Any] | None = None, meta: dict[str, Any] | None = None) -> dict:
    """Deprecated: Use ResponseHandler.error() instead."""
    return ApiResponse(success=False, data=None, message=message, meta=meta or {}).model_dump()


class ResponseHandler:
    """Centralized response creation handler. Use this for all API responses."""

    @staticmethod
    def success(
        data: Any = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ApiResponse[Any]:
        """Create a successful response."""
        return ApiResponse(
            success=True,
            data=data,
            message=message,
            meta=meta or {},
        )

    @staticmethod
    def error(
        message: str,
        errors: dict[str, Any] | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict:
        """Create an error response."""
        return ApiResponse(
            success=False,
            data=None,
            message=message,
            meta=meta or {},
        ).model_dump()

    @staticmethod
    def created(
        data: Any = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ApiResponse[Any]:
        """Create a resource created response (201)."""
        return ResponseHandler.success(data, message or "Resource created", meta)

    @staticmethod
    def updated(
        data: Any = None,
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ApiResponse[Any]:
        """Create a resource updated response."""
        return ResponseHandler.success(data, message or "Resource updated", meta)

    @staticmethod
    def deleted(
        message: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ApiResponse[None]:
        """Create a resource deleted response."""
        return ResponseHandler.success(None, message or "Resource deleted", meta)
