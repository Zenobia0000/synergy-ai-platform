"""
Parser 型別定義。

所有資料型別以 frozen dataclass（slots=True）定義，確保不可變性。
選用 dataclass 而非 TypedDict 以獲得更嚴格的型別檢查與不可變保護。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# 共用基礎型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Meta:
    """每份輸出 JSON 的 _meta 欄位，記錄來源與版本資訊。"""

    source_file: str
    source_sha256: str
    generated_at: str  # ISO-8601 字串，含時區
    parser_version: str


# ---------------------------------------------------------------------------
# 問卷 schema 型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FieldOption:
    """單選 / 多選題的選項。"""

    value: str
    label: str


@dataclass(frozen=True, slots=True)
class FieldCondition:
    """條件顯示規則（當某欄位滿足條件時才顯示本欄位）。"""

    field_id: str
    op: str   # "==", "!=", ">=", "<=", ">", "<"
    value: str


@dataclass(frozen=True, slots=True)
class Field:
    """問卷中的單一欄位。"""

    field_id: str
    label: str
    type: str  # single_choice / multi_choice / text / textarea / number / date / scale
    required: bool
    options: tuple[FieldOption, ...] | None
    default: str | None
    help_text: str | None
    condition: FieldCondition | None
    pii: bool
    order: int
    min: float | None
    max: float | None
    unit: str | None


@dataclass(frozen=True, slots=True)
class Section:
    """問卷區段，含多個欄位。"""

    id: str
    title: str
    order: int
    fields: tuple[Field, ...]


@dataclass(frozen=True, slots=True)
class QuestionnaireSchema:
    """問卷 schema 根節點。"""

    _meta: Meta
    version: str
    title: str
    sections: tuple[Section, ...]


# ---------------------------------------------------------------------------
# 產品 schema 型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Product:
    """單一產品資料。"""

    sku: str
    name: str
    category: str
    scenario: tuple[str, ...]
    price: int | None
    price_display: str
    bundle_contents: str | None
    usage_note: str
    image_url: str | None
    image_match_confidence: float | None


@dataclass(frozen=True, slots=True)
class UnmatchedImage:
    """無法對應產品的圖片連結記錄。"""

    name_in_docx: str
    url: str
    candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductsSchema:
    """產品 schema 根節點。"""

    _meta: Meta
    products: tuple[Product, ...]
    unmatched_images: tuple[UnmatchedImage, ...]


# ---------------------------------------------------------------------------
# 產品規則 schema 型別
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RuleCondition:
    """規則觸發條件的單一子條件。"""

    field_id: str
    op: str  # "==", "!=", ">=", "<=", ">", "<"
    value: str


@dataclass(frozen=True, slots=True)
class RuleTrigger:
    """規則觸發條件組合（and / or）。"""

    logic: Literal["and", "or"]
    conditions: tuple[RuleCondition, ...]


@dataclass(frozen=True, slots=True)
class Rule:
    """單一產品建議規則。"""

    id: str
    trigger: RuleTrigger
    recommended_skus: tuple[str, ...]
    reason_raw: str
    source_row: int


@dataclass(frozen=True, slots=True)
class UnmatchedRuleProduct:
    """規則中找不到對應 SKU 的產品名稱記錄。"""

    name_in_xlsx: str
    source_row: int


@dataclass(frozen=True, slots=True)
class ProductRules:
    """產品規則 schema 根節點。"""

    _meta: Meta
    rules: tuple[Rule, ...]
    unmatched_rule_products: tuple[UnmatchedRuleProduct, ...]
