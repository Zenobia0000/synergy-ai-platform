"""
問卷解析器測試（階段 2 GREEN）。

階段 2：實際斷言，驗收條件為全部 PASS。
"""

from __future__ import annotations

from pathlib import Path

from app.services.parsers.questionnaire import parse_questionnaire_xlsx

# rawdata 路徑（相對本測試檔往上三層至專案根，再進 rawdata/）
RAWDATA_DIR = Path(__file__).parents[4] / "rawdata"
QUESTIONNAIRE_XLSX = RAWDATA_DIR / "諮詢問卷_含產品建議.xlsx"


def test_parse_returns_schema_with_meta() -> None:
    """parse_questionnaire_xlsx 回傳的物件必須含有正確 _meta 欄位。"""
    result = parse_questionnaire_xlsx(QUESTIONNAIRE_XLSX)
    assert result._meta is not None, "_meta 欄位不得為 None"
    assert result._meta.source_file == "諮詢問卷_含產品建議.xlsx", (
        f"source_file 應為 '諮詢問卷_含產品建議.xlsx'，實際為 {result._meta.source_file!r}"
    )
    assert result._meta.source_sha256 != "", "source_sha256 不得為空字串"
    assert result._meta.generated_at != "", "generated_at 不得為空字串"
    assert result._meta.parser_version == "0.1.0", (
        f"parser_version 應為 '0.1.0'，實際為 {result._meta.parser_version!r}"
    )


def test_parse_returns_at_least_five_sections() -> None:
    """問卷至少應有 5 個區段（對應問卷各大主題）。"""
    result = parse_questionnaire_xlsx(QUESTIONNAIRE_XLSX)
    assert len(result.sections) >= 5, (
        f"預期至少 5 個 section，實際得到 {len(result.sections)} 個"
    )


def test_all_fields_have_unique_field_id() -> None:
    """所有欄位的 field_id 必須唯一，不得重複。"""
    result = parse_questionnaire_xlsx(QUESTIONNAIRE_XLSX)
    all_field_ids = [
        field.field_id
        for section in result.sections
        for field in section.fields
    ]
    unique_ids = set(all_field_ids)
    assert len(all_field_ids) == len(unique_ids), (
        f"發現重複 field_id：{[fid for fid in all_field_ids if all_field_ids.count(fid) > 1]}"
    )


def test_gender_field_has_expected_options() -> None:
    """gender 欄位必須存在，且選項含「男」與「女」。"""
    result = parse_questionnaire_xlsx(QUESTIONNAIRE_XLSX)
    all_fields = [
        field
        for section in result.sections
        for field in section.fields
    ]
    gender_fields = [f for f in all_fields if f.field_id == "gender"]
    assert len(gender_fields) == 1, "應有且僅有一個 field_id == 'gender' 的欄位"
    gender_field = gender_fields[0]
    assert gender_field.options is not None, "gender 欄位 options 不得為 None"
    option_labels = {opt.label for opt in gender_field.options}
    assert "男" in option_labels, f"gender 選項應含「男」，實際：{option_labels}"
    assert "女" in option_labels, f"gender 選項應含「女」，實際：{option_labels}"


def test_weight_field_is_number_type() -> None:
    """current_weight_kg 欄位必須存在且 type 為 number。"""
    result = parse_questionnaire_xlsx(QUESTIONNAIRE_XLSX)
    all_fields = [
        field
        for section in result.sections
        for field in section.fields
    ]
    weight_fields = [f for f in all_fields if f.field_id == "current_weight_kg"]
    assert len(weight_fields) == 1, (
        "應有且僅有一個 field_id == 'current_weight_kg' 的欄位"
    )
    weight_field = weight_fields[0]
    assert weight_field.type == "number", (
        f"current_weight_kg 的 type 應為 'number'，實際為 {weight_field.type!r}"
    )
