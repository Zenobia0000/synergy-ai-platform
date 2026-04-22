"""
產品規則解析器測試（TDD GREEN）。

階段 3：實際斷言，驗收條件為全部 PASS。
"""

from __future__ import annotations

from pathlib import Path

from app.services.parsers.products import parse_products
from app.services.parsers.rules import parse_product_rules

# rawdata 路徑
RAWDATA_DIR = Path(__file__).parents[4] / "rawdata"
QUESTIONNAIRE_WITH_RULES_XLSX = RAWDATA_DIR / "諮詢問卷_含產品建議.xlsx"
CATALOG_XLSX = RAWDATA_DIR / "product_catalog.xlsx"
IMAGES_DOCX = RAWDATA_DIR / "Synergy 產品圖片連結.docx"


def test_parse_returns_at_least_one_rule() -> None:
    """規則解析至少應回傳 10 條規則。"""
    products = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    result = parse_product_rules(QUESTIONNAIRE_WITH_RULES_XLSX, products)
    assert len(result.rules) >= 10, (
        f"預期至少 10 條規則，實際得到 {len(result.rules)} 條"
    )


def test_every_rule_has_recommended_skus() -> None:
    """每條規則必須至少有 1 個推薦 SKU（已過濾整條無匹配的規則）。"""
    products = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    result = parse_product_rules(QUESTIONNAIRE_WITH_RULES_XLSX, products)
    for rule in result.rules:
        assert len(rule.recommended_skus) >= 1, (
            f"規則 {rule.id!r} 沒有任何 recommended_skus"
        )


def test_unmatched_rule_products_is_tuple() -> None:
    """未匹配產品清單應為 tuple。"""
    products = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    result = parse_product_rules(QUESTIONNAIRE_WITH_RULES_XLSX, products)
    assert isinstance(result.unmatched_rule_products, tuple), (
        "unmatched_rule_products 應為 tuple"
    )
    for item in result.unmatched_rule_products:
        assert isinstance(item.name_in_xlsx, str), (
            f"name_in_xlsx 應為 str，實際為 {type(item.name_in_xlsx)}"
        )
        assert isinstance(item.source_row, int), (
            f"source_row 應為 int，實際為 {type(item.source_row)}"
        )


def test_rule_ids_unique() -> None:
    """所有規則 id 必須唯一。"""
    products = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    result = parse_product_rules(QUESTIONNAIRE_WITH_RULES_XLSX, products)
    ids = [rule.id for rule in result.rules]
    assert len(ids) == len(set(ids)), (
        f"規則 id 有重複：{[i for i in ids if ids.count(i) > 1]}"
    )
