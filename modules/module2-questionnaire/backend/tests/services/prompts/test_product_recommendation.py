"""
TDD 測試：product_recommendation.py

全程 mock LLMClient，不進行真實 API 呼叫。

執行：
    (cd backend && uv run pytest tests/services/prompts/test_product_recommendation.py -v)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core import LLMClient
from app.services.prompts.base import PromptContext, build_field_label_map
from app.services.prompts.rule_engine import CandidateProduct

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "schemas"
_QUESTIONNAIRE_PATH = _DATA_DIR / "questionnaire.json"
_PRODUCTS_PATH = _DATA_DIR / "products.json"

# ---------------------------------------------------------------------------
# 延遲匯入
# ---------------------------------------------------------------------------

from app.services.prompts.product_recommendation import generate_product_recommendation


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mock_client() -> AsyncMock:
    """Mock LLMClient，spec 符合真實 API。"""
    return AsyncMock(spec=LLMClient)


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
def sample_answers() -> dict[str, Any]:
    """典型問卷答案（含 PII 欄位供過濾測試）。"""
    return {
        "name": "王小明",
        "email": "user@example.com",
        "phone": "0912-345-678",
        "gender": "男",
        "age": 45,
        "height_cm": 170,
        "current_weight_kg": 95,
        "primary_goals": ["體重管理", "睡眠品質"],
        "stress_level": "高",
        "sleep_quality": "差",
    }


@pytest.fixture
def candidate_a() -> CandidateProduct:
    return CandidateProduct(
        sku="23711",
        name="倍然膠囊 (DOUBLE BURN)",
        category="體重管理",
        scenario=("體重管理",),
        price=2800,
        image_url=None,
        rule_hits=("rule_031_0",),
        hit_count=1,
    )


@pytest.fixture
def candidate_b() -> CandidateProduct:
    return CandidateProduct(
        sku="74915",
        name="全植舒眠優蛋白 (GA NIGHT VEGAN PROTEIN)",
        category="睡眠/體重管理",
        scenario=("睡眠品質差",),
        price=3200,
        image_url="https://example.com/74915.png",
        rule_hits=("rule_012_1", "rule_055_1"),
        hit_count=2,
    )


@pytest.fixture
def candidate_c() -> CandidateProduct:
    return CandidateProduct(
        sku="23209",
        name="果然鎂膠囊 (B-PRIME)",
        category="壓力/睡眠",
        scenario=("壓力大", "睡眠差"),
        price=1500,
        image_url=None,
        rule_hits=("rule_015_0",),
        hit_count=1,
    )


# ===========================================================================
# 1. 基本功能：回傳 RecommendedProduct 列表
# ===========================================================================


@pytest.mark.asyncio
async def test_returns_recommended_products(
    mock_client, prompt_context, sample_answers, candidate_a, candidate_b
):
    """mock 回傳 2 個 sku → 成功組 RecommendedProduct。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可加速代謝幫助控制體重。", "confidence": 0.85},
            {"sku": "74915", "reason": "因您睡眠品質差，此產品含有助眠成分可改善睡眠質量。", "confidence": 0.78},
        ]
    }

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a, candidate_b],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    assert len(result) == 2
    skus = [p.sku for p in result]
    assert "23711" in skus
    assert "74915" in skus

    # 檢查 RecommendedProduct 欄位
    for product in result:
        assert product.sku
        assert product.name
        assert len(product.reason) >= 10
        assert 0.0 <= product.confidence <= 1.0


# ===========================================================================
# 2. LLM 幻覺過濾：不在 candidates 的 SKU 被丟棄
# ===========================================================================


@pytest.mark.asyncio
async def test_invalid_sku_from_llm_filtered_out(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """mock 回傳包含不在 candidates 的 sku → 被過濾 + fallback 確保至少 1 個。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "FAKE-SKU-999", "reason": "這是幻覺產品，不應出現在結果中。", "confidence": 0.9},
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可加速代謝。", "confidence": 0.75},
        ]
    }

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    skus = [p.sku for p in result]
    assert "FAKE-SKU-999" not in skus
    assert "23711" in skus
    assert len(result) >= 1


# ===========================================================================
# 3. 空 candidates → fallback
# ===========================================================================


@pytest.mark.asyncio
async def test_empty_candidates_returns_fallback(
    mock_client, prompt_context, sample_answers
):
    """candidates=[] 時，不呼叫 LLM，直接回傳 fallback 產品（從 products.json 取第一個）。"""
    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    # fallback 時不應呼叫 LLM（或 LLM 呼叫被 system prompt 引導回傳空，但實作走 fallback 路徑）
    assert len(result) >= 1
    # fallback 的 reason 應明示這是通用建議
    assert result[0].reason  # 有理由
    # confidence 應較低（fallback 通用建議）
    assert result[0].confidence <= 0.5


# ===========================================================================
# 4. User prompt 含候選產品 SKU
# ===========================================================================


@pytest.mark.asyncio
async def test_user_prompt_contains_candidates(
    mock_client, prompt_context, sample_answers, candidate_a, candidate_b
):
    """mock.call_args 驗 user prompt 包含候選產品的 SKU。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可有效幫助管理體重。", "confidence": 0.8},
        ]
    }

    await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a, candidate_b],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    assert mock_client.complete_json.called
    call_kwargs = mock_client.complete_json.call_args.kwargs
    user_prompt = call_kwargs.get("user", "")

    # user prompt 應包含候選 SKU
    assert "23711" in user_prompt
    assert "74915" in user_prompt


# ===========================================================================
# 5. PII 欄位被過濾（user prompt 不含 PII）
# ===========================================================================


@pytest.mark.asyncio
async def test_pii_fields_stripped(
    mock_client, prompt_context, candidate_a
):
    """user prompt 不應包含 PII 欄位（name, email, phone）。"""
    answers_with_pii = {
        "name": "張三",
        "email": "zhang@example.com",
        "phone": "0912-111-222",
        "gender": "男",
        "age": 30,
    }

    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品有助達成目標。", "confidence": 0.7},
        ]
    }

    await generate_product_recommendation(
        answers=answers_with_pii,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    call_kwargs = mock_client.complete_json.call_args.kwargs
    user_prompt = call_kwargs.get("user", "")

    assert "zhang@example.com" not in user_prompt
    assert "0912-111-222" not in user_prompt
    # 名字可能在 prompt 中顯示，但 email/phone 不行


# ===========================================================================
# 6. max_products 限制
# ===========================================================================


@pytest.mark.asyncio
async def test_max_products_respected(
    mock_client, prompt_context, sample_answers, candidate_a, candidate_b, candidate_c
):
    """mock 回傳 3 個、max_products=2 → 取前 2 個。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，倍然膠囊可加速代謝效果顯著。", "confidence": 0.9},
            {"sku": "74915", "reason": "因您睡眠品質差，全植舒眠優蛋白可改善睡眠。", "confidence": 0.85},
            {"sku": "23209", "reason": "因您壓力較高，果然鎂可緩解壓力並改善神經功能。", "confidence": 0.7},
        ]
    }

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a, candidate_b, candidate_c],
        context=prompt_context,
        client=mock_client,
        max_products=2,
    )

    assert len(result) <= 2


# ===========================================================================
# 7. System prompt 明確禁止自創產品
# ===========================================================================


@pytest.mark.asyncio
async def test_system_prompt_forbids_invented_products(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """system prompt 應包含「只能從候選清單」的限制說明。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可協助達成目標。", "confidence": 0.8},
        ]
    }

    await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    call_kwargs = mock_client.complete_json.call_args.kwargs
    system_prompt = call_kwargs.get("system", "")

    # system prompt 必須包含限制用語
    assert "候選清單" in system_prompt or "候選" in system_prompt


# ===========================================================================
# 8. confidence 超出範圍時的處理
# ===========================================================================


@pytest.mark.asyncio
async def test_confidence_clamped_to_0_1(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """mock 回傳 confidence=1.5 時，應被 clamp 到 [0,1] 或過濾該項目。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品效果極佳值得推薦。", "confidence": 1.5},
        ]
    }

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    # 若產品還在結果中，confidence 必須在合法範圍
    for product in result:
        if product.sku == "23711":
            assert 0.0 <= product.confidence <= 1.0


# ===========================================================================
# 9. LLM 回傳空 products list 時走 fallback
# ===========================================================================


@pytest.mark.asyncio
async def test_empty_llm_response_triggers_fallback(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """LLM 回傳 {'products': []} 時，應 fallback 取 candidates 前 1 個。"""
    mock_client.complete_json.return_value = {"products": []}

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    assert len(result) >= 1
    assert result[0].sku == "23711"


# ===========================================================================
# 10. temperature 傳遞正確
# ===========================================================================


@pytest.mark.asyncio
async def test_llm_called_with_correct_temperature(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """LLM 應以 temperature=0.4 呼叫。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品適合您的目標。", "confidence": 0.8},
        ]
    }

    await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    call_kwargs = mock_client.complete_json.call_args.kwargs
    assert call_kwargs.get("temperature") == pytest.approx(0.4)


# ===========================================================================
# 11. LLM 回傳 products 不是 list 時走 fallback
# ===========================================================================


@pytest.mark.asyncio
async def test_llm_products_not_list_triggers_fallback(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """LLM 回傳 products 為非 list 時，應走 fallback。"""
    mock_client.complete_json.return_value = {"products": "invalid_string"}

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    # fallback 應回傳 candidates 前 1 個
    assert len(result) >= 1
    assert result[0].sku == "23711"


# ===========================================================================
# 12. answers 含 None/empty 值時 user prompt 仍正常生成
# ===========================================================================


@pytest.mark.asyncio
async def test_answers_with_none_values(
    mock_client, prompt_context, candidate_a
):
    """answers 含 None、空字串、空 list 的欄位不應出現在 prompt 中。"""
    answers_with_none = {
        "gender": "男",
        "age": None,
        "email": "",
        "primary_goals": [],
    }

    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可加速代謝效果。", "confidence": 0.8},
        ]
    }

    await generate_product_recommendation(
        answers=answers_with_none,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    call_kwargs = mock_client.complete_json.call_args.kwargs
    user_prompt = call_kwargs.get("user", "")
    # None 值欄位不應出現在 prompt
    assert "None" not in user_prompt
    assert "age" not in user_prompt or "None" not in user_prompt


# ===========================================================================
# 13. confidence 為非數值時的處理
# ===========================================================================


@pytest.mark.asyncio
async def test_confidence_non_numeric_handled(
    mock_client, prompt_context, sample_answers, candidate_a
):
    """mock 回傳 confidence 為字串 'N/A' 時，應被視為 0.5 預設值。"""
    mock_client.complete_json.return_value = {
        "products": [
            {"sku": "23711", "reason": "因您有體重管理需求，此產品可有效幫助達成目標。", "confidence": "N/A"},
        ]
    }

    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[candidate_a],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    # 有產品結果，且 confidence 在合法範圍
    assert len(result) >= 1
    for product in result:
        assert 0.0 <= product.confidence <= 1.0


# ===========================================================================
# 14. 候選清單空、products.json fallback 的 reason 文字
# ===========================================================================


@pytest.mark.asyncio
async def test_empty_candidates_fallback_has_general_reason(
    mock_client, prompt_context, sample_answers
):
    """空 candidates 時的 fallback reason 應明示「通用建議」。"""
    result = await generate_product_recommendation(
        answers=sample_answers,
        candidates=[],
        context=prompt_context,
        client=mock_client,
        max_products=3,
    )

    assert len(result) >= 1
    assert "通用建議" in result[0].reason or "通用" in result[0].reason


# ===========================================================================
# 15. _format_candidates_section — 空 candidates 路徑
# ===========================================================================


def test_format_candidates_section_empty() -> None:
    """_format_candidates_section([]) 應回傳「（無候選產品）」字串。"""
    from app.services.prompts.product_recommendation import _format_candidates_section

    result = _format_candidates_section([])
    assert "無候選產品" in result


def test_format_candidates_section_with_no_scenario(candidate_a) -> None:
    """候選產品 scenario 為空 tuple 時，格式化應顯示「無」。"""
    from app.services.prompts.product_recommendation import (
        CandidateProduct,
        _format_candidates_section,
    )

    no_scenario = CandidateProduct(
        sku="00001",
        name="測試產品",
        category="測試分類",
        scenario=(),
        price=None,
        image_url=None,
        rule_hits=(),
        hit_count=0,
    )
    result = _format_candidates_section([no_scenario])
    assert "無" in result


# ===========================================================================
# 16. _load_fallback_product — Exception 路徑（products.json 損毀）
# ===========================================================================


def test_load_fallback_product_returns_none_on_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """products.json 讀取拋例外時，回傳 None。"""
    from app.services.prompts import product_recommendation as pr_module

    monkeypatch.setattr(
        pr_module,
        "_PRODUCTS_JSON_PATH",
        Path("/nonexistent/products.json"),
    )
    result = pr_module._load_fallback_product()
    assert result is None


# ===========================================================================
# 17. _build_fallback_from_candidates — empty candidates
# ===========================================================================


def test_build_fallback_from_candidates_empty_list() -> None:
    """candidates=[] 時 _build_fallback_from_candidates 應回傳 []。"""
    from app.services.prompts.product_recommendation import _build_fallback_from_candidates

    result = _build_fallback_from_candidates([])
    assert result == []


# ===========================================================================
# 18. _build_fallback_from_products_json — None 路徑（products.json 不可讀）
# ===========================================================================


def test_build_fallback_from_products_json_returns_empty_when_no_product(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_load_fallback_product 回 None 時，_build_fallback_from_products_json 應回 []。"""
    from app.services.prompts import product_recommendation as pr_module

    monkeypatch.setattr(pr_module, "_load_fallback_product", lambda: None)
    result = pr_module._build_fallback_from_products_json()
    assert result == []


def test_build_fallback_from_products_json_key_error_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """products.json 缺少 sku 欄位（KeyError）時，回傳 []。"""
    from app.services.prompts import product_recommendation as pr_module

    # 缺少 sku 欄位的 product dict
    monkeypatch.setattr(
        pr_module,
        "_load_fallback_product",
        lambda: {"name": "無 SKU 產品", "image_url": None},
    )
    result = pr_module._build_fallback_from_products_json()
    assert result == []


# ===========================================================================
# 19. _parse_llm_products — ValidationError 路徑（reason 太短）
# ===========================================================================


def test_parse_llm_products_validation_error_skipped(candidate_a) -> None:
    """reason 字串過短（< 10 字）觸發 ValidationError 時，該項目應被略過。"""
    from app.services.prompts.product_recommendation import _parse_llm_products

    candidates_map = {"23711": candidate_a}
    # reason 只有 3 字，不足 10 字，會觸發 RecommendedProduct 驗證錯誤
    raw_items = [{"sku": "23711", "reason": "短", "confidence": 0.8}]

    result = _parse_llm_products(raw_items, candidates_map, max_products=3)
    # 驗證失敗的項目被略過 → 結果為空
    assert result == []


def test_build_fallback_from_candidates_validation_error_returns_empty() -> None:
    """
    _build_fallback_from_candidates：若 CandidateProduct 的 sku 為空（""），
    建立 RecommendedProduct 時觸發 ValidationError → 回傳 []。
    """
    from app.services.prompts.product_recommendation import (
        CandidateProduct,
        _build_fallback_from_candidates,
    )

    # sku="" 會觸發 RecommendedProduct(sku="", ...) 的 min_length=1 驗證錯誤
    bad_candidate = CandidateProduct(
        sku="X",  # sku 必須有值才能建立 CandidateProduct
        name="測試產品名稱",
        category="測試",
        scenario=(),
        price=None,
        image_url=None,
        rule_hits=(),
        hit_count=0,
    )

    # 用 monkeypatch 替換成空 sku 的假 candidate
    from unittest.mock import MagicMock

    bad_mock = MagicMock()
    bad_mock.sku = ""  # 空 sku → RecommendedProduct min_length=1 驗證失敗
    bad_mock.name = "測試"
    bad_mock.image_url = None

    result = _build_fallback_from_candidates([bad_mock])
    assert result == []
