"""
TDD 測試：app.schemas.advice 輸出契約驗證。

測試順序依照 Red-Green-Refactor 方法論建立，先驗證邊界條件與錯誤路徑，
再驗證正常路徑，最後驗證整體 JSON schema 結構。
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import json

from app.schemas.advice import (
    AdviceRequest,
    AdviceResponse,
    HealthAssessmentSummary,
    NextAction,
    RecommendedProduct,
    SalesScript,
    get_advice_response_schema_json,
)


# ---------------------------------------------------------------------------
# 測試輔助函式：建立最小合法資料
# ---------------------------------------------------------------------------


def _valid_product(**overrides) -> dict:
    """回傳合法的 RecommendedProduct 欄位 dict。"""
    base = {
        "sku": "PRD-001",
        "name": "超級維他命 C",
        "reason": "此客戶有明顯的免疫力不足症狀，維他命 C 可強化防禦力",
        "image_url": None,
        "confidence": 0.85,
    }
    return {**base, **overrides}


def _valid_script(**overrides) -> dict:
    """回傳合法的 SalesScript 欄位 dict。"""
    base = {
        "scenario": "opening",
        "script": "您好，根據您填寫的健康問卷，我發現您最近睡眠品質不佳，這讓我很擔心。",
        "taboo": None,
    }
    return {**base, **overrides}


def _valid_next_action(**overrides) -> dict:
    """回傳合法的 NextAction 欄位 dict。"""
    base = {
        "action": "schedule_consultation",
        "why": "客戶有多項中高風險指標，需安排專業諮詢",
        "priority": "high",
    }
    return {**base, **overrides}


def _valid_summary(**overrides) -> dict:
    """回傳合法的 HealthAssessmentSummary 欄位 dict。"""
    base = {
        "key_risks": ["睡眠品質差", "免疫力低下"],
        "overall_level": "medium",
        "narrative": (
            "根據您的問卷填答，您目前有睡眠品質不佳與免疫力下降等健康隱患。"
            "建議優先改善睡眠習慣並補充必要營養素。"
            "整體健康風險為中等，需持續關注後續變化。"
        ),
    }
    return {**base, **overrides}


def _valid_advice_response(**overrides) -> dict:
    """回傳合法的 AdviceResponse 欄位 dict。"""
    base = {
        "summary": _valid_summary(),
        "recommended_products": [_valid_product()],
        "sales_scripts": [
            _valid_script(scenario="opening"),
            _valid_script(scenario="closing", script="感謝您今天的時間，我建議您先試用一個月看看效果如何。"),
        ],
        "next_actions": [_valid_next_action()],
    }
    return {**base, **overrides}


# ---------------------------------------------------------------------------
# 1. RecommendedProduct 測試
# ---------------------------------------------------------------------------


class TestRecommendedProduct:
    def test_requires_reason_min_length(self):
        """reason 不足 10 字應拋出 ValidationError。"""
        data = _valid_product(reason="太短了")
        with pytest.raises(ValidationError) as exc_info:
            RecommendedProduct(**data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("reason",) for e in errors)

    def test_accepts_valid_payload(self):
        """合法資料應成功建立實例。"""
        product = RecommendedProduct(**_valid_product())
        assert product.sku == "PRD-001"
        assert product.confidence == 0.85
        assert product.image_url is None

    def test_rejects_extra_field(self):
        """extra='forbid' 應拒絕未定義的額外欄位。"""
        data = _valid_product(unknown_field="偷渡進來的欄位")
        with pytest.raises(ValidationError) as exc_info:
            RecommendedProduct(**data)
        errors = exc_info.value.errors()
        assert any("extra" in e["type"] for e in errors)

    def test_confidence_must_be_between_0_and_1(self):
        """confidence 超出 [0, 1] 範圍應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            RecommendedProduct(**_valid_product(confidence=1.5))
        with pytest.raises(ValidationError):
            RecommendedProduct(**_valid_product(confidence=-0.1))

    def test_sku_must_not_be_empty(self):
        """sku 為空字串應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            RecommendedProduct(**_valid_product(sku=""))

    def test_image_url_validates_format(self):
        """image_url 必須是合法 URL，無效格式應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            RecommendedProduct(**_valid_product(image_url="not-a-url"))

    def test_image_url_accepts_valid_https(self):
        """合法 HTTPS URL 應被接受。"""
        product = RecommendedProduct(**_valid_product(image_url="https://example.com/img.jpg"))
        assert product.image_url is not None


# ---------------------------------------------------------------------------
# 2. SalesScript 測試
# ---------------------------------------------------------------------------


class TestSalesScript:
    def test_scenario_must_be_enum(self):
        """scenario 不在允許值內應拋出 ValidationError。"""
        data = _valid_script(scenario="invalid_scenario")
        with pytest.raises(ValidationError) as exc_info:
            SalesScript(**data)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("scenario",) for e in errors)

    def test_accepts_all_valid_scenarios(self):
        """四個合法 scenario 值都應通過。"""
        for scenario in ("opening", "objection", "closing", "follow_up"):
            script = SalesScript(**_valid_script(scenario=scenario))
            assert script.scenario == scenario

    def test_script_min_length(self):
        """script 少於 20 字應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            SalesScript(**_valid_script(script="太短"))

    def test_taboo_is_optional(self):
        """taboo 可為 None。"""
        script = SalesScript(**_valid_script(taboo=None))
        assert script.taboo is None

        script_with_taboo = SalesScript(**_valid_script(taboo="避免提及價格比較"))
        assert script_with_taboo.taboo == "避免提及價格比較"

    def test_rejects_extra_field(self):
        """extra='forbid' 應拒絕未定義的額外欄位。"""
        with pytest.raises(ValidationError):
            SalesScript(**_valid_script(extra_key="value"))


# ---------------------------------------------------------------------------
# 3. NextAction 測試
# ---------------------------------------------------------------------------


class TestNextAction:
    def test_default_priority_is_medium(self):
        """未指定 priority 時預設值應為 'medium'。"""
        data = {
            "action": "schedule_consultation",
            "why": "客戶有多項健康風險指標需要專業諮詢",
        }
        action = NextAction(**data)
        assert action.priority == "medium"

    def test_action_must_be_valid_enum(self):
        """action 不在允許值內應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            NextAction(**_valid_next_action(action="make_sale"))

    def test_why_min_length(self):
        """why 少於 10 字應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            NextAction(**_valid_next_action(why="太短"))

    def test_accepts_all_valid_actions(self):
        """所有合法 action 值都應通過。"""
        valid_actions = [
            "schedule_consultation",
            "offer_trial",
            "escalate_to_senior",
            "send_educational_content",
            "hold_for_warming",
        ]
        for action in valid_actions:
            na = NextAction(**_valid_next_action(action=action))
            assert na.action == action

    def test_accepts_all_valid_priorities(self):
        """high、medium、low 三個優先級都應通過。"""
        for priority in ("high", "medium", "low"):
            na = NextAction(**_valid_next_action(priority=priority))
            assert na.priority == priority


# ---------------------------------------------------------------------------
# 4. HealthAssessmentSummary 測試
# ---------------------------------------------------------------------------


class TestHealthAssessmentSummary:
    def test_has_default_disclaimers(self):
        """未提供 disclaimers 時應包含預設免責聲明。"""
        summary = HealthAssessmentSummary(**_valid_summary())
        assert len(summary.disclaimers) >= 1
        assert any("醫療" in d or "醫師" in d for d in summary.disclaimers)

    def test_overall_level_must_be_enum(self):
        """overall_level 不在 low/medium/high 內應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            HealthAssessmentSummary(**_valid_summary(overall_level="critical"))

    def test_key_risks_min_one_item(self):
        """key_risks 為空列表應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            HealthAssessmentSummary(**_valid_summary(key_risks=[]))

    def test_key_risks_max_five_items(self):
        """key_risks 超過 5 項應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            HealthAssessmentSummary(**_valid_summary(key_risks=["a", "b", "c", "d", "e", "f"]))

    def test_narrative_min_length(self):
        """narrative 少於 30 字應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            HealthAssessmentSummary(**_valid_summary(narrative="太短了"))

    def test_custom_disclaimers_override_default(self):
        """明確提供 disclaimers 時應使用自訂值。"""
        custom = ["此為自訂免責聲明，請注意。"]
        summary = HealthAssessmentSummary(**_valid_summary(disclaimers=custom))
        assert summary.disclaimers == custom


# ---------------------------------------------------------------------------
# 5. AdviceResponse 測試
# ---------------------------------------------------------------------------


class TestAdviceResponse:
    def test_requires_at_least_one_product(self):
        """recommended_products 為空列表應拋出 ValidationError。"""
        data = _valid_advice_response(recommended_products=[])
        with pytest.raises(ValidationError) as exc_info:
            AdviceResponse(**data)
        errors = exc_info.value.errors()
        assert any("recommended_products" in str(e["loc"]) for e in errors)

    def test_max_five_products(self):
        """超過 5 個 recommended_products 應拋出 ValidationError。"""
        products = [_valid_product(sku=f"PRD-{i:03d}") for i in range(6)]
        data = _valid_advice_response(recommended_products=products)
        with pytest.raises(ValidationError):
            AdviceResponse(**data)

    def test_accepts_up_to_five_products(self):
        """恰好 5 個 recommended_products 應通過驗證。"""
        products = [_valid_product(sku=f"PRD-{i:03d}") for i in range(5)]
        data = _valid_advice_response(recommended_products=products)
        response = AdviceResponse(**data)
        assert len(response.recommended_products) == 5

    def test_requires_at_least_two_sales_scripts(self):
        """sales_scripts 只有 1 個應拋出 ValidationError。"""
        data = _valid_advice_response(sales_scripts=[_valid_script()])
        with pytest.raises(ValidationError):
            AdviceResponse(**data)

    def test_max_three_next_actions(self):
        """next_actions 超過 3 個應拋出 ValidationError。"""
        actions = [_valid_next_action() for _ in range(4)]
        data = _valid_advice_response(next_actions=actions)
        with pytest.raises(ValidationError):
            AdviceResponse(**data)

    def test_json_schema_contains_all_sections(self):
        """model_json_schema() 必須包含四個核心區段。"""
        schema = AdviceResponse.model_json_schema()
        properties = schema.get("properties", {})
        assert "summary" in properties
        assert "recommended_products" in properties
        assert "sales_scripts" in properties
        assert "next_actions" in properties

    def test_round_trip(self):
        """instance → model_dump() → AdviceResponse(**data) 應相等。"""
        original = AdviceResponse(**_valid_advice_response())
        dumped = original.model_dump()
        restored = AdviceResponse(**dumped)
        assert original.model_dump() == restored.model_dump()

    def test_accepts_valid_full_payload(self):
        """完整合法資料應成功建立實例並保留所有欄位。"""
        response = AdviceResponse(**_valid_advice_response())
        assert response.summary.overall_level == "medium"
        assert len(response.recommended_products) == 1
        assert len(response.sales_scripts) == 2
        assert len(response.next_actions) == 1


# ---------------------------------------------------------------------------
# 6. AdviceRequest 測試
# ---------------------------------------------------------------------------


class TestAdviceRequest:
    def test_accepts_mixed_answer_types(self):
        """answers 應接受 str、int、float、bool、list[str]、None 混合型別。"""
        request = AdviceRequest(
            answers={
                "q_name": "張小明",
                "q_age": 45,
                "q_bmi": 24.5,
                "q_smoking": True,
                "q_symptoms": ["頭痛", "失眠", "疲勞"],
                "q_optional": None,
            }
        )
        assert request.answers["q_name"] == "張小明"
        assert request.answers["q_age"] == 45
        assert request.answers["q_bmi"] == 24.5
        assert request.answers["q_smoking"] is True
        assert request.answers["q_symptoms"] == ["頭痛", "失眠", "疲勞"]
        assert request.answers["q_optional"] is None

    def test_default_locale_is_zh_tw(self):
        """未指定 locale 時預設應為 'zh-TW'。"""
        request = AdviceRequest(answers={"q1": "answer"})
        assert request.locale == "zh-TW"

    def test_default_coach_level_is_new(self):
        """未指定 coach_level 時預設應為 'new'。"""
        request = AdviceRequest(answers={"q1": "answer"})
        assert request.coach_level == "new"

    def test_locale_must_be_valid_enum(self):
        """locale 不在允許值內應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            AdviceRequest(answers={"q1": "a"}, locale="fr-FR")  # type: ignore[arg-type]

    def test_coach_level_must_be_valid_enum(self):
        """coach_level 不在允許值內應拋出 ValidationError。"""
        with pytest.raises(ValidationError):
            AdviceRequest(answers={"q1": "a"}, coach_level="expert")  # type: ignore[arg-type]

    def test_rejects_extra_field(self):
        """extra='forbid' 應拒絕未定義的額外欄位。"""
        with pytest.raises(ValidationError):
            AdviceRequest(answers={"q1": "a"}, unknown_param="value")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# 7. Helper 函式測試
# ---------------------------------------------------------------------------


class TestGetAdviceResponseSchemaJson:
    def test_returns_valid_json_string(self):
        """get_advice_response_schema_json() 應回傳可解析的 JSON 字串。"""
        result = get_advice_response_schema_json()
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_schema_contains_required_properties(self):
        """產出的 schema 必須包含四個核心區段的定義。"""
        result = get_advice_response_schema_json()
        parsed = json.loads(result)
        # JSON Schema 定義的 properties 或透過 $defs 解析
        schema_str = result
        assert "summary" in schema_str
        assert "recommended_products" in schema_str
        assert "sales_scripts" in schema_str
        assert "next_actions" in schema_str

    def test_respects_indent_parameter(self):
        """indent 參數應影響縮排格式。"""
        compact = get_advice_response_schema_json(indent=0)
        indented = get_advice_response_schema_json(indent=4)
        # indent=0 不換行（較短），indent=4 會有換行（較長）
        assert len(compact) < len(indented)
