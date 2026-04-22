"""
整合測試共用 fixtures。

提供：
    mock_llm_complete_json  — 依序回傳預設 4 組 LLM 回應的 side_effect factory
    advice_service_config   — 指向真實 data/schemas/ 的設定
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.core import LLMClient
from app.services import AdviceService, AdviceServiceConfig

# data/schemas/ 位於專案根（backend 的上一層）
_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "data" / "schemas"


@pytest.fixture
def schemas_dir() -> Path:
    return _SCHEMAS_DIR


@pytest.fixture
def advice_service_config() -> AdviceServiceConfig:
    """指向真實 data/schemas/ 的 AdviceServiceConfig。"""
    return AdviceServiceConfig(
        questionnaire_path=_SCHEMAS_DIR / "questionnaire.json",
        products_path=_SCHEMAS_DIR / "products.json",
        rules_path=_SCHEMAS_DIR / "product_rules.json",
        max_candidates=15,
        max_products=3,
        max_next_actions=3,
    )


def _make_health_summary_response(
    overall_level: str = "medium",
    key_risks: list[str] | None = None,
) -> dict[str, Any]:
    if key_risks is None:
        key_risks = ["體重偏高（BMI 30.2）", "缺乏規律運動"]
    return {
        "key_risks": key_risks,
        "overall_level": overall_level,
        "narrative": (
            "客戶有體重偏高與缺乏運動的問題，建議優先從飲食控制與基礎產品搭配入手。"
            "整體風險屬中等，需持續關注代謝相關指標。"
        ),
        "disclaimers": ["本評估僅供健康諮詢參考，非醫療診斷。"],
    }


def _make_products_response() -> dict[str, Any]:
    return {
        "products": [
            {
                "sku": "PLACEHOLDER",
                "reason": "此產品符合客戶的體重管理需求，可協助提升代謝效率。",
                "confidence": 0.82,
            }
        ]
    }


def _make_scripts_response() -> dict[str, Any]:
    return {
        "scripts": [
            {
                "scenario": "opening",
                "script": "嗨！最近身體狀況怎麼樣？很多人到了這個年紀都感覺體力大不如前，有空輕鬆聊一下健康話題嗎？",
                "taboo": "不要一開口就講產品功效，先關心對方狀況。",
            },
            {
                "scenario": "follow_up",
                "script": "嗨！上次我們有聊過健康的話題，我整理了一些對你可能有幫助的資料，純粹分享沒有壓力喔！",
                "taboo": "不要催問對方考慮得怎麼樣了，保持輕鬆友善語氣。",
            },
        ]
    }


def _make_actions_response() -> dict[str, Any]:
    return {
        "actions": [
            {
                "action": "schedule_consultation",
                "why": "客戶有明確的體重管理目標且填答完整，適合安排深度商談。",
                "priority": "high",
            }
        ]
    }


def make_four_llm_responses(
    overall_level: str = "medium",
    key_risks: list[str] | None = None,
) -> list[dict[str, Any]]:
    """產生對應 pipeline 4 次 LLM 呼叫的回應列表。"""
    return [
        _make_health_summary_response(overall_level, key_risks),
        _make_products_response(),
        _make_scripts_response(),
        _make_actions_response(),
    ]
