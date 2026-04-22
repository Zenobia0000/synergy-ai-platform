# parsers 模組

## 模組目的

將 `rawdata/` 下的 4 份異質來源（xlsx、docx）解析並正規化為 3 份 JSON schema，放置於 `data/schemas/`，作為後續 Pydantic schemas（2.2）、LLM prompts（3.x）、前端問卷渲染（5.3）共用的單一資料源（Single Source of Truth）。

---

## 執行方式

從 `backend/` 目錄執行：

```bash
(cd D:/project/synergy/backend && PYTHONIOENCODING=utf-8 uv run python scripts/build_schemas.py --verbose)
```

### 可用旗標

| 旗標 | 說明 | 預設值 |
|------|------|--------|
| `--verbose` | 顯示 DEBUG 級別詳細日誌 | 關閉 |
| `--input-dir PATH` | rawdata 目錄 | `<project_root>/rawdata` |
| `--output-dir PATH` | schema 輸出目錄 | `<project_root>/data/schemas` |

### 執行後輸出

```
data/schemas/
├── questionnaire.json           — 問卷結構（56 欄位，16 區段）
├── products.json                — 產品目錄（33 個產品，含圖片 URL）
├── product_rules.json           — 產品建議規則（61 條）
├── unmatched_rule_products.json — 規則中無法匹配的產品名（20 筆）
└── _consistency_report.md       — 問卷一致性報告（含手動抽檢）
```

---

## 資料來源對照

| rawdata 檔名 | 對應 parser 模組 | 產出 JSON |
|-------------|----------------|----------|
| `諮詢問卷_含產品建議.xlsx` | `questionnaire.py` | `questionnaire.json` |
| `諮詢問卷_含產品建議.xlsx`（K 欄） | `rules.py` | `product_rules.json` |
| `product_catalog.xlsx` | `products.py` | `products.json` |
| `Synergy 產品圖片連結.docx` | `products.py`（`_parse_images_docx`） | 圖片 URL 嵌入 `products.json` |
| `App Script-全心健康計畫｜初次健康評估問卷.docx` | `apps_script.py` | `_consistency_report.md`（驗證用） |

---

## 模組結構

```
app/services/parsers/
├── __init__.py         — 套件入口
├── types.py            — frozen dataclass 型別定義（不可變）
├── questionnaire.py    — 問卷 xlsx 解析
├── products.py         — 產品目錄 + 圖片匹配
├── rules.py            — 產品建議規則解析
├── apps_script.py      — Apps Script docx 題目擷取（驗證用）
├── consistency.py      — 問卷一致性比對報告
└── validators.py       — Pydantic v2 自驗證層
```

---

## 已知限制

### 1. 規則 K 欄指引文字（20 筆未匹配）

規則 xlsx K 欄有 20 筆是「指引文字」（如「依客戶填寫內容」、「建議諮詢醫師」），**不是產品名稱**。這些條目已記錄於 `unmatched_rule_products.json`，不阻斷 CLI，可手動確認後補充映射。

### 2. Apps Script docx 為交叉驗證用，非主來源

`App Script-全心健康計畫｜...docx` 擷取的題目標題用於一致性比對，**不作為解析主來源**。目前涵蓋率 60.7%（超過 50% 門檻）。差異主因為版本間標題格式差異（如加了序號前綴、合併題組），不影響問卷主資料正確性。

### 3. 圖片匹配含 fuzzy，信心值 < 1.0 需人工複核

圖片匹配採四層策略（精確 → NFKC 正規化 → 中文子字串包含 → fuzzy ≥ 0.85）。目前 33 個產品中：
- 23 個成功匹配（confidence 0.843–0.95）
- 4 個未匹配（套組或新版產品名差異過大），`image_url` 設 `null`
- **信心值 < 0.9 的建議人工確認** URL 正確性

### 4. 問卷未包含所有 PII 欄位

預設 PII 集合（`_PII_FIELD_IDS`）包含 `phone`、`mobile`、`birthday`、`address`、`id_number`、`line_id`，但此版本問卷僅有 `name`、`email`、`referrer`。若未來擴充問卷，新增欄位若 field_id 在集合中會自動標 `pii: true`。

---

## 擴充指引

### 新增產品

1. 在 `product_catalog.xlsx` 新增一列（確保 SKU 唯一）
2. 若有圖片，在 `Synergy 產品圖片連結.docx` 補上格式 `產品名：URL`
3. 重跑 CLI 即可自動匹配

### 新增問卷題型

1. 在 `questionnaire.py` 的 `_TYPE_MAP` 加入新的中文 → 英文映射
2. 在 `validators.py` 的 `_VALID_FIELD_TYPES` Literal 加入新類型
3. 更新 `test_questionnaire.py` 驗證新題型

### 調整圖片匹配閾值

修改 `products.py` 中的 `FUZZY_THRESHOLD`（目前 0.85）。降低閾值會增加匹配數但可能誤匹配；提高閾值則相反。

### 新增 PII 欄位

在 `questionnaire.py` 的 `_PII_FIELD_IDS` frozenset 加入新的 field_id。

---

## 測試

```bash
# 執行全部 parsers 測試
(cd D:/project/synergy/backend && uv run pytest tests/services/parsers -v --cov=app.services.parsers --cov-report=term-missing)
```

| 測試項目 | 測試數 |
|---------|--------|
| 問卷解析 | 5 |
| 產品解析 | 5 |
| 規則解析 | 4 |
| Apps Script 解析 | 3 |
| 一致性報告 | 4 |
| Pydantic 驗證層 | 16 |
| **合計** | **37** |

目前覆蓋率：**94%**（目標 ≥ 85%）
