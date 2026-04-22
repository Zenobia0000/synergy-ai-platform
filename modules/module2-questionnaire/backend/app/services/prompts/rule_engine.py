"""
規則引擎：從 product_rules.json 篩選候選產品。

策略：
    1. 解析規則條件（conditions），依 answers 評估是否觸發
    2. 匯聚被觸發規則的推薦 SKU，去重並計算命中次數
    3. 依命中次數降序排列，回傳前 max_candidates 個 CandidateProduct

所有函式皆為純函式，不呼叫 LLM，方便單元測試。

注意：
    - 空 conditions 的規則一律不觸發（避免候選過多）
    - SKU 不在 products map 中時略過，不報錯
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 支援的比較操作符
# ---------------------------------------------------------------------------

_SUPPORTED_OPS = frozenset({"==", "!=", ">=", "<=", ">", "<", "contains", "in"})


# ---------------------------------------------------------------------------
# Dataclasses（frozen=True 確保不可變）
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """單一條件：(field_id op value)。"""

    field_id: str
    op: str
    value: Any


@dataclass(frozen=True, slots=True)
class Rule:
    """
    產品推薦規則。

    Attributes
    ----------
    id:        規則唯一 ID
    logic:     多條件組合邏輯，"and" 或 "or"
    conditions: 條件 tuple（空 tuple 表示無顯性條件）
    recommended_skus: 本規則推薦的 SKU tuple
    reason_raw:       原始說明文字（Excel 原文）
    source_row:       來源 Excel 列號
    """

    id: str
    logic: str
    conditions: tuple[RuleCondition, ...]
    recommended_skus: tuple[str, ...]
    reason_raw: str
    source_row: int


@dataclass(frozen=True, slots=True)
class CandidateProduct:
    """
    候選產品：由規則引擎篩出，附帶命中資訊供 LLM 排序使用。

    Attributes
    ----------
    sku:       產品 SKU
    name:      產品名稱（繁中）
    category:  產品分類
    scenario:  適用情境 tuple
    price:     售價（整數，可能為 None）
    image_url: 圖片 URL（可能為 None）
    rule_hits: 命中此產品的規則 ID tuple
    hit_count: 命中次數（多條規則推薦同 SKU 時累加）
    """

    sku: str
    name: str
    category: str
    scenario: tuple[str, ...]
    price: int | None
    image_url: str | None
    rule_hits: tuple[str, ...]
    hit_count: int


# ---------------------------------------------------------------------------
# 載入資料
# ---------------------------------------------------------------------------


def load_catalog(
    products_path: Path,
    rules_path: Path,
) -> tuple[dict[str, dict[str, Any]], list[Rule]]:
    """
    從 products.json + product_rules.json 載入資料。

    Parameters
    ----------
    products_path:
        products.json 的路徑。
    rules_path:
        product_rules.json 的路徑。

    Returns
    -------
    tuple[dict[str, dict], list[Rule]]
        (products_map, rules_list)
        products_map: {sku: product_dict}
        rules_list: Rule 物件清單
    """
    products_raw: dict[str, Any] = json.loads(
        products_path.read_text(encoding="utf-8")
    )
    rules_raw: dict[str, Any] = json.loads(
        rules_path.read_text(encoding="utf-8")
    )

    # 建立 sku → product dict
    products_map: dict[str, dict[str, Any]] = {
        p["sku"]: p for p in products_raw.get("products", [])
    }

    # 解析規則
    rules: list[Rule] = []
    for r in rules_raw.get("rules", []):
        trigger = r.get("trigger", {})
        raw_conditions = trigger.get("conditions", [])

        parsed_conditions: tuple[RuleCondition, ...] = tuple(
            RuleCondition(
                field_id=c["field_id"],
                op=c["op"],
                value=c["value"],
            )
            for c in raw_conditions
        )

        rules.append(
            Rule(
                id=r["id"],
                logic=trigger.get("logic", "and"),
                conditions=parsed_conditions,
                recommended_skus=tuple(r.get("recommended_skus", [])),
                reason_raw=r.get("reason_raw", ""),
                source_row=r.get("source_row", 0),
            )
        )

    return products_map, rules


# ---------------------------------------------------------------------------
# 條件評估
# ---------------------------------------------------------------------------


def _evaluate_condition(condition: RuleCondition, answers: dict[str, Any]) -> bool:
    """
    評估單一條件是否成立。

    Parameters
    ----------
    condition:
        RuleCondition 物件。
    answers:
        問卷答案 dict。

    Returns
    -------
    bool
        True 表示條件成立。
    """
    if condition.field_id not in answers:
        return False

    answer = answers[condition.field_id]
    expected = condition.value
    op = condition.op

    if op not in _SUPPORTED_OPS:
        logger.warning("不支援的操作符 '%s'，條件視為 False", op)
        return False

    try:
        if op == "==":
            return answer == expected

        if op == "!=":
            return answer != expected

        if op == ">=":
            return float(answer) >= float(expected)

        if op == "<=":
            return float(answer) <= float(expected)

        if op == ">":
            return float(answer) > float(expected)

        if op == "<":
            return float(answer) < float(expected)

        if op == "contains":
            # 支援字串包含 或 list 包含
            if isinstance(answer, list):
                return expected in answer
            return expected in str(answer)

        if op == "in":
            # answer 的值在 expected list 中
            if isinstance(expected, list):
                return answer in expected
            return answer == expected

    except (TypeError, ValueError) as exc:
        logger.debug("條件評估發生錯誤：%s，視為 False", exc)
        return False

    return False  # pragma: no cover


def evaluate_rules(
    answers: dict[str, Any],
    rules: list[Rule],
) -> list[str]:
    """
    依 answers 評估規則，回傳被觸發的規則 ID 列表。

    觸發邏輯：
    - 空 conditions → 一律不觸發（避免候選過多）
    - logic="and"  → 所有條件皆成立才觸發
    - logic="or"   → 任一條件成立即觸發

    Parameters
    ----------
    answers:
        問卷填答 dict，key 為 field_id。
    rules:
        Rule 物件清單。

    Returns
    -------
    list[str]
        被觸發的規則 ID 列表（保持評估順序）。
    """
    triggered: list[str] = []

    for rule in rules:
        # 空 conditions 不觸發
        if not rule.conditions:
            continue

        if rule.logic == "and":
            is_triggered = all(
                _evaluate_condition(c, answers) for c in rule.conditions
            )
        else:  # "or" 及其他
            is_triggered = any(
                _evaluate_condition(c, answers) for c in rule.conditions
            )

        if is_triggered:
            triggered.append(rule.id)

    return triggered


# ---------------------------------------------------------------------------
# 候選產品收集
# ---------------------------------------------------------------------------


def collect_candidates(
    triggered_rule_ids: list[str],
    rules: list[Rule],
    products: dict[str, dict[str, Any]],
    *,
    max_candidates: int = 15,
) -> list[CandidateProduct]:
    """
    從觸發的規則聚合 SKU，去重、豐富產品資訊，依命中次數降序排列。

    Parameters
    ----------
    triggered_rule_ids:
        evaluate_rules() 回傳的規則 ID 列表。
    rules:
        所有 Rule 物件清單（用於查找 SKU）。
    products:
        {sku: product_dict} 映射。
    max_candidates:
        最多回傳幾個候選（預設 15）。

    Returns
    -------
    list[CandidateProduct]
        依 hit_count 降序排列，長度 <= max_candidates。
        SKU 不在 products 中的項目會被略過並記錄 warning。
    """
    # 建立規則 ID → Rule 快速查找
    rule_map: dict[str, Rule] = {r.id: r for r in rules}

    # 累積每個 SKU 的命中規則
    sku_hits: dict[str, list[str]] = {}

    for rule_id in triggered_rule_ids:
        if rule_id not in rule_map:
            logger.warning("規則 ID '%s' 不在 rules 中，略過", rule_id)
            continue

        rule = rule_map[rule_id]
        for sku in rule.recommended_skus:
            if sku not in sku_hits:
                sku_hits[sku] = []
            sku_hits[sku].append(rule_id)

    # 豐富產品資訊
    candidates: list[CandidateProduct] = []
    for sku, hit_rule_ids in sku_hits.items():
        if sku not in products:
            logger.warning("規則推薦的 SKU '%s' 不在 products 中，略過", sku)
            continue

        product = products[sku]
        scenario_raw = product.get("scenario", [])
        scenario: tuple[str, ...] = (
            tuple(scenario_raw) if isinstance(scenario_raw, list) else (scenario_raw,)
        )

        price_raw = product.get("price")
        price: int | None = int(price_raw) if price_raw is not None else None

        candidates.append(
            CandidateProduct(
                sku=sku,
                name=product.get("name", ""),
                category=product.get("category", ""),
                scenario=scenario,
                price=price,
                image_url=product.get("image_url"),
                rule_hits=tuple(hit_rule_ids),
                hit_count=len(hit_rule_ids),
            )
        )

    # 依 hit_count 降序排列，相同 hit_count 依 sku 字母序穩定排列
    candidates.sort(key=lambda c: (-c.hit_count, c.sku))

    return candidates[:max_candidates]
