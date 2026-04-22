"""
TDD 測試：next_actions.py — 下一步行動 Prompt 工程模組。

測試策略：
- 全程 mock LLMClient，不真實呼叫 Gemini
- 驗證 prompt 內容、解析邏輯、保底機制、過濾機制
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from app.core import LLMClient
from app.schemas import HealthAssessmentSummary, NextAction, RecommendedProduct
from app.services.prompts.base import PromptContext
from app.services.prompts.next_actions import generate_next_actions


# ---------------------------------------------------------------------------
# 共用 Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_health_summary_medium() -> HealthAssessmentSummary:
    """中風險健康摘要，整體 level=medium。"""
    return HealthAssessmentSummary(
        key_risks=["輕微體重過重", "睡眠品質不佳"],
        overall_level="medium",
        narrative=(
            "客戶為 35 歲女性，體重略微偏重，睡眠品質不佳。"
            "整體健康風險為中等，建議搭配適當的營養補充與生活習慣調整。"
            "目前無明顯慢性病史，可進行常規健康諮詢。"
        ),
        disclaimers=["本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適或正在治療中，請優先遵循醫師建議。"],
    )


@pytest.fixture
def sample_health_summary_high() -> HealthAssessmentSummary:
    """高風險健康摘要，整體 level=high，包含慢性病關鍵字。"""
    return HealthAssessmentSummary(
        key_risks=["慢性病風險（高血壓）", "正在服藥（降血壓藥）", "肥胖"],
        overall_level="high",
        narrative=(
            "客戶為 55 歲男性，有高血壓病史且正在服藥，整體健康風險偏高。"
            "體重明顯過重，代謝指標異常，需要資深教練介入評估。"
            "建議轉介專業諮詢，避免一般健康產品直接推薦。"
        ),
        disclaimers=["本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適或正在治療中，請優先遵循醫師建議。"],
    )


@pytest.fixture
def sample_health_summary_low() -> HealthAssessmentSummary:
    """低風險健康摘要，整體 level=low。"""
    return HealthAssessmentSummary(
        key_risks=["偶爾疲勞"],
        overall_level="low",
        narrative=(
            "客戶為 28 歲女性，整體健康狀況良好，偶有疲勞感。"
            "無明顯慢性病史，生活習慣尚可。"
            "整體健康風險低，適合一般健康諮詢。"
        ),
        disclaimers=["本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適或正在治療中，請優先遵循醫師建議。"],
    )


@pytest.fixture
def sample_products() -> list[RecommendedProduct]:
    """兩個推薦產品。"""
    return [
        RecommendedProduct(
            sku="PRD-001",
            name="超級維他命 C",
            reason="此客戶有明顯的免疫力不足症狀，維他命 C 可強化防禦力",
            image_url=None,
            confidence=0.85,
        ),
        RecommendedProduct(
            sku="PRD-002",
            name="優質蛋白質補充品",
            reason="客戶有體重管理需求，蛋白質有助於維持肌肉量並提升代謝",
            image_url=None,
            confidence=0.72,
        ),
    ]


@pytest.fixture
def valid_next_actions_raw() -> dict:
    """合法的 LLM 回傳 dict，含 3 個合法 action。"""
    return {
        "actions": [
            {
                "action": "schedule_consultation",
                "why": "您提到有明確的健康改善目標且預算合理，適合安排 2:1 深度商談",
                "priority": "high",
            },
            {
                "action": "send_educational_content",
                "why": "客戶對產品效果尚有疑慮，先推送相關衛教資料建立信任",
                "priority": "medium",
            },
            {
                "action": "offer_trial",
                "why": "客戶表示想先體驗效果再決定，提供試用品可降低購買門檻",
                "priority": "medium",
            },
        ]
    }


# ---------------------------------------------------------------------------
# 測試 1：基本功能 — 回傳 list[NextAction]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_list_of_next_actions(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """generate_next_actions 應回傳 list[NextAction]，且每項為合法 NextAction。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert isinstance(result, list)
    assert len(result) >= 1
    for item in result:
        assert isinstance(item, NextAction)
        assert item.action in {
            "schedule_consultation",
            "offer_trial",
            "escalate_to_senior",
            "send_educational_content",
            "hold_for_warming",
        }
        assert len(item.why) >= 10


# ---------------------------------------------------------------------------
# 測試 2：max_actions 限制 — mock 回 3 個，max_actions=2 → 取前 2
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_max_actions_respected(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """當 mock 回傳 3 個 action 但 max_actions=2，應只取前 2 個。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
        max_actions=2,
    )

    assert len(result) <= 2


# ---------------------------------------------------------------------------
# 測試 3：非法 action 被過濾 + warning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_action_filtered_out(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    caplog: pytest.LogCaptureFixture,
):
    """mock 回傳包含非列舉 action，應被過濾並記錄 warning。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [
            {
                "action": "send_discount_coupon",  # 非法 action
                "why": "這是非法的 action，不應出現",
                "priority": "high",
            },
            {
                "action": "schedule_consultation",
                "why": "客戶有明確需求且預算充足，適合安排正式商談",
                "priority": "high",
            },
        ]
    }

    with caplog.at_level(logging.WARNING, logger="app.services.prompts.next_actions"):
        result = await generate_next_actions(
            answers=sample_answers,
            health_summary=sample_health_summary_medium,
            recommended_products=sample_products,
            context=prompt_context,
            client=mock_llm_client,
        )

    # 非法 action 被過濾
    actions_in_result = [item.action for item in result]
    assert "send_discount_coupon" not in actions_in_result
    assert "schedule_consultation" in actions_in_result
    # 有 warning log
    assert any("send_discount_coupon" in r.message or "invalid" in r.message.lower() for r in caplog.records)


# ---------------------------------------------------------------------------
# 測試 4：全部 action 非法 → fallback 產出 1 個合法 action
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_when_all_actions_invalid(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
):
    """所有 action 均非法時，應 fallback 產出 1 個合法的 NextAction。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [
            {"action": "add_friend_on_line", "why": "非法行動", "priority": "high"},
            {"action": "send_discount", "why": "另一個非法", "priority": "low"},
        ]
    }

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert len(result) == 1
    assert result[0].action in {
        "schedule_consultation",
        "offer_trial",
        "escalate_to_senior",
        "send_educational_content",
        "hold_for_warming",
    }


# ---------------------------------------------------------------------------
# 測試 5：高風險 fallback → 必須是 escalate_to_senior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_for_high_risk_triggers_escalate(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_high: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
):
    """health_summary.overall_level='high' 且所有 action 非法 → fallback 為 escalate_to_senior。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [
            {"action": "send_gift", "why": "非法行動", "priority": "high"},
        ]
    }

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_high,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert len(result) == 1
    assert result[0].action == "escalate_to_senior"
    assert result[0].priority == "high"


# ---------------------------------------------------------------------------
# 測試 6：system prompt 包含 5 種 action
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_prompt_contains_all_five_actions(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """system prompt 必須包含 5 種 action 的名稱與定義。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    system_prompt: str = call_kwargs.kwargs.get("system") or call_kwargs.args[0]

    five_actions = [
        "schedule_consultation",
        "offer_trial",
        "escalate_to_senior",
        "send_educational_content",
        "hold_for_warming",
    ]
    for action in five_actions:
        assert action in system_prompt, f"system prompt 缺少 action: {action}"


# ---------------------------------------------------------------------------
# 測試 7：system prompt 包含醫療 escalation 指引
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_prompt_flags_medical_escalation(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """system prompt 應包含慢性病/正在服藥等醫療 escalation 指引語句。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    system_prompt: str = call_kwargs.kwargs.get("system") or call_kwargs.args[0]

    # 應包含醫療風險關鍵字，指引 escalate_to_senior
    medical_keywords = ["慢性病", "正在服藥", "escalate_to_senior"]
    found = [kw for kw in medical_keywords if kw in system_prompt]
    assert len(found) >= 2, (
        f"system prompt 應包含醫療 escalation 指引，但只找到：{found}\n"
        f"缺少：{[kw for kw in medical_keywords if kw not in system_prompt]}"
    )


# ---------------------------------------------------------------------------
# 測試 8：user prompt 包含 health_summary risks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_prompt_includes_health_summary_risks(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """user prompt 應包含 health_summary 的 key_risks 資訊。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    user_prompt: str = call_kwargs.kwargs.get("user") or call_kwargs.args[1]

    # key_risks 中的關鍵詞應出現在 user prompt
    for risk in sample_health_summary_medium.key_risks:
        assert risk in user_prompt, f"user prompt 缺少風險：{risk}"


# ---------------------------------------------------------------------------
# 測試 9：user prompt 包含推薦產品名稱
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_prompt_includes_product_names(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """user prompt 應包含推薦產品的名稱。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    user_prompt: str = call_kwargs.kwargs.get("user") or call_kwargs.args[1]

    for product in sample_products:
        assert product.name in user_prompt, f"user prompt 缺少產品名稱：{product.name}"


# ---------------------------------------------------------------------------
# 測試 10：PII 欄位被過濾
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pii_filtered(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """user prompt 中不應包含 PII 欄位（name, email, phone）的值。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    user_prompt: str = call_kwargs.kwargs.get("user") or call_kwargs.args[1]

    # PII 的值不應出現在 prompt
    pii_values = ["王小明", "user@example.com", "0912-345-678"]
    for pii in pii_values:
        assert pii not in user_prompt, f"user prompt 含有 PII 資訊：{pii}"


# ---------------------------------------------------------------------------
# 測試 11：priority 缺失時預設 medium
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_priority_default_medium(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
):
    """mock 回傳 action 無 priority 欄位時，解析後 priority 應為 'medium'。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [
            {
                "action": "send_educational_content",
                "why": "客戶目前在資訊蒐集階段，需要更多衛教資料建立信任基礎",
                # 故意不加 priority
            }
        ]
    }

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert len(result) == 1
    assert result[0].priority == "medium"


# ---------------------------------------------------------------------------
# 測試 12：model 覆蓋正確傳入 LLMClient
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_override_passed(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """指定 model 時，應將 model 正確傳給 LLMClient.complete_json。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw
    custom_model = "gemini/gemini-2.5-pro"

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
        model=custom_model,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    passed_model = call_kwargs.kwargs.get("model")
    assert passed_model == custom_model


# ---------------------------------------------------------------------------
# 測試 13：問卷答案含 None 值 → 顯示（未填）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_none_answer_shown_as_unfilled(
    mock_llm_client: AsyncMock,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    valid_next_actions_raw: dict,
):
    """問卷答案含 None 時，user prompt 應顯示『（未填）』。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw
    answers_with_none = {
        "gender": "女",
        "age": None,  # 故意 None
        "primary_goals": ["體重管理"],
    }

    await generate_next_actions(
        answers=answers_with_none,
        health_summary=sample_health_summary_medium,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    user_prompt: str = call_kwargs.kwargs.get("user") or call_kwargs.args[1]
    assert "（未填）" in user_prompt


# ---------------------------------------------------------------------------
# 測試 14：空產品列表 → user prompt 顯示無推薦產品
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_products_handled(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    valid_next_actions_raw: dict,
):
    """推薦產品列表為空時，user prompt 應顯示無推薦產品提示。"""
    mock_llm_client.complete_json.return_value = valid_next_actions_raw

    await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_medium,
        recommended_products=[],  # 空列表
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args
    user_prompt: str = call_kwargs.kwargs.get("user") or call_kwargs.args[1]
    assert "無推薦產品" in user_prompt


# ---------------------------------------------------------------------------
# 測試 15：LLM 回傳 actions 非列表 → fallback
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_when_actions_not_a_list(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_low: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
):
    """LLM 回傳 actions 欄位非列表時，應使用 fallback。"""
    mock_llm_client.complete_json.return_value = {
        "actions": "這不是一個列表"  # 非法結構
    }

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_low,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert len(result) == 1
    # overall_level=low → send_educational_content
    assert result[0].action == "send_educational_content"


# ---------------------------------------------------------------------------
# 測試 16：低風險 fallback → send_educational_content
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fallback_for_low_risk(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_low: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
):
    """overall_level='low' 且所有 action 無效時，fallback 應為 send_educational_content。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [{"action": "illegal_action", "why": "非法行動", "priority": "low"}]
    }

    result = await generate_next_actions(
        answers=sample_answers,
        health_summary=sample_health_summary_low,
        recommended_products=sample_products,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert len(result) == 1
    assert result[0].action == "send_educational_content"
    assert result[0].priority == "medium"


# ---------------------------------------------------------------------------
# 測試 17：NextAction 解析失敗（why 字數不足）→ 被跳過並記 warning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_action_with_invalid_why_skipped(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    sample_health_summary_medium: HealthAssessmentSummary,
    sample_products: list[RecommendedProduct],
    caplog: pytest.LogCaptureFixture,
):
    """why 欄位不足 10 字的 action 應被跳過，並記錄 warning。"""
    mock_llm_client.complete_json.return_value = {
        "actions": [
            {
                "action": "offer_trial",
                "why": "短",  # min_length=10，這會觸發 ValidationError
                "priority": "medium",
            },
            {
                "action": "schedule_consultation",
                "why": "客戶有明確需求且預算充足，適合安排正式商談",
                "priority": "high",
            },
        ]
    }

    with caplog.at_level(logging.WARNING, logger="app.services.prompts.next_actions"):
        result = await generate_next_actions(
            answers=sample_answers,
            health_summary=sample_health_summary_medium,
            recommended_products=sample_products,
            context=prompt_context,
            client=mock_llm_client,
        )

    # why 不足的 action 被跳過
    actions_in_result = [item.action for item in result]
    assert "offer_trial" not in actions_in_result
    assert "schedule_consultation" in actions_in_result
    # 有 warning log
    assert any("解析失敗" in r.message or "validation" in r.message.lower() for r in caplog.records)
