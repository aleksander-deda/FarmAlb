from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class ApiResponse(GenericModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    meta: dict[str, Any] = {}


class ApiErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    message: str
    errors: dict[str, Any] | None = None
    meta: dict[str, Any] = {}
