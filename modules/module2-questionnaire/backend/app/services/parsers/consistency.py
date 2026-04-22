"""
問卷一致性驗證模組。

比較主版本問卷（xlsx）與 Apps Script docx 的題目標題，產出一致性報告。
比對策略：先精確，再去括號/單位的正規化比對（NFKC + 去括號）。
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .types import QuestionnaireSchema

_BRACKET_RE = re.compile(r"[（(][^)）]*[)）]")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_label(label: str) -> str:
    """NFKC 正規化 + 去括號（含單位）+ 壓縮空白。"""
    label = unicodedata.normalize("NFKC", label)
    label = _BRACKET_RE.sub("", label)
    label = _WHITESPACE_RE.sub("", label)
    return label.strip()


def _extract_xlsx_labels(questionnaire: QuestionnaireSchema) -> set[str]:
    """從問卷 schema 抽取所有欄位 label 集合。"""
    labels: set[str] = set()
    for section in questionnaire.sections:
        for field in section.fields:
            if field.label and field.label.strip():
                labels.add(field.label.strip())
    return labels


def compare_sources(
    questionnaire: QuestionnaireSchema,
    apps_script_titles: tuple[str, ...],
) -> dict:
    """
    比較主版本問卷 xlsx 與 Apps Script docx 的題目標題集合。

    比對策略（兩層）：
    1. 精確字串比對
    2. 正規化後（NFKC + 去括號/單位）比對

    Args:
        questionnaire: 已解析的問卷 schema
        apps_script_titles: Apps Script docx 抽出的題目標題 tuple

    Returns:
        dict，含以下欄位：
        - xlsx_count: 主版本欄位總數
        - as_count: Apps Script 題目總數
        - intersection_count: 交集數（含正規化匹配）
        - coverage_ratio: 主版本被 Apps Script 涵蓋的比率 (float 0-1)
        - xlsx_only: 主版本獨有的標題 list（精確 + 正規化後仍不匹配）
        - as_only: Apps Script 獨有的標題 list
        - generated_at: ISO-8601 時間戳
    """
    xlsx_labels = _extract_xlsx_labels(questionnaire)
    as_set = set(apps_script_titles)

    # 建立正規化反查表
    norm_xlsx: dict[str, str] = {_normalize_label(l): l for l in xlsx_labels}
    norm_as: dict[str, str] = {_normalize_label(t): t for t in as_set}

    norm_xlsx_keys = set(norm_xlsx.keys())
    norm_as_keys = set(norm_as.keys())

    # 交集（正規化後）
    norm_intersection = norm_xlsx_keys & norm_as_keys
    coverage_ratio = len(norm_intersection) / len(xlsx_labels) if xlsx_labels else 0.0

    # 找出 xlsx 獨有（正規化後仍未出現於 AS）
    norm_xlsx_only_keys = norm_xlsx_keys - norm_as_keys
    xlsx_only = sorted(norm_xlsx[k] for k in norm_xlsx_only_keys)

    # 找出 AS 獨有
    norm_as_only_keys = norm_as_keys - norm_xlsx_keys
    as_only = sorted(norm_as[k] for k in norm_as_only_keys)

    generated_at = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()

    return {
        "xlsx_count": len(xlsx_labels),
        "as_count": len(as_set),
        "intersection_count": len(norm_intersection),
        "coverage_ratio": round(coverage_ratio, 4),
        "xlsx_only": xlsx_only,
        "as_only": as_only,
        "generated_at": generated_at,
    }


def write_consistency_report(report: dict, output_path: Path) -> None:
    """
    將一致性報告寫成 Markdown 檔案。

    Args:
        report: compare_sources() 回傳的 dict
        output_path: 輸出 markdown 路徑
    """
    coverage_pct = report["coverage_ratio"] * 100
    lines: list[str] = [
        "# 問卷一致性報告",
        "",
        f"產生時間：{report['generated_at']}",
        "",
        "## 概要",
        "",
        "| 指標 | 數值 |",
        "|------|------|",
        f"| 主版本欄位總數（xlsx） | {report['xlsx_count']} |",
        f"| Apps Script 題目總數 | {report['as_count']} |",
        f"| 交集數（含正規化比對） | {report['intersection_count']} |",
        f"| 主版本被 AS 涵蓋率 | {coverage_pct:.1f}% |",
        "",
        "## 差異詳情",
        "",
        "### 主版本獨有（xlsx 有、Apps Script 無）",
        "",
    ]

    if report["xlsx_only"]:
        for item in report["xlsx_only"]:
            lines.append(f"- {item}")
    else:
        lines.append("（無）")

    lines.extend([
        "",
        "### Apps Script 獨有（Apps Script 有、xlsx 無）",
        "",
    ])

    if report["as_only"]:
        for item in report["as_only"]:
            lines.append(f"- {item}")
    else:
        lines.append("（無）")

    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
