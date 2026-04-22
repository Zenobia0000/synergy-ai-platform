"""
路由模組：問卷 schema 與產品目錄端點。

/questionnaire/schema  — 前端表單渲染用
/products              — Debug / 管理用，支援 category filter 與 limit
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import load_products, load_questionnaire

router = APIRouter(tags=["schema"])


@router.get("/questionnaire/schema", response_model=None)
async def get_questionnaire_schema(
    data: dict[str, Any] = Depends(load_questionnaire),
) -> dict[str, Any]:
    """Return the full questionnaire JSON schema for frontend rendering."""
    return data


@router.get("/products", response_model=None)
async def list_products(
    category: str | None = Query(default=None, description="依分類篩選"),
    limit: int = Query(default=100, ge=1, description="最多回傳筆數"),
    data: dict[str, Any] = Depends(load_products),
) -> dict[str, Any]:
    """
    List products. Optional ?category filter, ?limit (default 100).

    回傳格式：
      {
        "_meta": {...},
        "products": [...],   # 已套用 category filter 與 limit
        "total": int,        # category filter 後的總筆數（不受 limit 影響）
      }
    """
    all_products: list[dict[str, Any]] = data["products"]
    total_all = len(all_products)

    if category is not None:
        filtered = [p for p in all_products if p.get("category") == category]
    else:
        filtered = all_products

    return {
        "_meta": data["_meta"],
        "products": filtered[:limit],
        "total": total_all,
    }
