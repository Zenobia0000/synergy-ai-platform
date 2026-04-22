"""
問卷 xlsx 解析器。

主要函式：parse_questionnaire_xlsx
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

from .types import (
    Field,
    FieldCondition,
    FieldOption,
    Meta,
    QuestionnaireSchema,
    Section,
)

logger = logging.getLogger(__name__)

PARSER_VERSION = "0.1.0"

# 區段名稱 → 英數 slug（固定映射表，涵蓋 xlsx 實際所有區段）
_SECTION_SLUG_MAP: dict[str, str] = {
    "基本資料": "basic_info",
    "健康目標": "health_goals",
    "壓力": "stress",
    "睡眠": "sleep",
    "消化": "digestion",
    "循環": "circulation",
    "水分代謝": "fluid_metabolism",
    "體態感受": "body_composition",
    "排便": "bowel",
    "飲食": "diet",
    "水分": "hydration",
    "習慣": "habits",
    "活動量": "activity",
    "醫療紀錄": "medical_history",
    "補充資訊": "additional_info",
    "同意": "consent",
}

# 題型映射：中文 → 英文類型字串
_TYPE_MAP: dict[str, str] = {
    "單選": "single_choice",
    "多選": "multi_choice",
    "核取方塊": "multi_choice",
    "簡答": "text",
    "段落": "textarea",
    "長答": "textarea",
    "數值": "number",
    "數字": "number",
    "日期": "date",
    "量表": "scale",
}

# PII 欄位 field_id 集合
_PII_FIELD_IDS: frozenset[str] = frozenset({
    "name", "phone", "email", "mobile", "birthday",
    "address", "id_number", "referrer",
})

# 選項分隔符正則（中文頓號、全形豎線、半形豎線、逗號）
_OPTION_SPLIT_RE = re.compile(r"[、｜|,\n]")

# 條件解析正則：`若 <field_id> == <value>` 或 `若 <field_id> >= <n>`
_CONDITION_RE = re.compile(
    r"若\s*(?P<field_id>\w+)\s*(?P<op>[><=!]+)\s*(?P<value>.+)"
)

# 條件包含語法：`<field_id> 包含「<value>」` 或 `<field_id> = <value>`
_CONDITION_CONTAINS_RE = re.compile(
    r"(?P<field_id>\w+)\s*包含[「「](?P<value>[^」」]+)[」」]"
)
_CONDITION_EQ_RE = re.compile(
    r"(?P<field_id>\w+)\s*=\s*(?P<value>.+)"
)

# 單位推測正則（從 label 擷取括號內單位，例：「目前體重（kg）」→ kg）
_UNIT_RE = re.compile(r"[（(](?P<unit>[a-zA-Z%/㎝]+)[)）]")


def _sha256_file(path: Path) -> str:
    """計算檔案 SHA256 hex digest。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _section_slug(section_name: str) -> str:
    """將區段中文名稱轉換為英數 slug。"""
    slug = _SECTION_SLUG_MAP.get(section_name)
    if slug is None:
        logger.warning("未知區段名稱 %r，使用 fallback slug", section_name)
        slug = re.sub(r"[^\w]", "_", section_name.strip()).lower() or "unknown"
    return slug


def _map_field_type(raw_type: str) -> str:
    """將中文題型映射為英文類型字串。"""
    mapped = _TYPE_MAP.get(raw_type)
    if mapped is None:
        logger.warning("未知欄位類型 %r，fallback 為 text", raw_type)
        return "text"
    return mapped


def _parse_options(raw_options: str) -> tuple[FieldOption, ...]:
    """解析選項字串，回傳 FieldOption tuple。"""
    parts = _OPTION_SPLIT_RE.split(raw_options)
    options: list[FieldOption] = []
    for part in parts:
        label = part.strip()
        if not label:
            continue
        # value 使用中文原文（專案簡化決策）
        options.append(FieldOption(value=label, label=label))
    return tuple(options)


def _parse_condition(raw: str) -> FieldCondition | None:
    """
    簡易 DSL 解析條件顯示欄位。

    支援：
    - `若 <field_id> == <value>`
    - `若 <field_id> >= <n>`
    - `<field_id> 包含「<value>」`
    - `<field_id> = <value>`
    無法解析回傳 None（condition 設 None，原文保留在 help_text）。
    """
    raw = raw.strip()

    # 若 field_id op value
    m = _CONDITION_RE.match(raw)
    if m:
        return FieldCondition(
            field_id=m.group("field_id"),
            op=m.group("op"),
            value=m.group("value").strip(),
        )

    # field_id 包含「value」
    m = _CONDITION_CONTAINS_RE.search(raw)
    if m:
        return FieldCondition(
            field_id=m.group("field_id"),
            op="contains",
            value=m.group("value").strip(),
        )

    # field_id = value
    m = _CONDITION_EQ_RE.match(raw)
    if m:
        return FieldCondition(
            field_id=m.group("field_id"),
            op="==",
            value=m.group("value").strip(),
        )

    logger.debug("無法解析條件顯示 DSL：%r，設為 None", raw)
    return None


def _infer_number_meta(
    label: str, help_text: str | None
) -> tuple[float | None, float | None, str | None]:
    """從 label 與 help_text 推斷 number 欄位的 min / max / unit。"""
    unit_match = _UNIT_RE.search(label)
    unit = unit_match.group("unit") if unit_match else None
    return None, None, unit


def _parse_required(raw: str | None) -> bool:
    """解析是否必填欄位。"""
    if raw is None:
        return False
    return raw.strip().lower() in {"是", "y", "true", "yes"}


def _build_field(row: tuple, order: int) -> Field | None:
    """從 xlsx 單列資料建立 Field 物件。"""
    _, _, label, field_id, raw_type, required_raw, options_raw, default, help_text, condition_raw, _ = row

    if not field_id or not label:
        return None

    field_type = _map_field_type(raw_type or "簡答")
    required = _parse_required(required_raw)

    options: tuple[FieldOption, ...] | None = None
    if options_raw and str(options_raw).strip():
        options = _parse_options(str(options_raw))

    condition: FieldCondition | None = None
    if condition_raw and str(condition_raw).strip():
        condition = _parse_condition(str(condition_raw))

    pii = str(field_id).strip() in _PII_FIELD_IDS

    min_val: float | None = None
    max_val: float | None = None
    unit: str | None = None
    if field_type == "number" or (
        field_type == "text" and help_text and "限制數字" in str(help_text)
    ):
        field_type = "number"
        min_val, max_val, unit = _infer_number_meta(
            str(label), str(help_text) if help_text else None
        )

    return Field(
        field_id=str(field_id).strip(),
        label=str(label).strip(),
        type=field_type,
        required=required,
        options=options,
        default=str(default).strip() if default is not None else None,
        help_text=str(help_text).strip() if help_text else None,
        condition=condition,
        pii=pii,
        order=order,
        min=min_val,
        max=max_val,
        unit=unit,
    )


def parse_questionnaire_xlsx(path: Path) -> QuestionnaireSchema:
    """
    解析問卷 xlsx 檔案，回傳標準化 QuestionnaireSchema。

    Args:
        path: 問卷 xlsx 檔案路徑（例：rawdata/諮詢問卷_含產品建議.xlsx）

    Returns:
        QuestionnaireSchema frozen dataclass 實例

    Raises:
        FileNotFoundError: 檔案不存在
        ValueError: 檔案格式不符預期
    """
    if not path.exists():
        raise FileNotFoundError(f"問卷 xlsx 不存在：{path}")

    sha256 = _sha256_file(path)
    generated_at = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()

    meta = Meta(
        source_file="諮詢問卷_含產品建議.xlsx",
        source_sha256=sha256,
        generated_at=generated_at,
        parser_version=PARSER_VERSION,
    )

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    # 依區段分組 fields
    sections_map: dict[str, list[Field]] = {}
    section_order: list[str] = []
    field_order_counter: dict[str, int] = {}

    for row in ws.iter_rows(min_row=2, max_col=11, values_only=True):
        if not any(c is not None for c in row):
            continue

        section_name = str(row[1]).strip() if row[1] else ""
        if not section_name:
            continue

        if section_name not in sections_map:
            sections_map[section_name] = []
            section_order.append(section_name)
            field_order_counter[section_name] = 0

        field_order_counter[section_name] += 1
        field = _build_field(row, field_order_counter[section_name])
        if field is not None:
            sections_map[section_name].append(field)

    wb.close()

    sections = tuple(
        Section(
            id=_section_slug(name),
            title=name,
            order=idx + 1,
            fields=tuple(sections_map[name]),
        )
        for idx, name in enumerate(section_order)
    )

    return QuestionnaireSchema(
        _meta=meta,
        version="1.0.0",
        title="Synergy 全心健康計畫初次評估問卷",
        sections=sections,
    )
