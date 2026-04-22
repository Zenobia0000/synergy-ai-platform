"""
FastAPI dependencies：資料載入與快取。

使用 lru_cache 確保每個 process 生命周期內只讀一次檔案。
測試中可透過 load_questionnaire.cache_clear() / load_products.cache_clear() 重置。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.services.parsers.validators import validate_questionnaire, validate_products

# data/schemas/ 位於專案根目錄
# deps.py 路徑：<root>/backend/app/api/deps.py
# parents: [0]=api, [1]=app, [2]=backend, [3]=<root>
DATA_SCHEMAS_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "schemas"


@lru_cache(maxsize=1)
def load_questionnaire() -> dict[str, Any]:
    """
    載入並 Pydantic 驗證 questionnaire.json，快取於記憶體。

    Raises:
        HTTPException 503: 檔案不存在（尚未執行 build_schemas.py）
        pydantic.ValidationError: 資料格式不符（讓 FastAPI 轉為 500）
    """
    path = DATA_SCHEMAS_DIR / "questionnaire.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Questionnaire schema not found. Run build_schemas.py first.",
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    validate_questionnaire(data)
    return data


@lru_cache(maxsize=1)
def load_products() -> dict[str, Any]:
    """
    載入並 Pydantic 驗證 products.json，快取於記憶體。

    Raises:
        HTTPException 503: 檔案不存在
        pydantic.ValidationError: 資料格式不符
    """
    path = DATA_SCHEMAS_DIR / "products.json"
    if not path.exists():
        raise HTTPException(
            status_code=503,
            detail="Products schema not found. Run build_schemas.py first.",
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    validate_products(data)
    return data


# ---------------------------------------------------------------------------
# AdviceService dependency
# ---------------------------------------------------------------------------

from app.core import LLMClient, get_settings  # noqa: E402
from app.services import AdviceService, get_default_config  # noqa: E402


@lru_cache(maxsize=1)
def _get_llm_client() -> LLMClient:
    """Singleton LLMClient，從 Settings 建構。"""
    return LLMClient(settings=get_settings())


@lru_cache(maxsize=1)
def get_advice_service() -> AdviceService:
    """
    FastAPI dependency：singleton AdviceService。

    warm_up 是 async，不在此處呼叫；AdviceService.advise() 首次呼叫時
    會自動觸發 warm_up，factory 不需要 await。

    測試中可透過 get_advice_service.cache_clear() 重置。
    """
    config = get_default_config()
    client = _get_llm_client()
    return AdviceService(config=config, client=client)
