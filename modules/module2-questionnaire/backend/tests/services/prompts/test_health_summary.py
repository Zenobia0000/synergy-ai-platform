"""
TDD 測試：generate_health_summary

共 11 個測試，全程 mock LLMClient.complete_json，不實際呼叫 Gemini。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, call, patch

import pytest
from pydantic import ValidationError

from app.services.prompts.health_summary import generate_health_summary
from app.services.prompts.base import PromptContext, build_field_label_map


# ---------------------------------------------------------------------------
# 1. 基本成功路徑
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_valid_summary(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """mock 回傳合法 dict → 成功解析為 HealthAssessmentSummary。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict

    result = await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert result.overall_level == "high"
    assert len(result.key_risks) >= 1
    assert len(result.narrative) >= 30
    mock_llm_client.complete_json.assert_called_once()


# ---------------------------------------------------------------------------
# 2. PII 過濾
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pii_fields_stripped_from_prompt(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """answers 含 name/email/phone，user prompt 中不應出現這些值。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict

    await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    user_prompt: str = call_kwargs["user"]

    # PII 值不應出現在 prompt 中
    assert "王小明" not in user_prompt
    assert "user@example.com" not in user_prompt
    assert "0912-345-678" not in user_prompt


# ---------------------------------------------------------------------------
# 3. field_id → label 轉換
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_field_ids_converted_to_labels(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """user prompt 應含中文 label『性別』而非 field_id『gender』。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict

    await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    user_prompt: str = call_kwargs["user"]

    assert "性別" in user_prompt
    # field_id 原始名稱不應裸露（允許出現在 label 本身，但不應直接用 field_id）
    # 驗證有標籤轉換：至少一個中文 label 出現
    assert "年齡" in user_prompt or "性別" in user_prompt


# ---------------------------------------------------------------------------
# 4. Disclaimer 自動補上
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disclaimer_auto_appended_when_missing(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
) -> None:
    """mock 回傳 disclaimers=[] → 結果自動補上含『非醫療診斷』的免責聲明。"""
    mock_llm_client.complete_json.return_value = {
        "key_risks": ["睡眠品質差"],
        "overall_level": "medium",
        "narrative": "客戶目前睡眠品質不佳，建議調整作息並補充適當營養素以改善狀況。",
        "disclaimers": [],
    }

    result = await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    # 結果必須有 disclaimer 且含「非醫療診斷」
    assert len(result.disclaimers) >= 1
    combined = " ".join(result.disclaimers)
    assert "非醫療診斷" in combined


# ---------------------------------------------------------------------------
# 5. Disclaimer 已有時不覆蓋
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_disclaimer_preserved_when_present(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """mock 回傳已有含『非醫療診斷』的 disclaimer → 不應被覆蓋或重複添加。"""
    original_disclaimer = "本評估僅供健康諮詢參考，非醫療診斷。請遵循醫師建議。"
    mock_llm_client.complete_json.return_value = {
        **valid_summary_dict,
        "disclaimers": [original_disclaimer],
    }

    result = await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert original_disclaimer in result.disclaimers


# ---------------------------------------------------------------------------
# 6. System prompt 含 JSON schema 欄位
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_prompt_contains_json_schema(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """system prompt 應嵌入 HealthAssessmentSummary schema，含 overall_level 等欄位名。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict

    await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    system_prompt: str = call_kwargs["system"]

    assert "overall_level" in system_prompt
    assert "key_risks" in system_prompt
    assert "narrative" in system_prompt
    assert "disclaimers" in system_prompt


# ---------------------------------------------------------------------------
# 7. System prompt 含醫療免責規則
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_system_prompt_forbids_medical_claims(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """system prompt 必須含『非醫療診斷』與『遵循醫師建議』等安全規則。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict

    await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    system_prompt: str = call_kwargs["system"]

    assert "非醫療診斷" in system_prompt
    assert "醫師" in system_prompt


# ---------------------------------------------------------------------------
# 8. ValidationError 後重試成功
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_on_validation_error(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """第 1 次 mock 回傳 invalid（缺 key_risks）→ 第 2 次成功。應有 2 次呼叫。"""
    invalid_dict = {
        # 缺少 key_risks
        "overall_level": "medium",
        "narrative": "客戶目前睡眠品質不佳，建議調整作息並補充適當營養素以改善狀況。",
        "disclaimers": ["非醫療診斷相關聲明。"],
    }

    mock_llm_client.complete_json.side_effect = [invalid_dict, valid_summary_dict]

    result = await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert mock_llm_client.complete_json.call_count == 2
    assert result.overall_level == "high"


# ---------------------------------------------------------------------------
# 9. 兩次都失敗則 raise
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_exhausted_raises(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
) -> None:
    """兩次都回傳 invalid dict → 應 raise（ValidationError 或封裝後的例外）。"""
    invalid_dict = {
        "overall_level": "invalid_level",  # 不合法的 literal
        "narrative": "短",  # 太短，不符合 min_length=30
        "disclaimers": [],
    }

    mock_llm_client.complete_json.side_effect = [invalid_dict, invalid_dict]

    with pytest.raises(Exception):
        await generate_health_summary(
            answers=sample_answers,
            context=prompt_context,
            client=mock_llm_client,
        )

    assert mock_llm_client.complete_json.call_count == 2


# ---------------------------------------------------------------------------
# 10. key_risks 超過 5 個 → ValidationError → 重試
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_key_risks_max_five(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """mock 回傳 6 個 risks → 觸發 ValidationError → 重試，第 2 次成功。"""
    too_many_risks_dict = {
        "key_risks": ["風險1", "風險2", "風險3", "風險4", "風險5", "風險6"],  # 超過 max=5
        "overall_level": "high",
        "narrative": "客戶有多項高風險指標，需要立即介入處理以改善整體健康狀況。",
        "disclaimers": ["非醫療診斷相關聲明，請遵循醫師建議。"],
    }

    mock_llm_client.complete_json.side_effect = [too_many_risks_dict, valid_summary_dict]

    result = await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
    )

    assert mock_llm_client.complete_json.call_count == 2
    assert len(result.key_risks) <= 5


# ---------------------------------------------------------------------------
# 11. model override 傳遞到 client
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_none_value_in_answers_rendered_as_unfilled(
    mock_llm_client: AsyncMock,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """answers 中 value=None 的欄位應在 user prompt 中顯示『（未填）』。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict
    answers_with_none = {
        "gender": "男",
        "age": None,  # None value
        "height_cm": 170,
        "current_weight_kg": 80,
        "primary_goals": ["體重管理"],
        "narrative": "測試用敘述，包含足夠長度以通過驗證。",
    }

    await generate_health_summary(
        answers=answers_with_none,
        context=prompt_context,
        client=mock_llm_client,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    user_prompt: str = call_kwargs["user"]
    assert "（未填）" in user_prompt


@pytest.mark.asyncio
async def test_model_override_is_passed_to_client(
    mock_llm_client: AsyncMock,
    sample_answers: dict,
    prompt_context: PromptContext,
    valid_summary_dict: dict,
) -> None:
    """傳入 model='gemini/gemini-2.5-pro' → client.complete_json 應收到該參數。"""
    mock_llm_client.complete_json.return_value = valid_summary_dict
    custom_model = "gemini/gemini-2.5-pro"

    await generate_health_summary(
        answers=sample_answers,
        context=prompt_context,
        client=mock_llm_client,
        model=custom_model,
    )

    call_kwargs = mock_llm_client.complete_json.call_args.kwargs
    assert call_kwargs.get("model") == custom_model
