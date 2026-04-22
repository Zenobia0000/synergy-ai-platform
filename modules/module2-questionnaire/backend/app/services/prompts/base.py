"""
prompts 套件共用基礎模組。

提供：
    PromptContext    — frozen dataclass，封裝 prompt 建構所需的上下文資訊
    build_field_label_map — 從 questionnaire.json 建立 field_id → label 映射
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# PromptContext
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromptContext:
    """
    Prompt 建構上下文（不可變）。

    Attributes
    ----------
    questionnaire_labels:
        field_id → 中文 label 的映射，用於將問卷欄位 ID 轉為可讀名稱。
    coach_level:
        教練等級，"new" 或 "experienced"，影響話術詳細程度。
    locale:
        回應語系，如 "zh-TW" 或 "en"。
    """

    questionnaire_labels: dict[str, str]
    coach_level: str
    locale: str


# ---------------------------------------------------------------------------
# build_field_label_map
# ---------------------------------------------------------------------------


def build_field_label_map(questionnaire_path: Path) -> dict[str, str]:
    """
    從 questionnaire.json 建立 field_id → label 映射。

    遍歷所有 sections 的 fields，提取每個欄位的 field_id 與 label，
    供 prompt 組裝時將技術 ID 轉換為使用者可讀的中文名稱。

    Parameters
    ----------
    questionnaire_path:
        questionnaire.json 的絕對路徑。

    Returns
    -------
    dict[str, str]
        {field_id: label} 映射，如 {"gender": "性別", "age": "年齡", ...}

    Raises
    ------
    FileNotFoundError
        若 questionnaire.json 不存在。
    KeyError
        若 JSON 結構不符合預期。
    """
    raw: dict[str, Any] = json.loads(questionnaire_path.read_text(encoding="utf-8"))
    label_map: dict[str, str] = {}

    for section in raw.get("sections", []):
        for field in section.get("fields", []):
            field_id: str = field["field_id"]
            label: str = field["label"]
            label_map[field_id] = label

    return label_map
