"""
一致性驗證測試。

測試 compare_sources() 與 write_consistency_report() 函式的正確性。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.services.parsers.apps_script import parse_apps_script_docx
from app.services.parsers.consistency import compare_sources, write_consistency_report
from app.services.parsers.questionnaire import parse_questionnaire_xlsx

RAWDATA_DIR = Path(__file__).parents[4] / "rawdata"
QUESTIONNAIRE_WITH_RULES_XLSX = RAWDATA_DIR / "諮詢問卷_含產品建議.xlsx"
APPS_SCRIPT_DOCX = RAWDATA_DIR / "App Script-全心健康計畫｜初次健康評估問卷.docx"


def test_compare_returns_coverage_ratio() -> None:
    """compare_sources 應回傳 coverage_ratio 為 float，範圍 0~1。"""
    questionnaire = parse_questionnaire_xlsx(QUESTIONNAIRE_WITH_RULES_XLSX)
    titles = parse_apps_script_docx(APPS_SCRIPT_DOCX)
    report = compare_sources(questionnaire, titles)

    assert "coverage_ratio" in report, "report 應包含 coverage_ratio"
    ratio = report["coverage_ratio"]
    assert isinstance(ratio, float), f"coverage_ratio 應為 float，實際為 {type(ratio)}"
    assert 0.0 <= ratio <= 1.0, f"coverage_ratio 應介於 0~1，實際為 {ratio}"


def test_coverage_at_least_50_percent() -> None:
    """主版本問卷被 Apps Script 涵蓋率應 >= 50%。"""
    questionnaire = parse_questionnaire_xlsx(QUESTIONNAIRE_WITH_RULES_XLSX)
    titles = parse_apps_script_docx(APPS_SCRIPT_DOCX)
    report = compare_sources(questionnaire, titles)

    ratio = report["coverage_ratio"]
    assert ratio >= 0.50, (
        f"涵蓋率應 >= 50%，實際為 {ratio:.1%}。"
        f"xlsx 獨有：{report['xlsx_only'][:5]}"
    )


def test_write_consistency_report_creates_file() -> None:
    """write_consistency_report 應建立含覆蓋率百分比的 Markdown 檔案。"""
    questionnaire = parse_questionnaire_xlsx(QUESTIONNAIRE_WITH_RULES_XLSX)
    titles = parse_apps_script_docx(APPS_SCRIPT_DOCX)
    report = compare_sources(questionnaire, titles)

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "subdir" / "_consistency_report.md"
        write_consistency_report(report, output_path)

        assert output_path.exists(), "報告檔案應存在"
        content = output_path.read_text(encoding="utf-8")
        assert "%" in content, "報告應包含百分比數值"
        assert "coverage_ratio" not in content, "報告不應直接暴露 key 名稱"
        assert "涵蓋率" in content or "交集" in content, "報告應包含涵蓋率相關文字"


def test_write_consistency_report_with_empty_intersection() -> None:
    """當交集為空時，報告應顯示「（無）」。"""
    # 建構完全不重疊的報告資料
    report = {
        "xlsx_count": 5,
        "as_count": 3,
        "intersection_count": 0,
        "coverage_ratio": 0.0,
        "xlsx_only": ["欄位A", "欄位B"],
        "as_only": [],
        "generated_at": "2026-04-21T00:00:00+08:00",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "_consistency_report.md"
        write_consistency_report(report, output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "（無）" in content, "AS 獨有為空時應顯示（無）"
        assert "欄位A" in content, "xlsx 獨有欄位應出現在報告中"
