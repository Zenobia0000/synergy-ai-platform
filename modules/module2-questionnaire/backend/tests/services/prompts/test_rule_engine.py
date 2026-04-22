"""
TDD 測試：rule_engine.py

測試規則引擎的純函式行為。所有測試不涉及 LLM 呼叫。

執行：
    (cd backend && uv run pytest tests/services/prompts/test_rule_engine.py -v)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "schemas"
_PRODUCTS_PATH = _DATA_DIR / "products.json"
_RULES_PATH = _DATA_DIR / "product_rules.json"


# ---------------------------------------------------------------------------
# 延遲匯入：待實作完成後才可用
# ---------------------------------------------------------------------------

from app.services.prompts.rule_engine import (
    CandidateProduct,
    Rule,
    RuleCondition,
    collect_candidates,
    evaluate_rules,
    load_catalog,
)


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def products_and_rules():
    """載入真實 products.json + product_rules.json。"""
    return load_catalog(_PRODUCTS_PATH, _RULES_PATH)


@pytest.fixture
def simple_rule_with_condition() -> Rule:
    """建立一條有 == 條件的測試規則。"""
    return Rule(
        id="rule_test_0",
        logic="and",
        conditions=(
            RuleCondition(field_id="gender", op="==", value="男"),
        ),
        recommended_skus=("SKU-001", "SKU-002"),
        reason_raw="測試規則",
        source_row=99,
    )


@pytest.fixture
def sample_products_map() -> dict:
    """最小 products map，供 collect_candidates 使用。"""
    return {
        "SKU-001": {
            "sku": "SKU-001",
            "name": "測試產品 A",
            "category": "免疫提升/營養補充",
            "scenario": ["需加強免疫功能"],
            "price": 1000,
            "image_url": None,
        },
        "SKU-002": {
            "sku": "SKU-002",
            "name": "測試產品 B",
            "category": "心血管/體重管理",
            "scenario": ["三高族群", "心血管保健"],
            "price": 2000,
            "image_url": "https://example.com/b.png",
        },
        "SKU-003": {
            "sku": "SKU-003",
            "name": "測試產品 C",
            "category": "血液循環/營養補充",
            "scenario": ["需提升血液循環"],
            "price": 3000,
            "image_url": None,
        },
    }


# ===========================================================================
# 1. load_catalog
# ===========================================================================


def test_load_catalog_returns_products_and_rules(products_and_rules):
    """load_catalog 應回傳 (products dict, rules list)，數量符合 JSON 實際資料。"""
    products, rules = products_and_rules

    # products.json 有 33 個產品
    assert len(products) == 33
    # product_rules.json 有 61 條規則
    assert len(rules) == 61

    # 檢查第一個產品有必要欄位
    first_product = next(iter(products.values()))
    assert "sku" in first_product
    assert "name" in first_product
    assert "category" in first_product


# ===========================================================================
# 2. evaluate_rules — 空 conditions 不觸發
# ===========================================================================


def test_evaluate_empty_rule_not_triggered():
    """空 conditions 的規則一律不觸發（避免過多候選）。"""
    rules = [
        Rule(
            id="rule_012_0",
            logic="and",
            conditions=(),  # 空 conditions
            recommended_skus=("23711",),
            reason_raw="體重管理",
            source_row=12,
        )
    ]
    answers: dict[str, Any] = {"gender": "男", "age": 45}
    triggered = evaluate_rules(answers, rules)
    assert triggered == []


# ===========================================================================
# 3. evaluate_rules — == 操作符
# ===========================================================================


def test_evaluate_equals_operator():
    """op=='==' 時，答案等於 value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_0",
            logic="and",
            conditions=(
                RuleCondition(field_id="gender", op="==", value="男"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="男性",
            source_row=99,
        )
    ]
    answers = {"gender": "男"}
    triggered = evaluate_rules(answers, rules)
    assert "rule_test_0" in triggered


def test_evaluate_equals_operator_no_match():
    """op=='==' 時，答案不等於 value 則不觸發。"""
    rules = [
        Rule(
            id="rule_test_0",
            logic="and",
            conditions=(
                RuleCondition(field_id="gender", op="==", value="男"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="男性",
            source_row=99,
        )
    ]
    answers = {"gender": "女"}
    triggered = evaluate_rules(answers, rules)
    assert triggered == []


# ===========================================================================
# 4. evaluate_rules — != 操作符
# ===========================================================================


def test_evaluate_not_equals():
    """op='!=' 時，答案不等於 value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_ne",
            logic="and",
            conditions=(
                RuleCondition(field_id="sleep_quality", op="!=", value="好"),
            ),
            recommended_skus=("SKU-002",),
            reason_raw="睡眠不佳",
            source_row=99,
        )
    ]
    answers = {"sleep_quality": "差"}
    triggered = evaluate_rules(answers, rules)
    assert "rule_test_ne" in triggered


# ===========================================================================
# 5. evaluate_rules — >= 數值比較
# ===========================================================================


def test_evaluate_ge_numeric():
    """op='>=' 時，answers 中的數值 >= value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_ge",
            logic="and",
            conditions=(
                RuleCondition(field_id="current_weight_kg", op=">=", value=80),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="體重過重",
            source_row=99,
        )
    ]
    answers = {"current_weight_kg": 85}
    triggered = evaluate_rules(answers, rules)
    assert "rule_test_ge" in triggered


def test_evaluate_ge_numeric_below_threshold():
    """op='>=' 時，answers 中的數值 < value 則不觸發。"""
    rules = [
        Rule(
            id="rule_test_ge",
            logic="and",
            conditions=(
                RuleCondition(field_id="current_weight_kg", op=">=", value=80),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="體重過重",
            source_row=99,
        )
    ]
    answers = {"current_weight_kg": 70}
    triggered = evaluate_rules(answers, rules)
    assert triggered == []


# ===========================================================================
# 6. evaluate_rules — and 邏輯
# ===========================================================================


def test_evaluate_and_logic():
    """logic='and' 時，所有條件都符合才觸發。"""
    rules = [
        Rule(
            id="rule_test_and",
            logic="and",
            conditions=(
                RuleCondition(field_id="gender", op="==", value="男"),
                RuleCondition(field_id="current_weight_kg", op=">=", value=80),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="男性體重過重",
            source_row=99,
        )
    ]
    # 兩條件皆符合
    answers = {"gender": "男", "current_weight_kg": 90}
    triggered = evaluate_rules(answers, rules)
    assert "rule_test_and" in triggered

    # 只有一條件符合
    answers_partial = {"gender": "男", "current_weight_kg": 60}
    triggered_partial = evaluate_rules(answers_partial, rules)
    assert triggered_partial == []


# ===========================================================================
# 7. evaluate_rules — or 邏輯
# ===========================================================================


def test_evaluate_or_logic():
    """logic='or' 時，任一條件符合即觸發。"""
    rules = [
        Rule(
            id="rule_test_or",
            logic="or",
            conditions=(
                RuleCondition(field_id="stress_level", op="==", value="高"),
                RuleCondition(field_id="sleep_quality", op="==", value="差"),
            ),
            recommended_skus=("SKU-002",),
            reason_raw="壓力或睡眠問題",
            source_row=99,
        )
    ]
    # 只有 stress_level 符合
    answers = {"stress_level": "高", "sleep_quality": "普通"}
    triggered = evaluate_rules(answers, rules)
    assert "rule_test_or" in triggered

    # 兩個都不符合
    answers_none = {"stress_level": "低", "sleep_quality": "好"}
    triggered_none = evaluate_rules(answers_none, rules)
    assert triggered_none == []


# ===========================================================================
# 8. evaluate_rules — 缺少 field_id 視為 False
# ===========================================================================


def test_missing_field_treated_as_false():
    """answers 中找不到 field_id 時，該條件判為 False，不觸發。"""
    rules = [
        Rule(
            id="rule_test_missing",
            logic="and",
            conditions=(
                RuleCondition(field_id="nonexistent_field", op="==", value="任意值"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="測試缺少欄位",
            source_row=99,
        )
    ]
    answers = {"gender": "男"}  # 沒有 nonexistent_field
    triggered = evaluate_rules(answers, rules)
    assert triggered == []


# ===========================================================================
# 9. collect_candidates — 多規則命中同 SKU 去重 + 累計 hit_count
# ===========================================================================


def test_collect_candidates_dedupes_sku(sample_products_map):
    """多條規則命中同一 SKU 時，只保留一筆，hit_count 累計。"""
    rules = [
        Rule(
            id="rule_A",
            logic="and",
            conditions=(RuleCondition(field_id="gender", op="==", value="男"),),
            recommended_skus=("SKU-001", "SKU-002"),
            reason_raw="規則 A",
            source_row=10,
        ),
        Rule(
            id="rule_B",
            logic="and",
            conditions=(RuleCondition(field_id="age", op=">=", value=40),),
            recommended_skus=("SKU-001", "SKU-003"),
            reason_raw="規則 B",
            source_row=20,
        ),
    ]
    answers = {"gender": "男", "age": 45}
    triggered_ids = evaluate_rules(answers, rules)
    candidates = collect_candidates(triggered_ids, rules, sample_products_map)

    sku_map = {c.sku: c for c in candidates}

    # SKU-001 被兩條規則命中
    assert "SKU-001" in sku_map
    assert sku_map["SKU-001"].hit_count == 2

    # SKU-002 只被一條規則命中
    assert "SKU-002" in sku_map
    assert sku_map["SKU-002"].hit_count == 1

    # SKU-003 只被一條規則命中
    assert "SKU-003" in sku_map
    assert sku_map["SKU-003"].hit_count == 1

    # 總共 3 個不同 SKU（無重複）
    assert len(candidates) == 3


# ===========================================================================
# 10. collect_candidates — 依 hit_count 降序排列
# ===========================================================================


def test_collect_candidates_sorted_by_hit_count_desc(sample_products_map):
    """collect_candidates 回傳清單應依 hit_count 降序排列。"""
    rules = [
        Rule(
            id="rule_A",
            logic="and",
            conditions=(RuleCondition(field_id="gender", op="==", value="男"),),
            recommended_skus=("SKU-001", "SKU-002"),
            reason_raw="規則 A",
            source_row=10,
        ),
        Rule(
            id="rule_B",
            logic="and",
            conditions=(RuleCondition(field_id="age", op=">=", value=40),),
            recommended_skus=("SKU-001",),
            reason_raw="規則 B",
            source_row=20,
        ),
        Rule(
            id="rule_C",
            logic="and",
            conditions=(RuleCondition(field_id="stress_level", op="==", value="高"),),
            recommended_skus=("SKU-001", "SKU-003"),
            reason_raw="規則 C",
            source_row=30,
        ),
    ]
    answers = {"gender": "男", "age": 45, "stress_level": "高"}
    triggered_ids = evaluate_rules(answers, rules)
    candidates = collect_candidates(triggered_ids, rules, sample_products_map)

    # SKU-001 被 3 條規則命中，應排第一
    assert candidates[0].sku == "SKU-001"
    assert candidates[0].hit_count == 3

    # 後續依 hit_count 降序
    for i in range(len(candidates) - 1):
        assert candidates[i].hit_count >= candidates[i + 1].hit_count


# ===========================================================================
# 11. collect_candidates — 遵守 max_candidates 上限
# ===========================================================================


def test_collect_candidates_respects_max(sample_products_map):
    """collect_candidates 回傳數量不超過 max_candidates。"""
    # 建立 5 條規則，每條命中一個不同 SKU（包含 products map 中已有的）
    rules = [
        Rule(
            id=f"rule_{i}",
            logic="and",
            conditions=(RuleCondition(field_id="gender", op="==", value="男"),),
            recommended_skus=(f"SKU-00{i + 1}",),
            reason_raw=f"規則 {i}",
            source_row=i,
        )
        for i in range(1, 4)  # SKU-001, SKU-002, SKU-003
    ]
    answers = {"gender": "男"}
    triggered_ids = evaluate_rules(answers, rules)
    candidates = collect_candidates(
        triggered_ids, rules, sample_products_map, max_candidates=2
    )

    assert len(candidates) <= 2


# ===========================================================================
# 12. evaluate_rules — contains 操作符（字串）
# ===========================================================================


def test_evaluate_contains_operator():
    """op='contains' 時，answers[field_id] 包含 value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_contains",
            logic="and",
            conditions=(
                RuleCondition(field_id="primary_goals", op="contains", value="體重管理"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="體重管理目標",
            source_row=12,
        )
    ]
    # 字串包含
    answers_str = {"primary_goals": "體重管理,睡眠品質"}
    triggered_str = evaluate_rules(answers_str, rules)
    assert "rule_test_contains" in triggered_str

    # list 包含
    answers_list = {"primary_goals": ["體重管理", "睡眠品質"]}
    triggered_list = evaluate_rules(answers_list, rules)
    assert "rule_test_contains" in triggered_list

    # 不包含
    answers_none = {"primary_goals": "睡眠品質"}
    triggered_none = evaluate_rules(answers_none, rules)
    assert triggered_none == []


# ===========================================================================
# 13. evaluate_rules — in 操作符（list）
# ===========================================================================


def test_evaluate_in_operator():
    """op='in' 時，answers[field_id] 在 value list 中則觸發。"""
    rules = [
        Rule(
            id="rule_test_in",
            logic="and",
            conditions=(
                RuleCondition(field_id="stress_level", op="in", value=["高", "極高"]),
            ),
            recommended_skus=("SKU-002",),
            reason_raw="高壓力",
            source_row=15,
        )
    ]
    answers_high = {"stress_level": "高"}
    triggered = evaluate_rules(answers_high, rules)
    assert "rule_test_in" in triggered

    answers_low = {"stress_level": "低"}
    triggered_none = evaluate_rules(answers_low, rules)
    assert triggered_none == []


# ===========================================================================
# 14. CandidateProduct — immutable dataclass
# ===========================================================================


def test_candidate_product_is_frozen():
    """CandidateProduct 應為 frozen dataclass（不可變）。"""
    candidate = CandidateProduct(
        sku="SKU-001",
        name="測試產品",
        category="免疫提升",
        scenario=("需加強免疫功能",),
        price=1000,
        image_url=None,
        rule_hits=("rule_A",),
        hit_count=1,
    )
    with pytest.raises((AttributeError, TypeError)):
        candidate.hit_count = 99  # type: ignore[misc]


# ===========================================================================
# 15. collect_candidates — SKU 不在 products map 時略過
# ===========================================================================


def test_collect_candidates_skips_unknown_sku(sample_products_map):
    """若規則推薦的 SKU 不在 products map 中，應略過而非報錯。"""
    rules = [
        Rule(
            id="rule_ghost",
            logic="and",
            conditions=(RuleCondition(field_id="gender", op="==", value="男"),),
            recommended_skus=("SKU-GHOST", "SKU-001"),
            reason_raw="含不存在 SKU 的規則",
            source_row=99,
        )
    ]
    answers = {"gender": "男"}
    triggered_ids = evaluate_rules(answers, rules)
    candidates = collect_candidates(triggered_ids, rules, sample_products_map)

    skus = [c.sku for c in candidates]
    assert "SKU-GHOST" not in skus
    assert "SKU-001" in skus


# ===========================================================================
# 16. evaluate_rules — <= 操作符
# ===========================================================================


def test_evaluate_le_numeric():
    """op='<=' 時，answers 中的數值 <= value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_le",
            logic="and",
            conditions=(
                RuleCondition(field_id="age", op="<=", value=30),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="年輕族群",
            source_row=99,
        )
    ]
    answers_match = {"age": 25}
    triggered = evaluate_rules(answers_match, rules)
    assert "rule_test_le" in triggered

    answers_over = {"age": 35}
    triggered_none = evaluate_rules(answers_over, rules)
    assert triggered_none == []


# ===========================================================================
# 17. evaluate_rules — > 操作符
# ===========================================================================


def test_evaluate_gt_numeric():
    """op='>' 時，answers 中的數值 > value 則觸發（不含等號）。"""
    rules = [
        Rule(
            id="rule_test_gt",
            logic="and",
            conditions=(
                RuleCondition(field_id="age", op=">", value=40),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="中老年族群",
            source_row=99,
        )
    ]
    answers_match = {"age": 45}
    triggered = evaluate_rules(answers_match, rules)
    assert "rule_test_gt" in triggered

    answers_equal = {"age": 40}
    triggered_equal = evaluate_rules(answers_equal, rules)
    assert triggered_equal == []


# ===========================================================================
# 18. evaluate_rules — < 操作符
# ===========================================================================


def test_evaluate_lt_numeric():
    """op='<' 時，answers 中的數值 < value 則觸發。"""
    rules = [
        Rule(
            id="rule_test_lt",
            logic="and",
            conditions=(
                RuleCondition(field_id="bmi", op="<", value=18.5),
            ),
            recommended_skus=("SKU-002",),
            reason_raw="過輕族群",
            source_row=99,
        )
    ]
    answers_match = {"bmi": 17.0}
    triggered = evaluate_rules(answers_match, rules)
    assert "rule_test_lt" in triggered

    answers_over = {"bmi": 20.0}
    triggered_none = evaluate_rules(answers_over, rules)
    assert triggered_none == []


# ===========================================================================
# 19. evaluate_rules — 不支援的操作符
# ===========================================================================


def test_evaluate_unsupported_op():
    """不支援的操作符應回傳 False 且不拋出異常。"""
    rules = [
        Rule(
            id="rule_test_bad_op",
            logic="and",
            conditions=(
                RuleCondition(field_id="gender", op="BETWEEN", value="男"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="測試不支援的 op",
            source_row=99,
        )
    ]
    answers = {"gender": "男"}
    triggered = evaluate_rules(answers, rules)
    assert triggered == []


# ===========================================================================
# 20. collect_candidates — 傳入不存在的 rule_id 時略過
# ===========================================================================


def test_collect_candidates_unknown_rule_id(sample_products_map):
    """triggered_rule_ids 含不在 rules list 的 ID 時，略過而非報錯。"""
    rules = [
        Rule(
            id="rule_existing",
            logic="and",
            conditions=(RuleCondition(field_id="gender", op="==", value="男"),),
            recommended_skus=("SKU-001",),
            reason_raw="已知規則",
            source_row=99,
        )
    ]
    # 傳入一個不存在的 rule_id
    triggered_ids = ["rule_existing", "rule_nonexistent"]
    candidates = collect_candidates(triggered_ids, rules, sample_products_map)

    skus = [c.sku for c in candidates]
    assert "SKU-001" in skus
    assert len(candidates) == 1  # 只有 rule_existing 的 SKU-001


# ===========================================================================
# 21. evaluate_rules — in 操作符，expected 不是 list
# ===========================================================================


def test_evaluate_in_operator_non_list():
    """op='in'，expected 不是 list 時，回退到 == 比較。"""
    rules = [
        Rule(
            id="rule_test_in_str",
            logic="and",
            conditions=(
                RuleCondition(field_id="status", op="in", value="active"),
            ),
            recommended_skus=("SKU-001",),
            reason_raw="狀態比較",
            source_row=99,
        )
    ]
    answers_match = {"status": "active"}
    triggered = evaluate_rules(answers_match, rules)
    assert "rule_test_in_str" in triggered
