from typing import Any

from app.schemas.response import ApiResponse


def success_response(data: Any = None, message: str | None = None, meta: dict[str, Any] | None = None) -> ApiResponse[Any]:
    return ApiResponse(success=True, data=data, message=message, meta=meta or {})


def error_response(message: str, errors: dict[str, Any] | None = None, meta: dict[str, Any] | None = None) -> dict:
    return ApiResponse(success=False, data=None, message=message, meta=meta or {}).model_dump()
