"""
產品規則解析器。

主要函式：parse_product_rules
"""

from __future__ import annotations

import difflib
import hashlib
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import openpyxl

from .types import Meta, ProductRules, ProductsSchema, Rule, RuleTrigger, UnmatchedRuleProduct

logger = logging.getLogger(__name__)

PARSER_VERSION = "0.1.0"

# 產品名分隔（以條件指示符切割每段，再切割同段產品名）
_COND_SEP_RE = re.compile(r"\n")
_PRODUCT_SEP_RE = re.compile(r"[、，,、；;]+")

# 移除括號英文名（保留中文主名用於匹配）
_BRACKET_RE = re.compile(r"[（(][^)）]*[)）]")
_TRAILING_RE = re.compile(r"[-\s→【】]+$")
_LEADING_RE = re.compile(r"^[\s→【】]+")


def _sha256_file(path: Path) -> str:
    """計算檔案 SHA256 hex digest。"""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_name(name: str) -> str:
    """NFKC 正規化 + 去括號 + 去尾端符號。"""
    name = unicodedata.normalize("NFKC", name)
    name = _BRACKET_RE.sub("", name)
    name = _TRAILING_RE.sub("", name.strip())
    name = _LEADING_RE.sub("", name.strip())
    return name.strip()


_ASCII_CHARS_RE = re.compile(r"[A-Za-z0-9+\-]+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_cn_only(name: str) -> str:
    """僅保留中文字元，用於 fuzzy 匹配。"""
    norm = _normalize_name(name)
    norm = _ASCII_CHARS_RE.sub("", norm)
    norm = _WHITESPACE_RE.sub("", norm)
    return norm.strip()


def _build_reverse_map(
    products: ProductsSchema,
) -> dict[str, tuple[str, str, str]]:
    """
    建立產品名 → (sku, normalized_name, cn_only) 反向查找表。
    包含原始名、正規化名、中文名三種鍵。
    """
    result: dict[str, tuple[str, str, str]] = {}
    for p in products.products:
        norm = _normalize_name(p.name)
        cn = _normalize_cn_only(p.name)
        result[p.name] = (p.sku, norm, cn)
        if norm not in result:
            result[norm] = (p.sku, norm, cn)
    return result


FUZZY_THRESHOLD = 0.85


def _lookup_sku(
    raw_name: str,
    reverse_map: dict[str, tuple[str, str, str]],
) -> str | None:
    """
    四層 SKU 匹配，回傳 sku 或 None。

    1. 精確匹配
    2. NFKC 正規化匹配
    3. 中文子字串包含（雙向）
    4. fuzzy CN 匹配 >= 0.85
    """
    # 第一層：精確匹配
    if raw_name in reverse_map:
        return reverse_map[raw_name][0]

    norm = _normalize_name(raw_name)

    # 第二層：正規化後精確匹配
    for _key, (sku, key_norm, _cn) in reverse_map.items():
        if key_norm == norm:
            return sku

    cn_query = _normalize_cn_only(raw_name)

    # 第三層：中文子字串雙向包含（至少 2 字）
    if len(cn_query) >= 2:
        for _key, (sku, _kn, key_cn) in reverse_map.items():
            if cn_query in key_cn or (len(key_cn) >= 2 and key_cn in cn_query):
                return sku

    # 第四層：fuzzy CN 匹配
    best_ratio = 0.0
    best_sku: str | None = None
    for _key, (sku, _kn, key_cn) in reverse_map.items():
        if not key_cn:
            continue
        ratio = difflib.SequenceMatcher(None, cn_query, key_cn).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_sku = sku

    if best_ratio >= FUZZY_THRESHOLD:
        return best_sku

    return None


def _extract_product_names_from_segment(segment: str) -> list[str]:
    """
    從一個片段（可能包含「條件 → 產品名, 產品名」）中抽取產品名清單。
    去掉條件描述部分（箭號之前）。
    """
    # 若含箭號，取箭號後的部分
    if "→" in segment:
        segment = segment.split("→", 1)[1]
    elif "→" in segment:
        segment = segment.split("→", 1)[1]

    # 去分號分隔的多段（例：A；B → C 的分號）
    # 此處只處理箭號後的產品清單
    raw_parts = _PRODUCT_SEP_RE.split(segment)
    names: list[str] = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        # 去尾端括號說明（優先）後清理
        clean = _LEADING_RE.sub("", part)
        clean = _TRAILING_RE.sub("", clean).strip()
        if clean:
            names.append(clean)
    return names


def _parse_k_column_text(
    text: str,
    field_id: str,
    source_row: int,
    reverse_map: dict[str, tuple[str, str, str]],
    unmatched_list: list[UnmatchedRuleProduct],
) -> list[Rule]:
    """
    解析 K 欄文字，產出 0..N 條 Rule。

    格式（資料實況）：
    - 「條件描述 → 產品A、產品B\\n條件描述 → 產品C」
    - 「純產品名清單」（無條件，代表「答了就建議」）
    """
    rules: list[Rule] = []
    segments = _COND_SEP_RE.split(text)

    for idx, segment in enumerate(segments):
        segment = segment.strip()
        if not segment:
            continue

        product_names = _extract_product_names_from_segment(segment)
        if not product_names:
            continue

        # 建立 trigger（無條件規則）
        trigger = RuleTrigger(
            logic="and",
            conditions=(),
        )

        matched_skus: list[str] = []
        for pname in product_names:
            sku = _lookup_sku(pname, reverse_map)
            if sku:
                matched_skus.append(sku)
            else:
                logger.warning(
                    "規則 source_row=%d 產品名 %r 找不到 SKU",
                    source_row,
                    pname,
                )
                unmatched_list.append(
                    UnmatchedRuleProduct(
                        name_in_xlsx=pname,
                        source_row=source_row,
                    )
                )

        if not matched_skus:
            logger.warning(
                "source_row=%d 段落 %r 無有效 SKU，略過此條規則",
                source_row,
                segment[:80],
            )
            continue

        rule_id = f"rule_{source_row:03d}_{idx}"
        rules.append(
            Rule(
                id=rule_id,
                trigger=trigger,
                recommended_skus=tuple(dict.fromkeys(matched_skus)),
                reason_raw=segment,
                source_row=source_row,
            )
        )

    return rules


def parse_product_rules(xlsx_path: Path, products: ProductsSchema) -> ProductRules:
    """
    解析產品規則 xlsx，回傳標準化 ProductRules。

    Args:
        xlsx_path: 含產品建議欄位的問卷 xlsx 路徑（K 欄為產品使用建議）
        products: 已解析的 ProductsSchema（供 SKU 對應用）

    Returns:
        ProductRules frozen dataclass 實例

    Raises:
        FileNotFoundError: 檔案不存在
        ValueError: 檔案格式不符預期
    """
    if not xlsx_path.exists():
        raise FileNotFoundError(f"規則 xlsx 不存在：{xlsx_path}")

    sha256 = _sha256_file(xlsx_path)
    generated_at = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()

    meta = Meta(
        source_file="諮詢問卷_含產品建議.xlsx",
        source_sha256=sha256,
        generated_at=generated_at,
        parser_version=PARSER_VERSION,
    )

    reverse_map = _build_reverse_map(products)

    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    all_rules: list[Rule] = []
    all_unmatched: list[UnmatchedRuleProduct] = []

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        # D 欄（index 3）= field_id；K 欄（index 10）= 產品使用建議
        field_id = row[3] if len(row) > 3 else None
        k_cell = row[10] if len(row) > 10 else None

        if not k_cell:
            continue

        k_text = str(k_cell).strip()
        if not k_text:
            continue

        rules = _parse_k_column_text(
            text=k_text,
            field_id=str(field_id) if field_id else "unknown",
            source_row=row_idx,
            reverse_map=reverse_map,
            unmatched_list=all_unmatched,
        )
        all_rules.extend(rules)

    wb.close()

    return ProductRules(
        _meta=meta,
        rules=tuple(all_rules),
        unmatched_rule_products=tuple(all_unmatched),
    )
