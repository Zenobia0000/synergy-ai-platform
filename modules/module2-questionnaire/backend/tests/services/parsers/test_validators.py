"""
validators.py 的單元測試與整合測試。

測試策略：
- 正常路徑：載入實際產出的 JSON 並呼叫驗證函式
- 錯誤路徑：構造不合規格的 dict，確認 ValidationError 被正確拋出
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.parsers.validators import (
    MetaModel,
    QuestionnaireModel,
    ProductsModel,
    ProductRulesModel,
    validate_questionnaire,
    validate_products,
    validate_rules,
)

# ---------------------------------------------------------------------------
# 路徑常數
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parents[3]  # backend/
_SCHEMAS_DIR = _BACKEND_DIR.parent / "data" / "schemas"

QUESTIONNAIRE_JSON = _SCHEMAS_DIR / "questionnaire.json"
PRODUCTS_JSON = _SCHEMAS_DIR / "products.json"
RULES_JSON = _SCHEMAS_DIR / "product_rules.json"


# ---------------------------------------------------------------------------
# 整合測試：驗證實際 CLI 產出的 JSON
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not QUESTIONNAIRE_JSON.exists(),
    reason="questionnaire.json 尚未產出，請先執行 build_schemas.py",
)
def test_validate_generated_questionnaire_json():
    """載入 questionnaire.json 進行 Pydantic 驗證，不應拋出錯誤。"""
    data = json.loads(QUESTIONNAIRE_JSON.read_text(encoding="utf-8"))
    model = validate_questionnaire(data)
    assert model.version == "1.0.0"
    assert len(model.sections) > 0
    assert model.meta.source_sha256  # 非空
    # 驗證至少有一個欄位有 field_id
    all_field_ids = [f.field_id for s in model.sections for f in s.fields]
    assert len(all_field_ids) > 0


@pytest.mark.skipif(
    not PRODUCTS_JSON.exists(),
    reason="products.json 尚未產出，請先執行 build_schemas.py",
)
def test_validate_generated_products_json():
    """載入 products.json 進行 Pydantic 驗證，不應拋出錯誤。"""
    data = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    model = validate_products(data)
    assert len(model.products) > 0
    assert model.meta.parser_version == "0.1.0"
    # 驗證每個產品都有 sku
    for product in model.products:
        assert product.sku.strip()


@pytest.mark.skipif(
    not RULES_JSON.exists(),
    reason="product_rules.json 尚未產出，請先執行 build_schemas.py",
)
def test_validate_generated_rules_json():
    """載入 product_rules.json 進行 Pydantic 驗證，不應拋出錯誤。"""
    data = json.loads(RULES_JSON.read_text(encoding="utf-8"))
    model = validate_rules(data)
    assert len(model.rules) >= 10  # 至少 10 條規則
    assert model.meta.source_file


# ---------------------------------------------------------------------------
# 單元測試：MetaModel 驗證
# ---------------------------------------------------------------------------


def _valid_meta() -> dict:
    return {
        "source_file": "test.xlsx",
        "source_sha256": "a" * 64,
        "generated_at": "2026-04-21T12:00:00+08:00",
        "parser_version": "0.1.0",
    }


def test_meta_model_valid():
    """合規的 meta dict 應通過驗證。"""
    m = MetaModel(**_valid_meta())
    assert m.source_file == "test.xlsx"
    assert m.source_sha256 == "a" * 64


def test_reject_meta_missing_sha256():
    """缺少 source_sha256 應拋出 ValidationError。"""
    data = _valid_meta()
    del data["source_sha256"]
    with pytest.raises(ValidationError):
        MetaModel(**data)


def test_reject_meta_invalid_sha256_length():
    """sha256 長度不是 64 hex 字元應拋出 ValidationError。"""
    data = _valid_meta()
    data["source_sha256"] = "abc123"  # 太短
    with pytest.raises(ValidationError) as exc_info:
        MetaModel(**data)
    assert "source_sha256" in str(exc_info.value).lower() or "64" in str(exc_info.value)


def test_reject_meta_non_hex_sha256():
    """sha256 包含非十六進位字元應拋出 ValidationError。"""
    data = _valid_meta()
    data["source_sha256"] = "g" * 64  # g 不是 hex
    with pytest.raises(ValidationError):
        MetaModel(**data)


def test_reject_meta_empty_source_file():
    """空白的 source_file 應拋出 ValidationError。"""
    data = _valid_meta()
    data["source_file"] = "   "
    with pytest.raises(ValidationError):
        MetaModel(**data)


# ---------------------------------------------------------------------------
# 單元測試：FieldModel type 驗證
# ---------------------------------------------------------------------------


def _valid_questionnaire_dict() -> dict:
    """構造最小合規問卷 dict。"""
    return {
        "_meta": _valid_meta(),
        "version": "1.0.0",
        "title": "Test Questionnaire",
        "sections": [
            {
                "id": "basic_info",
                "title": "基本資料",
                "order": 1,
                "fields": [
                    {
                        "field_id": "gender",
                        "label": "性別",
                        "type": "single_choice",
                        "required": True,
                        "options": [{"value": "male", "label": "男"}],
                        "default": None,
                        "help_text": None,
                        "condition": None,
                        "pii": False,
                        "order": 1,
                        "min": None,
                        "max": None,
                        "unit": None,
                    }
                ],
            }
        ],
    }


def test_reject_field_with_invalid_type():
    """欄位 type 為 'unknown' 應拋出 ValidationError。"""
    data = _valid_questionnaire_dict()
    data["sections"][0]["fields"][0]["type"] = "unknown"
    with pytest.raises(ValidationError):
        validate_questionnaire(data)


def test_reject_field_with_empty_field_id():
    """欄位 field_id 為空字串應拋出 ValidationError。"""
    data = _valid_questionnaire_dict()
    data["sections"][0]["fields"][0]["field_id"] = ""
    with pytest.raises(ValidationError):
        validate_questionnaire(data)


def test_questionnaire_all_valid_types():
    """所有合法 type 值都應通過驗證。"""
    valid_types = [
        "single_choice", "multi_choice", "text", "textarea", "number", "date", "scale"
    ]
    for t in valid_types:
        data = _valid_questionnaire_dict()
        data["sections"][0]["fields"][0]["type"] = t
        model = validate_questionnaire(data)
        assert model.sections[0].fields[0].type == t


# ---------------------------------------------------------------------------
# 單元測試：Products 驗證
# ---------------------------------------------------------------------------


def _valid_products_dict() -> dict:
    """構造最小合規產品 dict。"""
    return {
        "_meta": _valid_meta(),
        "products": [
            {
                "sku": "96371",
                "name": "普精耐粉末食品",
                "category": "心血管",
                "scenario": ["三高族群"],
                "price": 3800,
                "price_display": "NT$3,800",
                "bundle_contents": None,
                "usage_note": "每日1包",
                "image_url": None,
                "image_match_confidence": None,
            }
        ],
        "unmatched_images": [],
    }


def test_products_valid():
    """合規的 products dict 應通過驗證。"""
    model = validate_products(_valid_products_dict())
    assert model.products[0].sku == "96371"


def test_reject_product_with_empty_sku():
    """空 sku 應拋出 ValidationError。"""
    data = _valid_products_dict()
    data["products"][0]["sku"] = ""
    with pytest.raises(ValidationError):
        validate_products(data)


# ---------------------------------------------------------------------------
# 單元測試：Rules 驗證
# ---------------------------------------------------------------------------


def _valid_rules_dict() -> dict:
    """構造最小合規規則 dict。"""
    return {
        "_meta": _valid_meta(),
        "rules": [
            {
                "id": "rule_001_0",
                "trigger": {"logic": "and", "conditions": []},
                "recommended_skus": ["96371"],
                "reason_raw": "體重過重建議補充",
                "source_row": 1,
            }
        ],
        "unmatched_rule_products": [],
    }


def test_rules_valid():
    """合規的 rules dict 應通過驗證。"""
    model = validate_rules(_valid_rules_dict())
    assert len(model.rules) == 1
    assert model.rules[0].id == "rule_001_0"


def test_reject_rule_trigger_invalid_logic():
    """trigger.logic 非 'and'/'or' 應拋出 ValidationError。"""
    data = _valid_rules_dict()
    data["rules"][0]["trigger"]["logic"] = "xor"
    with pytest.raises(ValidationError):
        validate_rules(data)


def test_reject_rule_with_empty_id():
    """規則 id 為空字串應拋出 ValidationError。"""
    data = _valid_rules_dict()
    data["rules"][0]["id"] = ""
    with pytest.raises(ValidationError):
        validate_rules(data)
