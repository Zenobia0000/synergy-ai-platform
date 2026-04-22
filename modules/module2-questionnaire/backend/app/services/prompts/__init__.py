"""
prompts 套件：LLM Prompt 工程模組集合。

目前匯出：
    generate_health_summary  — 健康研判摘要（WBS 任務 3.1）

product_recommendation（任務 3.2）平行進行中，用 try/except 避免尚未完成時爆炸。
"""

from __future__ import annotations

from app.services.prompts.health_summary import generate_health_summary

__all__ = ["generate_health_summary"]

try:
    from app.services.prompts.product_recommendation import (  # type: ignore[import]
        generate_product_recommendation,
    )

    __all__ = [*__all__, "generate_product_recommendation"]
except ImportError:
    pass
