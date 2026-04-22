"""
整合測試：API 層 E2E（POST /advise）。

策略：
- 使用 FastAPI TestClient
- 用真實 AdviceService 實例（不 override dependency，override LLMClient）
- 只 mock LLMClient.complete_json

任務 6.2-B：4 個測試案例
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_advice_service
from app.api.main import app
from app.core import LLMClient
from app.schemas import AdviceResponse
from app.services import AdviceService, AdviceServiceConfig

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "data" / "schemas"

# ---------------------------------------------------------------------------
# 回應工廠（與 test_advice_pipeline.py 保持一致）
# ---------------------------------------------------------------------------


def _health_summary_response(
    overall_level: str = "medium",
) -> dict[str, Any]:
    return {
        "key_risks": ["體重偏高", "缺乏運動"],
        "overall_level": overall_level,
        "narrative": (
            "客戶有體重偏高與缺乏運動的問題，需特別注意代謝風險。"
            "建議優先從飲食控制與運動習慣入手，並搭配適當的營養調整。"
        ),
        "disclaimers": ["本評估僅供健康諮詢參考，非醫療診斷。"],
    }


def _products_response(sku: str = "PLACEHOLDER") -> dict[str, Any]:
    return {
        "products": [
            {
                "sku": sku,
                "reason": "此產品符合客戶的體重管理需求，可協助提升代謝效率達成目標。",
                "confidence": 0.82,
            }
        ]
    }


def _scripts_response() -> dict[str, Any]:
    return {
        "scripts": [
            {
                "scenario": "opening",
                "script": "嗨！最近身體狀況怎麼樣？很多人到了這個年紀都感覺體力大不如前，有空輕鬆聊一下健康嗎？",
                "taboo": "不要一開口就講產品功效，先關心對方狀況。",
            },
            {
                "scenario": "follow_up",
                "script": "嗨！上次有聊過健康話題，我整理了一些對你可能有幫助的資料，純粹分享沒有壓力喔！",
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


def make_smart_mock_client() -> AsyncMock:
    """依 system prompt 關鍵字路由回應的 LLMClient mock。"""

    async def smart_side(**kwargs: Any) -> dict[str, Any]:
        system: str = kwargs.get("system", "")
        # product_recommendation 的獨特字串
        if "精準推薦產品" in system or "候選清單" in system:
            return _products_response()
        # sales_scripts
        if "coach-of-coach" in system:
            return _scripts_response()
        # next_actions
        if "資深營運教練" in system:
            return _actions_response()
        # health_summary（其餘）
        return _health_summary_response()

    mock = AsyncMock(spec=LLMClient)
    mock.complete_json.side_effect = smart_side
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def real_service_with_mock_llm() -> AdviceService:
    """真實 AdviceService 實例，搭配 mock LLMClient。"""
    config = AdviceServiceConfig(
        questionnaire_path=_SCHEMAS_DIR / "questionnaire.json",
        products_path=_SCHEMAS_DIR / "products.json",
        rules_path=_SCHEMAS_DIR / "product_rules.json",
        max_candidates=15,
        max_products=3,
        max_next_actions=3,
    )
    mock_client = make_smart_mock_client()
    return AdviceService(config=config, client=mock_client)


@pytest.fixture
def e2e_client(real_service_with_mock_llm: AdviceService) -> TestClient:
    """覆寫 get_advice_service dependency，注入真實 service + mock LLM。"""
    app.dependency_overrides[get_advice_service] = lambda: real_service_with_mock_llm
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 測試 1：真實 service + mock LLM 4 次回應 → HTTP 200 + 完整結構
# ---------------------------------------------------------------------------


def test_post_advise_full_pipeline(
    e2e_client: TestClient,
    real_service_with_mock_llm: AdviceService,
) -> None:
    """
    真實 AdviceService 串接 4 個 LLM 呼叫 → HTTP 200 + 四段完整結構。
    """
    resp = e2e_client.post(
        "/advise",
        json={
            "answers": {
                "gender": "男",
                "age": 45,
                "current_weight_kg": 95,
                "height_cm": 170,
                "exercise_frequency": "幾乎不運動",
            }
        },
    )

    assert resp.status_code == 200
    body = resp.json()

    # 四段結構
    assert "summary" in body
    assert "recommended_products" in body
    assert "sales_scripts" in body
    assert "next_actions" in body

    # 子欄位驗證
    assert body["summary"]["overall_level"] in ("low", "medium", "high")
    assert len(body["recommended_products"]) >= 1
    assert len(body["sales_scripts"]) >= 2
    assert len(body["next_actions"]) >= 1


# ---------------------------------------------------------------------------
# 測試 2：只傳 {"gender":"男"} → pipeline 仍能產出（fallback 機制）
# ---------------------------------------------------------------------------


def test_post_advise_with_minimal_answers(
    real_service_with_mock_llm: AdviceService,
) -> None:
    """
    只傳最少答案 → pipeline 不應崩潰，應 HTTP 200 且有合理輸出。
    """
    # 每次測試都需要新的 service（避免 warm_up 快取干擾）
    config = AdviceServiceConfig(
        questionnaire_path=_SCHEMAS_DIR / "questionnaire.json",
        products_path=_SCHEMAS_DIR / "products.json",
        rules_path=_SCHEMAS_DIR / "product_rules.json",
    )
    mock_client = make_smart_mock_client()
    service = AdviceService(config=config, client=mock_client)

    app.dependency_overrides[get_advice_service] = lambda: service
    try:
        with TestClient(app) as c:
            resp = c.post("/advise", json={"answers": {"gender": "男"}})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "recommended_products" in body


# ---------------------------------------------------------------------------
# 測試 3：第 3 次 LLM 呼叫（scripts）raise → 整個 endpoint 502
# ---------------------------------------------------------------------------


def test_post_advise_llm_partial_failure() -> None:
    """
    pipeline 中第 3 次 LLM 呼叫（sales_scripts）raise LLMError → HTTP 502。
    """
    from app.core.llm_client import LLMError

    call_count = 0

    async def failing_side(**kwargs: Any) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        system: str = kwargs.get("system", "")
        # product_recommendation 成功
        if "精準推薦產品" in system or "候選清單" in system:
            return _products_response()
        # next_actions 成功
        if "資深營運教練" in system:
            return _actions_response()
        # sales_scripts 失敗
        if "coach-of-coach" in system:
            raise LLMError("simulated scripts LLM failure")
        # health_summary 成功
        return _health_summary_response()

    config = AdviceServiceConfig(
        questionnaire_path=_SCHEMAS_DIR / "questionnaire.json",
        products_path=_SCHEMAS_DIR / "products.json",
        rules_path=_SCHEMAS_DIR / "product_rules.json",
    )
    failing_client = AsyncMock(spec=LLMClient)
    failing_client.complete_json.side_effect = failing_side
    service = AdviceService(config=config, client=failing_client)

    app.dependency_overrides[get_advice_service] = lambda: service
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/advise",
                json={"answers": {"gender": "女", "age": 30}},
            )
    finally:
        app.dependency_overrides.clear()

    # LLMError → advise 路由轉為 502
    assert resp.status_code == 502


# ---------------------------------------------------------------------------
# 測試 4：response JSON 能 round-trip 回 AdviceResponse Pydantic model
# ---------------------------------------------------------------------------


def test_advise_response_shape_matches_pydantic(
    e2e_client: TestClient,
) -> None:
    """
    驗 response JSON 能成功 parse 為 AdviceResponse Pydantic model（round-trip）。
    """
    resp = e2e_client.post(
        "/advise",
        json={
            "answers": {
                "gender": "女",
                "age": 40,
                "sleep_quality": "差",
            }
        },
    )

    assert resp.status_code == 200
    body = resp.json()

    # round-trip 驗證：不應拋 ValidationError
    parsed = AdviceResponse.model_validate(body)
    assert parsed.summary is not None
    assert parsed.recommended_products is not None
    assert len(parsed.sales_scripts) >= 2
    assert len(parsed.next_actions) >= 1
