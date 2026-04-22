"""
TDD 測試：generate_sales_scripts（共 12 個測試，全程 mock LLMClient）
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.schemas.advice import HealthAssessmentSummary, RecommendedProduct, SalesScript
from app.services.prompts.base import PromptContext
from app.services.prompts.sales_scripts import generate_sales_scripts

# ---------------------------------------------------------------------------
# 常用 script 字串（>= 20 字，測試共用）
# ---------------------------------------------------------------------------
_S_OPENING = "嗨！最近身體狀況怎麼樣？很多人到了這個年紀都感覺體力不如從前，有空輕鬆聊一下？"
_S_OBJECTION = "我完全理解你的顧慮，很多人一開始也這樣想，其實只是先了解一下身體狀況，不是要你馬上做決定。"
_S_CLOSING = "根據你的狀況，我建議先從基礎調理開始試試一個月，很多人第三週就感覺到變化，你這週哪天方便聊？"
_S_FOLLOW_UP = "嗨！上次聊到你有睡眠不好和體力的問題，我整理了一些資料，純粹分享給你參考看看，完全沒有壓力喔！"
_TABOO = "不要一開口就講產品功效，先關心對方狀況。"


# ---------------------------------------------------------------------------
# Fixtures（本測試檔新增的，不與 conftest.py 重複）
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_health_summary() -> HealthAssessmentSummary:
    return HealthAssessmentSummary(
        key_risks=["體重過重（BMI 32.8）", "三高家族史", "睡眠品質差"],
        overall_level="high",
        narrative=(
            "客戶為 45 歲男性，體重 95kg，BMI 約 32.8，屬肥胖範圍。"
            "家族有高血壓、糖尿病、高血脂三高病史，自身風險偏高。"
            "睡眠品質差且壓力高，代謝狀況需重點關注。"
        ),
        disclaimers=["本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適請優先遵循醫師建議。"],
    )


@pytest.fixture
def sample_recommended_products() -> list[RecommendedProduct]:
    return [
        RecommendedProduct(
            sku="PRD-001",
            name="PROARGI-9+",
            reason="此客戶有明顯的心血管風險，PROARGI-9+ 可支持心臟健康與血液循環",
            image_url=None,
            confidence=0.9,
        ),
        RecommendedProduct(
            sku="PRD-002",
            name="e9 能量飲",
            reason="客戶體力下降，e9 能量飲可提升日常活力",
            image_url=None,
            confidence=0.75,
        ),
    ]


@pytest.fixture
def valid_scripts_dict() -> dict[str, Any]:
    return {
        "scripts": [
            {"scenario": "opening", "script": _S_OPENING, "taboo": _TABOO},
            {"scenario": "objection", "script": _S_OBJECTION, "taboo": _TABOO},
            {"scenario": "closing", "script": _S_CLOSING, "taboo": _TABOO},
            {"scenario": "follow_up", "script": _S_FOLLOW_UP, "taboo": _TABOO},
        ]
    }


# ---------------------------------------------------------------------------
# Helper：側錄 system/user kwargs 同時回傳指定 dict
# ---------------------------------------------------------------------------


def _make_capture(return_value: dict) -> tuple[list[str], list[str], Any]:
    captured_system: list[str] = []
    captured_user: list[str] = []

    async def _side(**kwargs: Any) -> dict:
        captured_system.append(kwargs.get("system", ""))
        captured_user.append(kwargs.get("user", ""))
        return return_value

    return captured_system, captured_user, _side


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_list_of_scripts(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """mock 回傳 4 個合法情境 → 解析為 4 個 SalesScript。"""
    mock_llm_client.complete_json.return_value = valid_scripts_dict
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert len(result) == 4
    assert all(isinstance(s, SalesScript) and len(s.script) >= 20 for s in result)
    mock_llm_client.complete_json.assert_called_once()


@pytest.mark.asyncio
async def test_all_four_scenarios_requested_by_default(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """預設 scenarios → user prompt 包含四個情境名稱。"""
    captured_sys, captured_usr, side = _make_capture(valid_scripts_dict)
    mock_llm_client.complete_json.side_effect = side
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    for scenario in ("opening", "objection", "closing", "follow_up"):
        assert scenario in captured_usr[0]


@pytest.mark.asyncio
async def test_custom_scenarios_honored(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
) -> None:
    """scenarios=('opening',) → user prompt 含 opening，結果只有 1 個。"""
    single = {"scripts": [{"scenario": "opening", "script": _S_OPENING, "taboo": _TABOO}]}
    captured_sys, captured_usr, side = _make_capture(single)
    mock_llm_client.complete_json.side_effect = side
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
        scenarios=("opening",),
    )
    assert "opening" in captured_usr[0]
    assert len(result) == 1
    assert result[0].scenario == "opening"


@pytest.mark.asyncio
async def test_script_min_length_validated(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """第一次回傳 script 太短 → 重試，第二次合法 → 呼叫兩次。"""
    short = {"scripts": [
        {"scenario": "opening", "script": "太短", "taboo": None},
        {"scenario": "objection", "script": "太短", "taboo": None},
    ]}
    call_n = 0

    async def _side(**kwargs: Any) -> dict:
        nonlocal call_n
        call_n += 1
        return short if call_n == 1 else valid_scripts_dict

    mock_llm_client.complete_json.side_effect = _side
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert mock_llm_client.complete_json.call_count == 2
    assert all(len(s.script) >= 20 for s in result)


@pytest.mark.asyncio
async def test_taboo_optional(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
) -> None:
    """taboo=None → SalesScript 合法，結果 taboo 全為 None。"""
    no_taboo = {"scripts": [
        {"scenario": "opening", "script": _S_OPENING, "taboo": None},
        {"scenario": "objection", "script": _S_OBJECTION, "taboo": None},
        {"scenario": "closing", "script": _S_CLOSING, "taboo": None},
        {"scenario": "follow_up", "script": _S_FOLLOW_UP, "taboo": None},
    ]}
    mock_llm_client.complete_json.return_value = no_taboo
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert len(result) == 4
    assert all(s.taboo is None for s in result)


@pytest.mark.asyncio
async def test_system_prompt_forbids_exaggeration(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """system prompt 應包含禁止誇大療效的規則。"""
    captured_sys, captured_usr, side = _make_capture(valid_scripts_dict)
    mock_llm_client.complete_json.side_effect = side
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert "禁止誇大" in captured_sys[0] or "誇大" in captured_sys[0]


@pytest.mark.asyncio
async def test_user_prompt_includes_health_risks(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """user prompt 包含 health_summary.key_risks 中至少一個風險。"""
    captured_sys, captured_usr, side = _make_capture(valid_scripts_dict)
    mock_llm_client.complete_json.side_effect = side
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert any(risk in captured_usr[0] for risk in sample_health_summary.key_risks)


@pytest.mark.asyncio
async def test_user_prompt_includes_product_names(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """user prompt 包含所有推薦產品的 name。"""
    captured_sys, captured_usr, side = _make_capture(valid_scripts_dict)
    mock_llm_client.complete_json.side_effect = side
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    for product in sample_recommended_products:
        assert product.name in captured_usr[0]


@pytest.mark.asyncio
async def test_pii_fields_filtered(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """answers 含 PII 欄位 → user prompt 不包含 PII 值。"""
    captured_sys, captured_usr, side = _make_capture(valid_scripts_dict)
    mock_llm_client.complete_json.side_effect = side
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    user_prompt = captured_usr[0]
    assert "王小明" not in user_prompt
    assert "user@example.com" not in user_prompt
    assert "0912-345-678" not in user_prompt


@pytest.mark.asyncio
async def test_model_override_passed(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """傳 model 參數 → complete_json 收到相同 model 值。"""
    mock_llm_client.complete_json.return_value = valid_scripts_dict
    await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
        model="gemini/gemini-2.5-pro",
    )
    assert mock_llm_client.complete_json.call_args.kwargs.get("model") == "gemini/gemini-2.5-pro"


@pytest.mark.asyncio
async def test_fallback_when_less_than_two_scripts(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
) -> None:
    """mock 持續只回傳 1 個合法 script → fallback 補齊至 >= 2。"""
    one_valid = {"scripts": [{"scenario": "opening", "script": _S_OPENING, "taboo": _TABOO}]}
    mock_llm_client.complete_json.return_value = one_valid
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert len(result) >= 2
    assert all(isinstance(s, SalesScript) and len(s.script) >= 20 for s in result)


@pytest.mark.asyncio
async def test_retry_on_validation_error(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """第一次 script 過短（ValidationError） → 重試一次後成功。"""
    invalid = {"scripts": [
        {"scenario": "opening", "script": "短", "taboo": None},
        {"scenario": "closing", "script": "短", "taboo": None},
    ]}
    call_n = 0

    async def _side(**kwargs: Any) -> dict:
        nonlocal call_n
        call_n += 1
        return invalid if call_n == 1 else valid_scripts_dict

    mock_llm_client.complete_json.side_effect = _side
    result = await generate_sales_scripts(
        answers=sample_answers, health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context, client=mock_llm_client,
    )
    assert mock_llm_client.complete_json.call_count == 2
    assert len(result) >= 2
    assert all(len(s.script) >= 20 for s in result)


# ---------------------------------------------------------------------------
# 補強測試：覆蓋 sales_scripts.py 缺口
# ---------------------------------------------------------------------------


def test_format_answers_none_value(prompt_context: PromptContext) -> None:
    """_format_answers 處理 None 值時應格式化為「（未填）」。"""
    from app.services.prompts.sales_scripts import _format_answers

    answers = {"gender": None, "age": 45}
    result = _format_answers(answers, prompt_context)
    assert "（未填）" in result
    assert "45" in result


def test_parse_scripts_unknown_scenario_ignored() -> None:
    """LLM 回傳未在 scenarios 中的情境 → 被忽略，不拋例外。"""
    from app.services.prompts.sales_scripts import _parse_scripts

    raw = {
        "scripts": [
            {"scenario": "unknown_xyz", "script": _S_OPENING, "taboo": None},
            {"scenario": "opening", "script": _S_OPENING, "taboo": None},
        ]
    }
    result = _parse_scripts(raw, scenarios=("opening", "closing"))
    scenarios_found = [s.scenario for s in result]
    assert "unknown_xyz" not in scenarios_found
    assert "opening" in scenarios_found


def test_apply_fallback_does_not_duplicate_existing_scenario() -> None:
    """_apply_fallback：fallback 情境已存在時不重複加入。"""
    from app.services.prompts.sales_scripts import SalesScript, _apply_fallback

    existing = [
        SalesScript(scenario="opening", script=_S_OPENING, taboo=None),
        SalesScript(scenario="follow_up", script=_S_FOLLOW_UP, taboo=None),
    ]
    result = _apply_fallback(existing)
    # 已有 2 個，不需補
    assert len(result) == 2
    # opening 和 follow_up 不重複
    scenarios = [s.scenario for s in result]
    assert scenarios.count("opening") == 1
    assert scenarios.count("follow_up") == 1


@pytest.mark.asyncio
async def test_single_scenario_does_not_apply_fallback(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
) -> None:
    """scenarios=('opening',) 時 min_required=1，即使只有 1 個 script 也不走 apply_fallback。"""
    single = {"scripts": [{"scenario": "opening", "script": _S_OPENING, "taboo": None}]}
    mock_llm_client.complete_json.return_value = single

    result = await generate_sales_scripts(
        answers=sample_answers,
        health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context,
        client=mock_llm_client,
        scenarios=("opening",),
    )
    # 1 個即滿足 min_required=1，直接回傳
    assert len(result) == 1
    assert result[0].scenario == "opening"


@pytest.mark.asyncio
async def test_single_scenario_all_attempts_fail_returns_last_valid(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
) -> None:
    """
    scenarios=('opening',)（min_required=1），2 次嘗試都回傳空 scripts
    → 走 return last_valid 路徑（L252），回傳空 list。
    """
    empty = {"scripts": []}
    mock_llm_client.complete_json.return_value = empty

    result = await generate_sales_scripts(
        answers=sample_answers,
        health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context,
        client=mock_llm_client,
        scenarios=("opening",),
    )
    # min_required=1，但兩次都沒得到合法 script → last_valid=[]
    assert result == []


@pytest.mark.asyncio
async def test_answers_with_list_value_formatted(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary: HealthAssessmentSummary,
    sample_recommended_products: list[RecommendedProduct],
    valid_scripts_dict: dict,
) -> None:
    """answers 含 list 型別值時，user prompt 中應以「、」連接顯示。"""
    captured_usr: list[str] = []

    async def _side(**kwargs: Any) -> dict:
        captured_usr.append(kwargs.get("user", ""))
        return valid_scripts_dict

    mock_llm_client.complete_json.side_effect = _side
    answers_with_list = dict(sample_answers)
    answers_with_list["primary_goals"] = ["體重管理", "睡眠品質", "心血管"]

    await generate_sales_scripts(
        answers=answers_with_list,
        health_summary=sample_health_summary,
        recommended_products=sample_recommended_products,
        context=prompt_context,
        client=mock_llm_client,
    )
    # list 值應以「、」連接
    assert "體重管理、睡眠品質、心血管" in captured_usr[0]
