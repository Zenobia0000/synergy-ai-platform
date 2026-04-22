"""
共用 pytest fixtures，供 prompts 測試套件使用。

fixtures:
    mock_llm_client   — AsyncMock(spec=LLMClient)
    sample_answers    — 典型問卷答案（含 PII 欄位供過濾測試）
    prompt_context    — 用真實 questionnaire.json 載入的 PromptContext
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.core import LLMClient
from app.services.prompts.base import PromptContext, build_field_label_map

# questionnaire.json 的絕對路徑（相對於專案根目錄）
_QUESTIONNAIRE_PATH = Path(__file__).resolve().parents[4] / "data" / "schemas" / "questionnaire.json"


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """回傳一個 AsyncMock，spec 為 LLMClient。"""
    client = AsyncMock(spec=LLMClient)
    return client


@pytest.fixture
def sample_answers() -> dict:
    """
    典型問卷答案字典，包含：
    - PII 欄位（name、email、phone）用於 PII 過濾測試
    - 健康相關欄位用於正常流程測試
    """
    return {
        # PII 欄位
        "name": "王小明",
        "email": "user@example.com",
        "phone": "0912-345-678",
        # 健康欄位
        "gender": "男",
        "age": 45,
        "height_cm": 170,
        "current_weight_kg": 95,
        "primary_goals": ["體重管理", "睡眠品質"],
        "family_history": ["高血壓", "糖尿病", "高血脂"],
        "sleep_quality": "差",
        "stress_level": "高",
        "exercise_frequency": "幾乎不運動",
    }


@pytest.fixture
def prompt_context() -> PromptContext:
    """用真實 questionnaire.json 建立 PromptContext。"""
    label_map = build_field_label_map(_QUESTIONNAIRE_PATH)
    return PromptContext(
        questionnaire_labels=label_map,
        coach_level="new",
        locale="zh-TW",
    )


@pytest.fixture
def valid_summary_dict() -> dict:
    """合法的 HealthAssessmentSummary dict，供 mock 回傳使用。"""
    return {
        "key_risks": ["體重過重（BMI 32.8）", "三高家族史", "睡眠品質差"],
        "overall_level": "high",
        "narrative": (
            "客戶為 45 歲男性，體重 95kg，BMI 約 32.8，屬肥胖範圍。"
            "家族有高血壓、糖尿病、高血脂三高病史，自身風險偏高。"
            "睡眠品質差且壓力高，代謝狀況需重點關注。"
            "建議優先進行體重管理並改善睡眠，搭配適當的營養補充。"
        ),
        "disclaimers": [
            "本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適或正在治療中，請優先遵循醫師建議。"
        ],
    }
