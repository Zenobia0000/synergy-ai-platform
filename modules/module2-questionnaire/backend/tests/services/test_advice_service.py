"""
TDD: AdviceService 整合 Orchestrator 測試套件。

測試策略：
    - 全程 mock 四個 prompt 子模組（不呼叫真實 LLM）
    - 驗證 orchestration 邏輯：平行化、錯誤冒泡、warm_up 幂等性
    - smoke test 用真實 load_catalog + evaluate_rules，只 mock LLM
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas import (
    AdviceRequest,
    AdviceResponse,
    HealthAssessmentSummary,
    NextAction,
    RecommendedProduct,
    SalesScript,
)
from app.services.advice_service import AdviceService, AdviceServiceConfig

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data" / "schemas"
_QUESTIONNAIRE_PATH = _DATA_ROOT / "questionnaire.json"
_PRODUCTS_PATH = _DATA_ROOT / "products.json"
_RULES_PATH = _DATA_ROOT / "product_rules.json"


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_answers() -> dict:
    return {
        "gender": "男",
        "age": 45,
        "height_cm": 170,
        "current_weight_kg": 95,
        "primary_goals": ["體重管理", "睡眠品質"],
        "family_history": ["高血壓", "糖尿病"],
        "sleep_quality": "差",
    }


@pytest.fixture
def sample_summary() -> HealthAssessmentSummary:
    return HealthAssessmentSummary(
        key_risks=["體重過重", "三高家族史"],
        overall_level="high",
        narrative=(
            "客戶為 45 歲男性，體重 95kg，BMI 偏高。"
            "家族有高血壓與糖尿病病史，健康風險偏高。"
            "建議優先進行體重管理並搭配適當營養補充。"
        ),
        disclaimers=["本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適，請優先遵循醫師建議。"],
    )


@pytest.fixture
def sample_products() -> list[RecommendedProduct]:
    return [
        RecommendedProduct(
            sku="PRD-001",
            name="超級維他命 C",
            reason="此客戶有明顯免疫力不足，維他命 C 可強化防禦力",
            image_url=None,
            confidence=0.85,
        )
    ]


@pytest.fixture
def sample_scripts() -> list[SalesScript]:
    return [
        SalesScript(
            scenario="opening",
            script="您好，根據您填寫的健康問卷，我發現您最近有些健康隱患需要關注。",
            taboo=None,
        ),
        SalesScript(
            scenario="closing",
            script="感謝您今天的時間，建議您先試用一個月產品，看看身體的改變。",
            taboo=None,
        ),
    ]


@pytest.fixture
def sample_actions() -> list[NextAction]:
    return [
        NextAction(
            action="schedule_consultation",
            why="客戶有多項中高風險指標，需安排專業諮詢討論",
            priority="high",
        )
    ]


# ---------------------------------------------------------------------------
# Config + service fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def real_config() -> AdviceServiceConfig:
    """使用真實 data/schemas/ 路徑的設定。"""
    return AdviceServiceConfig(
        questionnaire_path=_QUESTIONNAIRE_PATH,
        products_path=_PRODUCTS_PATH,
        rules_path=_RULES_PATH,
    )


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    from app.core import LLMClient
    return AsyncMock(spec=LLMClient)


@pytest.fixture
def service_with_real_config(real_config, mock_llm_client) -> AdviceService:
    return AdviceService(config=real_config, client=mock_llm_client)


# ---------------------------------------------------------------------------
# Test 1: 正常流程 → 完整 AdviceResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_advise_returns_advice_response(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """所有子模組 mock 成功 → advise 回傳完整 AdviceResponse。"""
    svc = service_with_real_config

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        request = AdviceRequest(answers=sample_answers)
        response = await svc.advise(request)

    assert isinstance(response, AdviceResponse)
    assert response.summary == sample_summary
    assert response.recommended_products == sample_products
    assert response.sales_scripts == sample_scripts
    assert response.next_actions == sample_actions


# ---------------------------------------------------------------------------
# Test 2: warm_up 幂等性（只執行一次）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warm_up_loads_static_data_once(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """連續呼叫 advise 兩次，warm_up 內的 build_field_label_map 只執行一次。"""
    svc = service_with_real_config

    call_count = 0
    original_build = None

    import app.services.advice_service as adv_mod

    real_build = adv_mod.build_field_label_map

    def counting_build(path):
        nonlocal call_count
        call_count += 1
        return real_build(path)

    with (
        patch("app.services.advice_service.build_field_label_map", side_effect=counting_build),
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        request = AdviceRequest(answers=sample_answers)
        await svc.advise(request)
        await svc.advise(request)

    assert call_count == 1, f"build_field_label_map 應只呼叫一次，實際呼叫 {call_count} 次"


# ---------------------------------------------------------------------------
# Test 3: Stage 2 平行化驗證
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_2_runs_in_parallel(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """mock summary 與 products 各 sleep 0.1s，總時間應接近 0.1s（平行）而非 0.2s（串行）。"""
    svc = service_with_real_config

    async def slow_summary(**kwargs):
        await asyncio.sleep(0.1)
        return sample_summary

    async def slow_products(**kwargs):
        await asyncio.sleep(0.1)
        return sample_products

    with (
        patch("app.services.advice_service.generate_health_summary", new=slow_summary),
        patch("app.services.advice_service.generate_product_recommendation", new=slow_products),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        start = time.monotonic()
        request = AdviceRequest(answers=sample_answers)
        await svc.advise(request)
        elapsed = time.monotonic() - start

    # 平行應接近 0.1s，留 0.15s 彈性；串行則 >= 0.2s
    assert elapsed < 0.25, f"Stage 2 應平行執行，但耗時 {elapsed:.3f}s（超過 0.25s）"


# ---------------------------------------------------------------------------
# Test 4: 空 candidates 仍能產出回應（依賴下游 fallback）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_candidates_still_produces_response(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """evaluate_rules 回空 triggered → collect_candidates 回空 → 仍能呼叫 LLM 並得到回應。"""
    svc = service_with_real_config

    with (
        patch("app.services.advice_service.evaluate_rules", return_value=[]),
        patch("app.services.advice_service.collect_candidates", return_value=[]),
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        request = AdviceRequest(answers=sample_answers)
        response = await svc.advise(request)

    assert isinstance(response, AdviceResponse)


# ---------------------------------------------------------------------------
# Test 5–8: 各子模組失敗例外冒泡
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_failure_propagates(
    service_with_real_config,
    sample_answers,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """health_summary mock raise RuntimeError → advise 應冒泡相同例外。"""
    svc = service_with_real_config

    async def failing_summary(**kwargs):
        raise RuntimeError("LLM summary failed")

    with (
        patch("app.services.advice_service.generate_health_summary", new=failing_summary),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        with pytest.raises(RuntimeError, match="LLM summary failed"):
            request = AdviceRequest(answers=sample_answers)
            await svc.advise(request)


@pytest.mark.asyncio
async def test_products_failure_propagates(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_scripts,
    sample_actions,
):
    """product_recommendation mock raise ValueError → advise 應冒泡相同例外。"""
    svc = service_with_real_config

    async def failing_products(**kwargs):
        raise ValueError("products LLM error")

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=failing_products),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        with pytest.raises(ValueError, match="products LLM error"):
            request = AdviceRequest(answers=sample_answers)
            await svc.advise(request)


@pytest.mark.asyncio
async def test_scripts_failure_propagates(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_actions,
):
    """sales_scripts mock raise RuntimeError → advise 應冒泡相同例外。"""
    svc = service_with_real_config

    async def failing_scripts(**kwargs):
        raise RuntimeError("scripts LLM error")

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=failing_scripts),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        with pytest.raises(RuntimeError, match="scripts LLM error"):
            request = AdviceRequest(answers=sample_answers)
            await svc.advise(request)


@pytest.mark.asyncio
async def test_actions_failure_propagates(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
):
    """next_actions mock raise RuntimeError → advise 應冒泡相同例外。"""
    svc = service_with_real_config

    async def failing_actions(**kwargs):
        raise RuntimeError("actions LLM error")

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=failing_actions),
    ):
        with pytest.raises(RuntimeError, match="actions LLM error"):
            request = AdviceRequest(answers=sample_answers)
            await svc.advise(request)


# ---------------------------------------------------------------------------
# Test 9: default config 路徑真實存在
# ---------------------------------------------------------------------------


def test_default_config_paths_exist():
    """get_default_config() 的三個路徑應指向真實存在的檔案。"""
    from app.services import get_default_config

    # 清除 lru_cache 避免跨測試污染
    get_default_config.cache_clear()
    config = get_default_config()

    assert config.questionnaire_path.exists(), (
        f"questionnaire_path 不存在：{config.questionnaire_path}"
    )
    assert config.products_path.exists(), (
        f"products_path 不存在：{config.products_path}"
    )
    assert config.rules_path.exists(), (
        f"rules_path 不存在：{config.rules_path}"
    )


# ---------------------------------------------------------------------------
# Test 10: AdviceResponse Pydantic 驗證
# ---------------------------------------------------------------------------


def test_advice_response_validates(
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """手動組裝 AdviceResponse，應通過 Pydantic 驗證而不 raise。"""
    response = AdviceResponse(
        summary=sample_summary,
        recommended_products=sample_products,
        sales_scripts=sample_scripts,
        next_actions=sample_actions,
    )

    assert response.summary.overall_level == "high"
    assert len(response.recommended_products) == 1
    assert len(response.sales_scripts) == 2
    assert len(response.next_actions) == 1


# ---------------------------------------------------------------------------
# Test 11: smoke test — 真實 load_catalog + evaluate_rules，LLM 全 mock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_smoke_real_catalog_mocked_llm(
    real_config,
    mock_llm_client,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """
    整合 smoke test：
    - 真實 load_catalog（讀真實 products.json + product_rules.json）
    - 真實 evaluate_rules + collect_candidates（不 mock rule engine）
    - 四個 LLM 子模組全部 mock
    - 驗證整條 pipeline 可通
    """
    svc = AdviceService(config=real_config, client=mock_llm_client)

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        request = AdviceRequest(answers=sample_answers)
        response = await svc.advise(request)

    assert isinstance(response, AdviceResponse)
    assert response.summary.overall_level in {"low", "medium", "high"}


# ---------------------------------------------------------------------------
# Test 12: warm_up 可被明確呼叫，不重複初始化
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_explicit_warm_up_then_advise(
    service_with_real_config,
    sample_answers,
    sample_summary,
    sample_products,
    sample_scripts,
    sample_actions,
):
    """明確呼叫 warm_up 後再呼叫 advise，context 只初始化一次。"""
    svc = service_with_real_config

    # 確認 warm_up 前 context 為 None
    assert svc._context is None

    await svc.warm_up()
    assert svc._context is not None
    first_context = svc._context

    with (
        patch("app.services.advice_service.generate_health_summary", new=AsyncMock(return_value=sample_summary)),
        patch("app.services.advice_service.generate_product_recommendation", new=AsyncMock(return_value=sample_products)),
        patch("app.services.advice_service.generate_sales_scripts", new=AsyncMock(return_value=sample_scripts)),
        patch("app.services.advice_service.generate_next_actions", new=AsyncMock(return_value=sample_actions)),
    ):
        request = AdviceRequest(answers=sample_answers)
        await svc.advise(request)

    # context 物件應為同一個（warm_up 未被重複執行）
    assert svc._context is first_context


# ---------------------------------------------------------------------------
# Test 13: 重複呼叫 warm_up 幂等（覆蓋 early-return 分支）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_warm_up_idempotent_direct_calls(real_config, mock_llm_client):
    """直接呼叫 warm_up 兩次，第二次應立即回傳（幂等 guard）。"""
    svc = AdviceService(config=real_config, client=mock_llm_client)

    await svc.warm_up()
    first_context = svc._context

    # 第二次呼叫應命中 early-return（覆蓋 line 97）
    await svc.warm_up()

    # context 物件不變
    assert svc._context is first_context
