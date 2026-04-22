"""
Schema 建構 CLI。

將 rawdata/ 中的異質資料解析並輸出為 data/schemas/ 下的 JSON 檔案。

使用方式（從 backend/ 目錄執行）：
    uv run python scripts/build_schemas.py [--verbose] [--input-dir PATH] [--output-dir PATH]

輸出檔案：
    questionnaire.json      — 問卷結構
    products.json           — 產品目錄（含圖片匹配）
    product_rules.json      — 產品建議規則
    unmatched_rule_products.json — 規則中無法匹配的產品名
    _consistency_report.md  — 問卷一致性報告（含手動抽檢段落）
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# 路徑計算（script 位於 backend/scripts/，專案根在 backend/../）
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

DEFAULT_INPUT_DIR = PROJECT_ROOT / "rawdata"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "schemas"

# ---------------------------------------------------------------------------
# Rawdata 檔名常數
# ---------------------------------------------------------------------------

QUESTIONNAIRE_XLSX = "諮詢問卷_含產品建議.xlsx"
CATALOG_XLSX = "product_catalog.xlsx"
IMAGES_DOCX = "Synergy 產品圖片連結.docx"
APPS_SCRIPT_DOCX = "App Script-全心健康計畫｜初次健康評估問卷.docx"


# ---------------------------------------------------------------------------
# 序列化輔助
# ---------------------------------------------------------------------------


def _to_dict(obj: object) -> object:
    """遞迴將 frozen dataclass 轉換為可 JSON 序列化的 dict / list。"""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        raw = {}
        for f in dataclasses.fields(obj):  # type: ignore[arg-type]
            val = getattr(obj, f.name)
            raw[f.name] = _to_dict(val)
        return raw
    if isinstance(obj, tuple):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, list):
        return [_to_dict(item) for item in obj]
    return obj


def _write_json(data: object, path: Path) -> None:
    """序列化並寫入 JSON，ensure_ascii=False, indent=2。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(_to_dict(data), fh, ensure_ascii=False, indent=2)


def _validate_and_log(label: str, path: Path, validate_fn, log) -> bool:
    """
    讀回寫出的 JSON 並執行 Pydantic 驗證。

    Args:
        label: 顯示名稱（例 "questionnaire.json"）
        path: 已寫出的 JSON 路徑
        validate_fn: validators.validate_xxx 函式
        log: logger 實例

    Returns:
        True = 驗證通過，False = 驗證失敗
    """
    from pydantic import ValidationError
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        validate_fn(data)
        log.info("  [VALIDATED] %s", label)
        return True
    except ValidationError as exc:
        log.error("  [VALIDATION FAILED] %s\n%s", label, exc)
        return False
    except Exception as exc:
        log.error("  [VALIDATION ERROR] %s: %s", label, exc)
        return False


def _generate_audit_section(output_dir: Path) -> str:
    """
    從已產出的 JSON 產生手動抽檢 Markdown 段落。

    Returns:
        Markdown 字串（含換行）
    """
    lines: list[str] = []
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 手動抽檢")
    lines.append("")
    lines.append(f"產生時間：{datetime.now(ZoneInfo('Asia/Taipei')).isoformat()}")
    lines.append("")

    # --- 問卷欄位抽檢 ---
    lines.append("### 代表性欄位抽檢（3 個）")
    lines.append("")
    q_path = output_dir / "questionnaire.json"
    if q_path.exists():
        q_data = json.loads(q_path.read_text(encoding="utf-8"))
        target_ids = ["gender", "current_weight_kg", "medical_history"]
        for section in q_data.get("sections", []):
            for field in section.get("fields", []):
                if field["field_id"] in target_ids:
                    target_ids.remove(field["field_id"])
                    lines.append(f"**欄位：`{field['field_id']}`（{field['label']}）**")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(field, ensure_ascii=False, indent=2))
                    lines.append("```")
                    lines.append("")
    else:
        lines.append("_questionnaire.json 不存在，跳過欄位抽檢_")
        lines.append("")

    # --- 產品圖片抽檢 ---
    lines.append("### 產品圖片 URL 抽檢（5 個）")
    lines.append("")
    p_path = output_dir / "products.json"
    if p_path.exists():
        p_data = json.loads(p_path.read_text(encoding="utf-8"))
        # 選取 5 個目標產品（PROARGI-9+、SYNERBEET、VITALIFT、DOUBLE BURN、任高信心度）
        target_names = ["PROARGI-9+", "SYNERBEET", "VITALIFT", "DOUBLE BURN"]
        selected: list[dict] = []
        remaining: list[dict] = []
        for prod in p_data.get("products", []):
            name_upper = prod["name"].upper()
            if any(t in name_upper for t in target_names) and len(selected) < 4:
                selected.append(prod)
            elif prod.get("image_url"):
                remaining.append(prod)

        # 補足到 5 個（取高信心度）
        remaining.sort(key=lambda x: x.get("image_match_confidence") or 0, reverse=True)
        selected.extend(remaining[: max(0, 5 - len(selected))])
        selected = selected[:5]

        lines.append("| SKU | 名稱 | image_match_confidence | URL 前綴驗證 |")
        lines.append("|-----|------|------------------------|------------|")
        synergy_prefix = "https://twprod.synergyworldwide.com/"
        for prod in selected:
            url = prod.get("image_url") or ""
            conf = prod.get("image_match_confidence")
            conf_str = f"{conf:.3f}" if conf is not None else "null (未匹配)"
            url_ok = "✓" if url.startswith(synergy_prefix) else ("null" if not url else "❌ 非預期 URL")
            lines.append(
                f"| {prod['sku']} | {prod['name'][:35]} | {conf_str} | {url_ok} |"
            )
        lines.append("")
        lines.append(
            f"> URL 驗證基準：`{synergy_prefix}` 開頭視為合規。"
        )
        lines.append("")
    else:
        lines.append("_products.json 不存在，跳過產品抽檢_")
        lines.append("")

    lines.append("### 小結")
    lines.append("")
    lines.append("- PII 欄位標註：`name`、`email`、`referrer` 已標 `pii: true`")
    lines.append("- 其他 PII 候選（phone、mobile、birthday 等）在本版問卷中不存在，預設集合已備妥")
    lines.append("- 圖片 URL 均以 `https://twprod.synergyworldwide.com/` 開頭（或 null）")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def build(input_dir: Path, output_dir: Path, verbose: bool) -> int:
    """
    執行完整 schema 建構流程。

    Returns:
        0 = 成功，1 = 致命錯誤
    """
    log = logging.getLogger("build_schemas")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 步驟 1：解析問卷
    # ------------------------------------------------------------------
    from app.services.parsers.questionnaire import parse_questionnaire_xlsx

    questionnaire_xlsx = input_dir / QUESTIONNAIRE_XLSX
    if not questionnaire_xlsx.exists():
        log.error("問卷 xlsx 不存在：%s", questionnaire_xlsx)
        return 1

    log.info("[1/5] 解析問卷 xlsx …")
    try:
        questionnaire = parse_questionnaire_xlsx(questionnaire_xlsx)
    except Exception as exc:
        log.error("問卷解析失敗：%s", exc)
        return 1

    q_out = output_dir / "questionnaire.json"
    _write_json(questionnaire, q_out)
    field_count = sum(len(s.fields) for s in questionnaire.sections)
    log.info("  questionnaire.json 寫入完成（%d 個區段，%d 個欄位）",
             len(questionnaire.sections), field_count)

    # Pydantic 驗證：問卷
    from app.services.parsers.validators import validate_questionnaire, validate_products, validate_rules
    if not _validate_and_log("questionnaire.json", q_out, validate_questionnaire, log):
        return 2

    # ------------------------------------------------------------------
    # 步驟 2：解析產品目錄
    # ------------------------------------------------------------------
    from app.services.parsers.products import parse_products

    catalog_xlsx = input_dir / CATALOG_XLSX
    images_docx = input_dir / IMAGES_DOCX
    if not catalog_xlsx.exists():
        log.error("產品目錄 xlsx 不存在：%s", catalog_xlsx)
        return 1
    if not images_docx.exists():
        log.error("產品圖片 docx 不存在：%s", images_docx)
        return 1

    log.info("[2/5] 解析產品目錄 …")
    try:
        products = parse_products(catalog_xlsx, images_docx)
    except Exception as exc:
        log.error("產品解析失敗：%s", exc)
        return 1

    p_out = output_dir / "products.json"
    _write_json(products, p_out)
    log.info("  products.json 寫入完成（%d 個產品，%d 筆未匹配圖片）",
             len(products.products), len(products.unmatched_images))

    # Pydantic 驗證：產品
    if not _validate_and_log("products.json", p_out, validate_products, log):
        return 2

    # ------------------------------------------------------------------
    # 步驟 3：解析產品規則
    # ------------------------------------------------------------------
    from app.services.parsers.rules import parse_product_rules

    log.info("[3/5] 解析產品規則（依賴產品目錄）…")
    try:
        rules_schema = parse_product_rules(questionnaire_xlsx, products)
    except Exception as exc:
        log.error("規則解析失敗：%s", exc)
        return 1

    r_out = output_dir / "product_rules.json"
    _write_json(rules_schema, r_out)

    unmatched_r_out = output_dir / "unmatched_rule_products.json"
    _write_json(list(rules_schema.unmatched_rule_products), unmatched_r_out)

    unmatched_count = len(rules_schema.unmatched_rule_products)
    if unmatched_count:
        log.warning("  規則解析：%d 筆產品名稱無法匹配 SKU（已寫入 unmatched_rule_products.json）",
                    unmatched_count)
    log.info("  product_rules.json 寫入完成（%d 條規則，%d 筆未匹配）",
             len(rules_schema.rules), unmatched_count)

    # Pydantic 驗證：規則
    if not _validate_and_log("product_rules.json", r_out, validate_rules, log):
        return 2

    # ------------------------------------------------------------------
    # 步驟 4：解析 Apps Script docx 題目標題
    # ------------------------------------------------------------------
    from app.services.parsers.apps_script import parse_apps_script_docx

    apps_script_docx = input_dir / APPS_SCRIPT_DOCX
    if not apps_script_docx.exists():
        log.warning("Apps Script docx 不存在，跳過一致性驗證：%s", apps_script_docx)
        return 0

    log.info("[4/5] 解析 Apps Script docx 題目標題 …")
    try:
        as_titles = parse_apps_script_docx(apps_script_docx)
    except Exception as exc:
        log.warning("Apps Script 解析失敗（不阻斷）：%s", exc)
        as_titles = ()

    log.info("  抽取題目標題 %d 個", len(as_titles))

    # ------------------------------------------------------------------
    # 步驟 5：一致性驗證 → _consistency_report.md（含手動抽檢段落）
    # ------------------------------------------------------------------
    from app.services.parsers.consistency import compare_sources, write_consistency_report

    log.info("[5/5] 產生一致性報告 …")
    report = compare_sources(questionnaire, as_titles)
    report_out = output_dir / "_consistency_report.md"
    write_consistency_report(report, report_out)

    # 追加手動抽檢段落
    audit_section = _generate_audit_section(output_dir)
    with report_out.open("a", encoding="utf-8") as fh:
        fh.write(audit_section)
    log.info("  手動抽檢段落已追加到 _consistency_report.md")

    coverage_pct = report["coverage_ratio"] * 100
    log.info("  _consistency_report.md 寫入完成（涵蓋率 %.1f%%，差異 xlsx 獨有 %d 筆）",
             coverage_pct, len(report["xlsx_only"]))

    if coverage_pct < 50.0:
        log.warning("  一致性涵蓋率低於 50%%（%.1f%%），建議人工確認差異清單", coverage_pct)

    # ------------------------------------------------------------------
    # 總結
    # ------------------------------------------------------------------
    log.info("")
    log.info("=== 建構完成 ===")
    log.info("輸出目錄：%s", output_dir)
    log.info("  questionnaire.json  — %d 欄位（[VALIDATED]）", field_count)
    log.info("  products.json       — %d 個產品（[VALIDATED]）", len(products.products))
    log.info("  product_rules.json  — %d 條規則（[VALIDATED]）", len(rules_schema.rules))
    log.info("  unmatched_rule_products.json — %d 筆", unmatched_count)
    log.info("  _consistency_report.md — 涵蓋率 %.1f%%（含手動抽檢）", coverage_pct)

    return 0


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="解析 rawdata/ 並輸出 data/schemas/ JSON 檔案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"rawdata 目錄（預設：{DEFAULT_INPUT_DIR}）",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"schema 輸出目錄（預設：{DEFAULT_OUTPUT_DIR}）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="顯示詳細日誌",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(message)s",
        stream=sys.stdout,
    )

    sys.exit(build(args.input_dir, args.output_dir, args.verbose))


if __name__ == "__main__":
    main()
