"""
Apps Script docx 解析器測試。

階段 3：實際斷言，驗收條件為全部 PASS。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.parsers.apps_script import parse_apps_script_docx

# rawdata 路徑（含全形 ｜ 字元，用 pathlib 處理）
RAWDATA_DIR = Path(__file__).parents[4] / "rawdata"
APPS_SCRIPT_DOCX = RAWDATA_DIR / "App Script-全心健康計畫｜初次健康評估問卷.docx"


def test_parse_returns_non_empty_title_list() -> None:
    """Apps Script docx 解析後應回傳至少 10 個題目標題（tuple）。"""
    result = parse_apps_script_docx(APPS_SCRIPT_DOCX)
    assert isinstance(result, tuple), f"預期回傳 tuple，實際為 {type(result)}"
    assert len(result) >= 10, f"題目標題應至少 10 個，實際得到 {len(result)} 個"
    for title in result:
        assert isinstance(title, str) and title.strip() != "", (
            f"標題 {title!r} 不得為空字串"
        )


def test_titles_contain_gender_or_age() -> None:
    """解析結果應包含常見題目（性別或年齡相關）。"""
    result = parse_apps_script_docx(APPS_SCRIPT_DOCX)
    # 找常見關鍵字
    keywords = ("性別", "年齡", "姓名", "填寫日期", "身高", "體重")
    found = any(
        any(kw in title for kw in keywords) for title in result
    )
    assert found, (
        f"結果應包含 {keywords} 之一的題目，實際標題集合：{result[:10]}"
    )


def test_file_not_found_raises() -> None:
    """不存在的檔案應引發 FileNotFoundError。"""
    with pytest.raises(FileNotFoundError, match="不存在"):
        parse_apps_script_docx(Path("/nonexistent/path.docx"))


# ---------------------------------------------------------------------------
# 補強覆蓋率：mock docx.Document 測試內部路徑
# ---------------------------------------------------------------------------

class _MockParagraph:
    """最小 paragraph stub。"""
    def __init__(self, text: str) -> None:
        self.text = text


class _MockCell:
    def __init__(self, paragraphs: list[_MockParagraph]) -> None:
        self.paragraphs = paragraphs


class _MockRow:
    def __init__(self, cells: list[_MockCell]) -> None:
        self.cells = cells


class _MockTable:
    def __init__(self, rows: list[_MockRow]) -> None:
        self.rows = rows


class _MockDocument:
    def __init__(self, paragraphs: list[_MockParagraph], tables: list[_MockTable]) -> None:
        self.paragraphs = paragraphs
        self.tables = tables


def _make_temp_docx(tmp_path: Path) -> Path:
    """建立最小的真實 docx 占位檔（用於 path.exists() 通過），內容由 mock 覆蓋。"""
    # 我們需要一個存在的路徑；實際解析由 monkeypatch 攔截
    p = tmp_path / "fake.docx"
    p.write_bytes(b"PK\x03\x04")  # zip magic bytes（docx 是 zip）
    return p


def test_empty_document_raises_value_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """docx 內容完全空白 → 引發 ValueError。"""
    fake_path = _make_temp_docx(tmp_path)
    mock_doc = _MockDocument(
        paragraphs=[_MockParagraph("")],
        tables=[],
    )
    monkeypatch.setattr(
        "app.services.parsers.apps_script.Document",
        lambda path: mock_doc,
    )
    with pytest.raises(ValueError, match="內容為空"):
        parse_apps_script_docx(fake_path)


def test_table_cells_included_in_extraction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """表格 cell 中的 setTitle 也應被抽取。"""
    fake_path = _make_temp_docx(tmp_path)
    table_para = _MockParagraph(".setTitle('表格題目一')")
    mock_doc = _MockDocument(
        paragraphs=[_MockParagraph("// some code")],
        tables=[
            _MockTable([_MockRow([_MockCell([table_para])])])
        ],
    )
    monkeypatch.setattr(
        "app.services.parsers.apps_script.Document",
        lambda path: mock_doc,
    )
    result = parse_apps_script_docx(fake_path)
    assert "表格題目一" in result


def test_empty_title_in_set_title_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """setTitle('') 空標題應被過濾，不出現在結果中。"""
    fake_path = _make_temp_docx(tmp_path)
    mock_doc = _MockDocument(
        paragraphs=[
            _MockParagraph(".setTitle('')"),
            _MockParagraph(".setTitle('  ')"),
            _MockParagraph(".setTitle('有效題目')"),
        ],
        tables=[],
    )
    monkeypatch.setattr(
        "app.services.parsers.apps_script.Document",
        lambda path: mock_doc,
    )
    result = parse_apps_script_docx(fake_path)
    # 空白標題不應出現
    assert "" not in result
    assert "  " not in result
    # 有效題目應在
    assert "有效題目" in result


def test_deduplication_preserves_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """重複的標題只保留第一次出現，順序維持。"""
    fake_path = _make_temp_docx(tmp_path)
    mock_doc = _MockDocument(
        paragraphs=[
            _MockParagraph(".setTitle('第一題')"),
            _MockParagraph(".setTitle('第二題')"),
            _MockParagraph(".setTitle('第一題')"),  # 重複
        ],
        tables=[],
    )
    monkeypatch.setattr(
        "app.services.parsers.apps_script.Document",
        lambda path: mock_doc,
    )
    result = parse_apps_script_docx(fake_path)
    assert result == ("第一題", "第二題")
    assert len(result) == 2
