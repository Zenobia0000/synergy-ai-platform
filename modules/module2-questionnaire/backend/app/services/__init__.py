"""
services 套件入口。

匯出：
    AdviceService        — 四模組 orchestrator
    AdviceServiceConfig  — 服務設定 frozen dataclass
    get_default_config   — 專案根感知的預設設定 factory（供 API 層使用）
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.services.advice_service import AdviceService, AdviceServiceConfig

__all__ = [
    "AdviceService",
    "AdviceServiceConfig",
    "get_default_config",
]


@lru_cache(maxsize=1)
def get_default_config() -> AdviceServiceConfig:
    """
    回傳專案根感知的預設 AdviceServiceConfig。

    路徑計算：從此檔案向上三層（services → app → backend → 專案根），
    再進入 data/schemas/ 目錄。

    快取：lru_cache(maxsize=1) 確保整個程序只建立一次，避免重複 I/O。

    Returns
    -------
    AdviceServiceConfig
        指向 data/schemas/ 下三個 JSON 的設定物件。
    """
    root = Path(__file__).resolve().parents[3]  # backend/ 的上一層 = 專案根
    return AdviceServiceConfig(
        questionnaire_path=root / "data" / "schemas" / "questionnaire.json",
        products_path=root / "data" / "schemas" / "products.json",
        rules_path=root / "data" / "schemas" / "product_rules.json",
    )
