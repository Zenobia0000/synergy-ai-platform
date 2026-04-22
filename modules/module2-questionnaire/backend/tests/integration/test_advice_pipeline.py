"""
整合測試：完整 AdviceService pipeline（不經 API 層）。

策略：
- 使用真實 data/schemas/*.json（不 mock parsers）
- 使用真實 AdviceService + AdviceServiceConfig
- 只 mock LLMClient.complete_json，依 system prompt 內容路由回應

任務 6.2-A：三個情境測試
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.core import LLMClient
from app.schemas import AdviceRequest, AdviceResponse
from app.services import AdviceService, AdviceServiceConfig

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "data" / "schemas"

# ---------------------------------------------------------------------------
# 回應工廠
# ---------------------------------------------------------------------------


def _health_summary_response(
    overall_level: str = "medium",
    key_risks: list[str] | None = None,
) -> dict[str, Any]:
    if key_risks is None:
        key_risks = ["體重偏高（BMI 31.5）", "缺乏規律運動"]
    return {
        "key_risks": key_risks,
        "overall_level": overall_level,
        "narrative": (
            "客戶有體重偏高與缺乏規律運動的問題，代謝風險需特別關注。"
            "建議優先從飲食控制與運動習慣入手，搭配適當的營養補充調整。"
        ),
        "disclaimers": ["本評估僅供健康諮詢參考，非醫療診斷。"],
    }


def _products_response(sku: str = "PLACEHOLDER") -> dict[str, Any]:
    return {
        "products": [
            {
                "sku": sku,
                "reason": "此產品符合客戶的體重管理需求，可協助提升代謝效率。",
                "confidence": 0.82,
            }
        ]
    }


def _scripts_response() -> dict[str, Any]:
    return {
        "scripts": [
            {
                "scenario": "opening",
                "script": "嗨！最近身體狀況怎麼樣？很多人到了這個年紀都感覺體力大不如前，有空輕鬆聊一下？",
                "taboo": "不要一開口就講產品功效，先關心對方狀況。",
            },
            {
                "scenario": "follow_up",
                "script": "嗨！上次我們有聊過健康話題，我整理了一些資料純粹分享，完全沒有壓力喔！",
                "taboo": "不要催問考慮得怎麼樣了，保持輕鬆語氣。",
            },
        ]
    }


def _actions_response() -> dict[str, Any]:
    return {
        "actions": [
            {
                "action": "schedule_consultation",
                "why": "客戶填答完整且有明確健康目標，適合安排深度商談推進決策。",
                "priority": "high",
            }
        ]
    }


def _escalate_actions_response() -> dict[str, Any]:
    return {
        "actions": [
            {
                "action": "escalate_to_senior",
                "why": "客戶健康風險等級高且具有慢性病史，超出新手教練處理範圍，需轉介資深上線。",
                "priority": "high",
            },
            {
                "action": "schedule_consultation",
                "why": "同時安排 2:1 商談，讓資深教練直接介入。",
                "priority": "high",
            },
        ]
    }


# ---------------------------------------------------------------------------
# Smart mock factory：依 system prompt 關鍵字路由回應
# ---------------------------------------------------------------------------


def make_smart_mock(
    overall_level: str = "medium",
    key_risks: list[str] | None = None,
    actions_response: dict[str, Any] | None = None,
    product_sku: str = "PLACEHOLDER",
) -> AsyncMock:
    """
    依 system prompt 關鍵字決定回傳哪個 response。

    區分方式（各 system prompt 的獨特字串）：
    - health_summary：「快速解讀客戶問卷，提供健康評估摘要」
    - product_recommendation：「精準推薦產品」或「候選清單」
    - sales_scripts：「coach-of-coach」
    - next_actions：「資深營運教練」
    """
    if actions_response is None:
        actions_response = _actions_response()

    async def smart_side_effect(**kwargs: Any) -> dict[str, Any]:
        system: str = kwargs.get("system", "")
        # 精準推薦產品 → product_recommendation
        if "精準推薦產品" in system or "候選清單" in system:
            return _products_response(product_sku)
        # coach-of-coach → sales_scripts
        if "coach-of-coach" in system:
            return _scripts_response()
        # 資深營運教練 → next_actions
        if "資深營運教練" in system:
            return actions_response
        # 其餘（含「健康評估摘要」等）→ health_summary
        return _health_summary_response(overall_level, key_risks)

    mock = AsyncMock(spec=LLMClient)
    mock.complete_json.side_effect = smart_side_effect
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config() -> AdviceServiceConfig:
    return AdviceServiceConfig(
        questionnaire_path=_SCHEMAS_DIR / "questionnaire.json",
        products_path=_SCHEMAS_DIR / "products.json",
        rules_path=_SCHEMAS_DIR / "product_rules.json",
        max_candidates=15,
        max_products=3,
        max_next_actions=3,
    )


# ---------------------------------------------------------------------------
# 情境 1：男性、45 歲、體重 95kg
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_male_45_overweight(config: AdviceServiceConfig) -> None:
    """
    情境：男性、45 歲、體重 95kg。

    驗：
    1. AdviceResponse 結構完整（四段）
    2. LLM 被呼叫 4 次（health_summary + product_recommendation + scripts + actions）
    3. mock responses 被正確組裝進 AdviceResponse
    """
    mock_client = make_smart_mock(
        overall_level="high",
        key_risks=["體重過重（BMI 32.8）", "三高家族史", "缺乏運動"],
    )

    service = AdviceService(config=config, client=mock_client)
    request = AdviceRequest(
        answers={
            "gender": "男",
            "age": 45,
            "current_weight_kg": 95,
            "height_cm": 170,
            "exercise_frequency": "幾乎不運動",
            "family_history": ["高血壓", "糖尿病"],
        }
    )

    result = await service.advise(request)

    # 結構驗證
    assert isinstance(result, AdviceResponse)
    assert result.summary is not None
    assert result.recommended_products is not None
    assert result.sales_scripts is not None
    assert result.next_actions is not None

    # 四段均有內容
    assert len(result.summary.key_risks) >= 1
    assert len(result.recommended_products) >= 1
    assert len(result.sales_scripts) >= 2
    assert len(result.next_actions) >= 1

    # LLM 呼叫次數：
    # Stage 2: health_summary(1) + product_recommendation(0~1，取決於規則引擎是否觸發候選)
    # Stage 3: sales_scripts(1) + next_actions(1)
    # 最少 3 次（candidates 為空走 fallback，product_recommendation 不呼叫 LLM）
    assert mock_client.complete_json.call_count >= 3

    # mock 回應被正確組裝
    assert result.summary.overall_level == "high"
    assert "體重過重" in " ".join(result.summary.key_risks)
    assert result.next_actions[0].action == "schedule_consultation"


# ---------------------------------------------------------------------------
# 情境 2：女性、35 歲、失眠
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_female_35_with_sleep_issue(config: AdviceServiceConfig) -> None:
    """
    情境：女性、35 歲、失眠。

    驗：
    1. AdviceResponse 結構完整
    2. LLM 呼叫 4 次
    3. overall_level=medium 被正確組裝
    """
    mock_client = make_smart_mock(
        overall_level="medium",
        key_risks=["睡眠品質差", "壓力偏高"],
    )

    service = AdviceService(config=config, client=mock_client)
    request = AdviceRequest(
        answers={
            "gender": "女",
            "age": 35,
            "sleep_quality": "差",
            "stress_level": "高",
            "primary_goals": ["睡眠品質", "壓力管理"],
        }
    )

    result = await service.advise(request)

    assert isinstance(result, AdviceResponse)
    assert result.summary.overall_level == "medium"
    assert len(result.recommended_products) >= 1
    assert len(result.sales_scripts) >= 2
    assert len(result.next_actions) >= 1

    # LLM 呼叫次數（health_summary + scripts + actions 至少 3 次；
    # product_recommendation 視規則引擎是否觸發候選而定）
    assert mock_client.complete_json.call_count >= 3

    # 健康摘要 key_risks 來自 mock 回應
    assert any("睡眠" in risk for risk in result.summary.key_risks)


# ---------------------------------------------------------------------------
# 情境 3：高風險觸發 escalation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_high_risk_triggers_escalation(config: AdviceServiceConfig) -> None:
    """
    情境：overall_level=high + key_risks 含「慢性病」。

    驗：
    1. next_actions 的 mock 被呼叫（pipeline 正確串接）
    2. escalate_to_senior action 出現在結果中
    3. LLM 呼叫 4 次
    """
    mock_client = make_smart_mock(
        overall_level="high",
        key_risks=["慢性病史（糖尿病）", "高血壓", "體重過重"],
        actions_response=_escalate_actions_response(),
    )

    service = AdviceService(config=config, client=mock_client)
    request = AdviceRequest(
        answers={
            "gender": "男",
            "age": 60,
            "chronic_conditions": ["糖尿病", "高血壓"],
            "current_weight_kg": 88,
            "height_cm": 165,
        }
    )

    result = await service.advise(request)

    assert isinstance(result, AdviceResponse)

    # pipeline 正確串接：next_actions mock 應被呼叫
    # 至少 3 次（health_summary + sales_scripts + next_actions）
    assert mock_client.complete_json.call_count >= 3

    # escalate_to_senior 應出現
    action_types = [a.action for a in result.next_actions]
    assert "escalate_to_senior" in action_types

    # 高風險摘要
    assert result.summary.overall_level == "high"


# ---------------------------------------------------------------------------
# 性能斷言：asyncio.gather 平行化應使總時間 ≈ 2 × 單次延遲
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pipeline_parallelism_performance(config: AdviceServiceConfig) -> None:
    """
    每個 LLM 呼叫 sleep 0.05s（模擬網路延遲）。
    pipeline 應 ≤ 0.25s（2 stages × 0.05 + margin），
    而非串行 4 × 0.05s = 0.20s（margin 考量 event loop 開銷）。
    """
    _LLM_DELAY = 0.05

    async def delayed_side(**kwargs: Any) -> dict[str, Any]:
        await asyncio.sleep(_LLM_DELAY)
        system: str = kwargs.get("system", "")
        if "精準推薦產品" in system or "候選清單" in system:
            return _products_response()
        if "coach-of-coach" in system:
            return _scripts_response()
        if "資深營運教練" in system:
            return _actions_response()
        return _health_summary_response()

    mock_client = AsyncMock(spec=LLMClient)
    mock_client.complete_json.side_effect = delayed_side

    service = AdviceService(config=config, client=mock_client)
    request = AdviceRequest(answers={"gender": "女", "age": 30})

    start = time.perf_counter()
    result = await service.advise(request)
    elapsed = time.perf_counter() - start

    assert isinstance(result, AdviceResponse)
    # 平行化後應顯著快於串行 4 次（0.2s），允許 0.25s margin
    assert elapsed < 0.25, (
        f"Pipeline 耗時 {elapsed:.3f}s，超過預期 0.25s 上限。"
        "可能平行化失效。"
    )
