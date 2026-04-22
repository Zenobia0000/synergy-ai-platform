"""
整合測試：POST /advise 路由。

使用 FastAPI TestClient，mock 整個 AdviceService，
不真實呼叫 LLM，確保路由層邏輯正確。
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_advice_service
from app.api.main import app
from app.core.llm_client import LLMError, LLMJSONError, LLMTimeoutError
from app.schemas import (
    AdviceRequest,
    AdviceResponse,
    HealthAssessmentSummary,
    NextAction,
    RecommendedProduct,
    SalesScript,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ANSWERS: dict[str, str | int | float | bool | list[str] | None] = {
    "gender": "男",
    "age": 45,
    "bmi": 29.0,
    "exercise_frequency": "rarely",
}


@pytest.fixture
def mock_advice_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(mock_advice_service: AsyncMock):
    """每個測試注入 mock service，測試後清除覆寫。"""
    app.dependency_overrides[get_advice_service] = lambda: mock_advice_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_advice_response() -> AdviceResponse:
    return AdviceResponse(
        summary=HealthAssessmentSummary(
            key_risks=["體重偏高", "缺乏運動"],
            overall_level="medium",
            narrative="45 歲男性，BMI 29，缺乏規律運動，建議從飲食控制與基礎產品搭配入手。這是一段超過三十字的說明文字。",
        ),
        recommended_products=[
            RecommendedProduct(
                sku="96371",
                name="PROARGI-9+",
                reason="支持心血管健康且適合代謝族群使用，建議每日補充一份。",
                confidence=0.85,
            ),
        ],
        sales_scripts=[
            SalesScript(
                scenario="opening",
                script="您好，我看到您最近有想改善健康狀況，我們可以一起來評估您目前的健康狀況。",
            ),
            SalesScript(
                scenario="closing",
                script="我們可以先安排一次 30 分鐘的諮詢，幫您規劃具體步驟，您方便本週找個時間嗎？",
            ),
        ],
        next_actions=[
            NextAction(
                action="schedule_consultation",
                why="客戶意願明確且需求清楚，應盡快安排面談。",
                priority="high",
            ),
        ],
    )


# ---------------------------------------------------------------------------
# 1. 正常請求回傳 200
# ---------------------------------------------------------------------------


def test_post_advise_returns_200_with_valid_request(
    client: TestClient,
    mock_advice_service: AsyncMock,
    sample_advice_response: AdviceResponse,
) -> None:
    """mock service.advise 回 sample_advice_response → HTTP 200 + 結構正確"""
    mock_advice_service.advise.return_value = sample_advice_response

    resp = client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    assert resp.status_code == 200
    body = resp.json()
    assert "summary" in body
    assert "recommended_products" in body
    assert "sales_scripts" in body
    assert "next_actions" in body


# ---------------------------------------------------------------------------
# 2. 缺少 answers key → 422
# ---------------------------------------------------------------------------


def test_post_advise_rejects_missing_answers_key(client: TestClient) -> None:
    """body 缺 answers key → FastAPI 自動 422"""
    resp = client.post("/advise", json={"locale": "zh-TW"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 3. locale 非法值 → 422
# ---------------------------------------------------------------------------


def test_post_advise_rejects_invalid_locale(client: TestClient) -> None:
    """locale='fr' 非允許值 → 422"""
    resp = client.post(
        "/advise",
        json={"answers": SAMPLE_ANSWERS, "locale": "fr"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 4. 預設 coach_level = "new"
# ---------------------------------------------------------------------------


def test_post_advise_default_coach_level(
    client: TestClient,
    mock_advice_service: AsyncMock,
    sample_advice_response: AdviceResponse,
) -> None:
    """未傳 coach_level → service 收到 request.coach_level='new'"""
    mock_advice_service.advise.return_value = sample_advice_response

    client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    call_args = mock_advice_service.advise.call_args
    received_request: AdviceRequest = call_args[0][0]
    assert received_request.coach_level == "new"


# ---------------------------------------------------------------------------
# 5. 驗 service 收到正確的 AdviceRequest
# ---------------------------------------------------------------------------


def test_post_advise_passes_request_to_service(
    client: TestClient,
    mock_advice_service: AsyncMock,
    sample_advice_response: AdviceResponse,
) -> None:
    """驗 mock_advice_service.advise 收到正確 AdviceRequest（用 call_args）"""
    mock_advice_service.advise.return_value = sample_advice_response

    resp = client.post(
        "/advise",
        json={"answers": SAMPLE_ANSWERS, "locale": "en", "coach_level": "experienced"},
    )

    assert resp.status_code == 200
    call_args = mock_advice_service.advise.call_args
    received_request: AdviceRequest = call_args[0][0]
    assert received_request.locale == "en"
    assert received_request.coach_level == "experienced"
    assert received_request.answers == SAMPLE_ANSWERS


# ---------------------------------------------------------------------------
# 6. LLMTimeoutError → 504
# ---------------------------------------------------------------------------


def test_post_advise_timeout_returns_504(
    client: TestClient,
    mock_advice_service: AsyncMock,
) -> None:
    """mock service.advise raise LLMTimeoutError → HTTP 504"""
    mock_advice_service.advise.side_effect = LLMTimeoutError("timed out")

    resp = client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    assert resp.status_code == 504
    assert "timeout" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 7. LLMJSONError → 502
# ---------------------------------------------------------------------------


def test_post_advise_json_error_returns_502(
    client: TestClient,
    mock_advice_service: AsyncMock,
) -> None:
    """mock raise LLMJSONError → HTTP 502"""
    mock_advice_service.advise.side_effect = LLMJSONError("bad json")

    resp = client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    assert resp.status_code == 502
    assert "invalid" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 8. 泛型 LLMError → 502
# ---------------------------------------------------------------------------


def test_post_advise_generic_llm_error_returns_502(
    client: TestClient,
    mock_advice_service: AsyncMock,
) -> None:
    """mock raise LLMError → HTTP 502"""
    mock_advice_service.advise.side_effect = LLMError("upstream error")

    resp = client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    assert resp.status_code == 502
    assert "upstream" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 9. 非預期例外 → 500
# ---------------------------------------------------------------------------


def test_post_advise_unexpected_error_returns_500(
    mock_advice_service: AsyncMock,
) -> None:
    """mock raise RuntimeError → HTTP 500（FastAPI default handler）。

    TestClient 預設遇到 server 例外時會重新 raise（raise_server_exceptions=True），
    需改為 raise_server_exceptions=False 才能接到 500 回應。
    """
    mock_advice_service.advise.side_effect = RuntimeError("unexpected")
    app.dependency_overrides[get_advice_service] = lambda: mock_advice_service
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post("/advise", json={"answers": SAMPLE_ANSWERS})
        assert resp.status_code == 500
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 10. 回應含全部四個段落
# ---------------------------------------------------------------------------


def test_post_advise_response_schema_has_all_four_sections(
    client: TestClient,
    mock_advice_service: AsyncMock,
    sample_advice_response: AdviceResponse,
) -> None:
    """驗回 JSON 含 summary / recommended_products / sales_scripts / next_actions"""
    mock_advice_service.advise.return_value = sample_advice_response

    resp = client.post("/advise", json={"answers": SAMPLE_ANSWERS})

    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) >= {"summary", "recommended_products", "sales_scripts", "next_actions"}
    assert isinstance(body["recommended_products"], list)
    assert isinstance(body["sales_scripts"], list)
    assert isinstance(body["next_actions"], list)
    assert isinstance(body["summary"], dict)


# ---------------------------------------------------------------------------
# 11. answers 含多種型別 → 200
# ---------------------------------------------------------------------------


def test_post_advise_accepts_mixed_answer_types(
    client: TestClient,
    mock_advice_service: AsyncMock,
    sample_advice_response: AdviceResponse,
) -> None:
    """answers 含 str / int / list / None 各種型別 → 200"""
    mock_advice_service.advise.return_value = sample_advice_response

    mixed_answers: dict[str, str | int | float | bool | list[str] | None] = {
        "name": "陳小明",
        "age": 35,
        "bmi": 22.5,
        "is_smoker": False,
        "symptoms": ["頭痛", "疲勞"],
        "remarks": None,
    }

    resp = client.post("/advise", json={"answers": mixed_answers})

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 12. CORS preflight OPTIONS → POST 被允許
# ---------------------------------------------------------------------------


def test_cors_allows_post_from_localhost_3000(client: TestClient) -> None:
    """OPTIONS preflight 驗 POST 被允許（CORS middleware）"""
    resp = client.options(
        "/advise",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    # 允許 200 或 204
    assert resp.status_code in (200, 204)
    assert "access-control-allow-origin" in resp.headers
    assert "POST" in resp.headers.get("access-control-allow-methods", "")


# ---------------------------------------------------------------------------
# 13-14. deps.py AdviceService factory 單元測試（提升覆蓋率）
# ---------------------------------------------------------------------------


def test_get_advice_service_returns_advice_service_instance() -> None:
    """get_advice_service() 回傳 AdviceService 實例（mock 所有外部依賴）。"""
    from unittest.mock import MagicMock, patch

    import app.api.deps as deps_module

    mock_config = MagicMock()
    mock_client = MagicMock()
    mock_service = MagicMock()

    with (
        patch.object(deps_module, "get_default_config", return_value=mock_config),
        patch.object(deps_module, "_get_llm_client", return_value=mock_client),
        patch("app.api.deps.AdviceService", return_value=mock_service) as mock_cls,
    ):
        deps_module.get_advice_service.cache_clear()
        result = deps_module.get_advice_service()

    assert result is mock_service
    mock_cls.assert_called_once_with(config=mock_config, client=mock_client)
    deps_module.get_advice_service.cache_clear()


def test_get_llm_client_returns_llm_client_instance() -> None:
    """_get_llm_client() 回傳 LLMClient 實例（mock Settings）。"""
    from unittest.mock import MagicMock, patch

    import app.api.deps as deps_module

    mock_settings = MagicMock()
    mock_client = MagicMock()

    with (
        patch.object(deps_module, "get_settings", return_value=mock_settings),
        patch("app.api.deps.LLMClient", return_value=mock_client) as mock_cls,
    ):
        deps_module._get_llm_client.cache_clear()
        result = deps_module._get_llm_client()

    assert result is mock_client
    mock_cls.assert_called_once_with(settings=mock_settings)
    deps_module._get_llm_client.cache_clear()
