from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    has_more: bool


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    error: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: list[T] = []
    error: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


def success_response(data: Any, **meta_fields) -> dict:
    result = {"success": True, "data": data}
    if meta_fields:
        result["meta"] = meta_fields
    return result


def paginated_response(
    data: list, total: int, page: int, limit: int
) -> dict:
    return {
        "success": True,
        "data": data,
        "meta": {
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "has_more": (page * limit) < total,
            }
        },
    }


def error_response(
    error_type: str,
    code: str,
    message: str,
    param: str | None = None,
) -> dict:
    error = {
        "type": error_type,
        "code": code,
        "message": message,
    }
    if param:
        error["param"] = param
    return {"success": False, "data": None, "error": error}
