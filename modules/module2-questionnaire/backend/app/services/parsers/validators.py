"""
Pydantic v2 驗證層。

對應 types.py 的 frozen dataclass，用於 CLI round-trip 驗證。
匯出三個驗證函式：validate_questionnaire、validate_products、validate_rules。
"""

from __future__ import annotations

import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# 共用
# ---------------------------------------------------------------------------

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_VALID_FIELD_TYPES = Literal[
    "single_choice",
    "multi_choice",
    "text",
    "textarea",
    "number",
    "date",
    "scale",
]


class MetaModel(BaseModel):
    """每份 JSON 的 _meta 欄位。"""

    model_config = ConfigDict(populate_by_name=True)

    source_file: str
    source_sha256: str
    generated_at: str
    parser_version: str

    @field_validator("source_sha256")
    @classmethod
    def sha256_must_be_hex64(cls, v: str) -> str:
        if not _SHA256_RE.match(v):
            raise ValueError(f"source_sha256 must be 64-char hex string, got: {v!r}")
        return v

    @field_validator("generated_at")
    @classmethod
    def generated_at_must_be_iso8601(cls, v: str) -> str:
        if not _ISO8601_RE.match(v):
            raise ValueError(f"generated_at must be ISO-8601 string, got: {v!r}")
        return v

    @field_validator("source_file")
    @classmethod
    def source_file_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("source_file must not be empty")
        return v


# ---------------------------------------------------------------------------
# 問卷 schema 模型
# ---------------------------------------------------------------------------


class FieldOptionModel(BaseModel):
    """選項模型。"""

    value: str
    label: str


class FieldConditionModel(BaseModel):
    """條件顯示規則模型。"""

    field_id: str
    op: str
    value: str

    @field_validator("field_id")
    @classmethod
    def field_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("FieldCondition.field_id must not be empty")
        return v


class FieldModel(BaseModel):
    """問卷欄位模型。"""

    field_id: str
    label: str
    type: _VALID_FIELD_TYPES  # type: ignore[valid-type]
    required: bool
    options: Optional[list[FieldOptionModel]] = None
    default: Optional[str] = None
    help_text: Optional[str] = None
    condition: Optional[FieldConditionModel] = None
    pii: bool
    order: int
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None

    @field_validator("field_id")
    @classmethod
    def field_id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field_id must not be empty")
        return v


class SectionModel(BaseModel):
    """問卷區段模型。"""

    id: str
    title: str
    order: int
    fields: list[FieldModel]

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Section.id must not be empty")
        return v


class QuestionnaireModel(BaseModel):
    """問卷根節點模型（使用 alias 處理 _meta）。"""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaModel = Field(alias="_meta")
    version: str
    title: str
    sections: list[SectionModel]


# ---------------------------------------------------------------------------
# 產品 schema 模型
# ---------------------------------------------------------------------------


class ProductModel(BaseModel):
    """單一產品模型。"""

    sku: str
    name: str
    category: str
    scenario: list[str]
    price: Optional[int] = None
    price_display: str
    bundle_contents: Optional[str] = None
    usage_note: str
    image_url: Optional[str] = None
    image_match_confidence: Optional[float] = None

    @field_validator("sku")
    @classmethod
    def sku_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Product.sku must not be empty")
        return v


class UnmatchedImageModel(BaseModel):
    """未匹配圖片模型。"""

    name_in_docx: str
    url: str
    candidates: list[str]


class ProductsModel(BaseModel):
    """產品根節點模型。"""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaModel = Field(alias="_meta")
    products: list[ProductModel]
    unmatched_images: list[UnmatchedImageModel]


# ---------------------------------------------------------------------------
# 產品規則 schema 模型
# ---------------------------------------------------------------------------


class RuleConditionModel(BaseModel):
    """規則子條件模型。"""

    field_id: str
    op: str
    value: str


class RuleTriggerModel(BaseModel):
    """規則觸發條件模型。"""

    logic: Literal["and", "or"]
    conditions: list[RuleConditionModel]


class RuleModel(BaseModel):
    """單一規則模型。"""

    id: str
    trigger: RuleTriggerModel
    recommended_skus: list[str]
    reason_raw: str
    source_row: int

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rule.id must not be empty")
        return v


class UnmatchedRuleProductModel(BaseModel):
    """未匹配規則產品模型。"""

    name_in_xlsx: str
    source_row: int


class ProductRulesModel(BaseModel):
    """規則根節點模型。"""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaModel = Field(alias="_meta")
    rules: list[RuleModel]
    unmatched_rule_products: list[UnmatchedRuleProductModel]


# ---------------------------------------------------------------------------
# 公開驗證函式
# ---------------------------------------------------------------------------


def validate_questionnaire(data: dict[str, Any]) -> QuestionnaireModel:
    """
    驗證問卷 JSON dict，回傳 QuestionnaireModel。

    Raises:
        pydantic.ValidationError: 資料不符規格
    """
    return QuestionnaireModel.model_validate(data)


def validate_products(data: dict[str, Any]) -> ProductsModel:
    """
    驗證產品 JSON dict，回傳 ProductsModel。

    Raises:
        pydantic.ValidationError: 資料不符規格
    """
    return ProductsModel.model_validate(data)


def validate_rules(data: dict[str, Any]) -> ProductRulesModel:
    """
    驗證規則 JSON dict，回傳 ProductRulesModel。

    Raises:
        pydantic.ValidationError: 資料不符規格
    """
    return ProductRulesModel.model_validate(data)
