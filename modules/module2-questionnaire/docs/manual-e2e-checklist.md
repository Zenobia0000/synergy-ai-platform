# 手動 E2E 驗證清單

> 用途：在沒有完整自動化 E2E 測試時，快速用瀏覽器走完一遍關鍵路徑。
> 每次發布前或重大改動後執行一次，確保主要流程正常。

---

## 前置準備

- [ ] 設定 `backend/.env` 的 `GEMINI_API_KEY`（向專案負責人取得）
- [ ] 啟動後端：`(cd D:/project/synergy/backend && uv run uvicorn main:app --reload)` → port 8000
- [ ] 啟動前端：`(cd D:/project/synergy/frontend && npm run dev)` → port 3000
- [ ] 確認 schema 檔存在：`D:/project/synergy/data/schemas/questionnaire.json`
  - 若不存在，執行：`(cd D:/project/synergy/backend && uv run python scripts/build_schemas.py --verbose)`
- [ ] 瀏覽器開啟 http://localhost:3000 確認首頁正常載入

---

## 通用 API 健康確認

在瀏覽器或 curl 確認以下端點：

| 端點 | 預期狀態 | 說明 |
|------|---------|------|
| `GET http://localhost:8000/health` | 200 | `{"status": "ok"}` 或類似 |
| `GET http://localhost:8000/questionnaire/schema` | 200 | 回應含 `sections` 陣列 |

---

## 情境 1：中年男性 + 代謝風險

**對應 fixture：** `backend/tests/fixtures/scenarios/male_45_overweight.json`

### 填寫步驟

1. 開啟 http://localhost:3000，點「開始問卷」或「立即評估」
2. **基本資料**填寫：
   - 姓名：任意測試名稱
   - 年齡：45
   - 性別：男
   - 身高：172 cm
   - 目前體重：92 kg
   - 理想體重：75 kg
3. **健康目標**：選「體重管理」、「體力不足」
4. **壓力**：壓力程度選「中等」，來源選「工作」、「健康」
5. **睡眠**：作息「不規律」，睡眠時數「6-7小時」，精神狀態「普通」
6. **活動量**：平日活動「久坐為主」，每週運動「0次」
7. **醫療紀錄**：
   - 勾選「高血壓」、「血糖異常」
   - 有長期藥物：「有」→ 填「降血壓藥」
   - 健檢異常：「有」→ 填「血糖偏高、三酸甘油脂偏高」
8. **飲食**：選「澱粉比例較高」、「肉類比例較高」、「經常外食」
9. 送出問卷

### 預期結果

- [ ] 問卷提交後不顯示錯誤訊息
- [ ] 頁面進入「分析中」或載入狀態
- [ ] 最終顯示 AI 建議頁面
- [ ] `summary.overall_level` 顯示為 **medium** 或 **high**
- [ ] 推薦產品清單不為空（至少 1 項）
- [ ] next_actions 含有類似「安排諮詢」或「schedule_consultation」
- [ ] 建議頁面無 500/502/504 錯誤訊息

---

## 情境 2：30 多歲女性 + 壓力睡眠問題

**對應 fixture：** `backend/tests/fixtures/scenarios/female_35_sleep_issue.json`

### 填寫步驟

1. 重新開始問卷（或重整頁面）
2. **基本資料**：
   - 年齡：35
   - 性別：女
   - 身高：162 cm
   - 目前體重：58 kg
3. **健康目標**：選「睡眠品質」、「壓力與疲勞」、「體力不足」
4. **壓力**：壓力程度選「很高」，症狀選「肩頸緊繃」、「頭痛」、「情緒起伏較大」、「容易疲倦」
5. **睡眠**：
   - 作息「不規律」
   - 睡眠時數「5-6小時」
   - 常見睡眠問題：全部勾選（難以入睡、易醒、多夢、起床後疲倦）
   - 起床精神：「很差」
6. **活動量**：久坐為主，0次運動
7. **醫療紀錄**：無病史、無藥物、健檢正常
8. 送出問卷

### 預期結果

- [ ] 問卷正常提交
- [ ] `summary` 中提到睡眠或壓力相關關鍵字
- [ ] 推薦產品含睡眠/放鬆/舒壓類別產品
- [ ] sales_scripts 的情境涵蓋壓力或睡眠訴求
- [ ] next_actions 至少 1 項

---

## 情境 3：高齡 62 歲 + 多重慢性病 → 轉上線

**對應 fixture：** `backend/tests/fixtures/scenarios/senior_62_chronic.json`

> 此情境最重要，驗證 AI 是否識別高風險並觸發 escalate_to_senior 行動。

### 填寫步驟

1. 重新開始問卷
2. **基本資料**：
   - 年齡：62
   - 性別：男
   - 身高：168 cm
   - 目前體重：78 kg
3. **健康目標**：選「體力不足」、「體重管理」
4. **壓力**：中等
5. **睡眠**：規律，6-7小時，起床精神「偏差」
6. **醫療紀錄**（關鍵）：
   - 勾選「高血壓」、「血糖異常」、「胃食道逆流」
   - 有長期藥物：「有」→ 填「降血壓藥、降血糖藥、胃藥」
   - 健檢異常：「有」→ 填「血壓偏高、血糖偏高、GFR 輕微偏低」
7. 送出問卷

### 預期結果

- [ ] 問卷正常提交不報錯
- [ ] `next_actions` 含有 **escalate_to_senior**（高優先級）
- [ ] `summary.disclaimers` 或建議內容提到「請遵循醫師建議」或「與醫師確認」
- [ ] `summary.overall_level` 為 **high**
- [ ] 推薦產品考量腎功能（無含高鉀/高磷的產品），或備註需醫師確認
- [ ] 不出現與現有藥物明顯衝突的強推薦

---

## 自動化驗證（不需 Gemini API）

以下指令可在不啟動 Gemini 的情況下執行 schema 完整性驗證：

```bash
# 只驗 fixture 合法性（不呼叫 /advise）
uv run python scripts/e2e_verify.py --dry-run

# 驗單一情境（需後端執行中，預設 port 8000）
uv run python scripts/e2e_verify.py --scenario male_45_overweight

# 驗全部情境（需後端執行中 + GEMINI_API_KEY）
uv run python scripts/e2e_verify.py --all
```

```bash
# pytest fixture 驗證（不需後端）
(cd D:/project/synergy/backend && uv run pytest tests/test_scenarios_fixtures.py -v)
```

---

## 常見問題排除

| 症狀 | 原因 | 解法 |
|------|------|------|
| 問卷畫面空白 / 無法載入 | backend 未啟動或 schema 遺失 | 確認 port 8000 正常，並確認 `data/schemas/questionnaire.json` 存在 |
| `POST /advise` 回傳 504 Timeout | Gemini API 呼叫逾時 | 檢查 `GEMINI_API_KEY` 是否正確，確認網路可連到 Google API |
| `POST /advise` 回傳 502 Bad Gateway | LLM 回應非合法 JSON | 查看 backend 日誌，確認 prompt 結構，或切換 Gemini model 版本 |
| `/advise` 回傳 422 Validation Error | 答案欄位格式錯誤 | 對照 `GET /questionnaire/schema` 的欄位型別，確認 answers 格式 |
| 產品無圖片顯示 | 圖片未匹配 | 查看 `data/schemas/unmatched_images.json` 確認哪些產品圖片遺失 |
| next_actions 無 `escalate_to_senior` | Prompt 未觸發或 LLM 未判斷高風險 | 確認情境 3 的慢性病欄位都有填寫，查看 backend prompt 設定 |

---

## 驗證記錄格式

每次執行後，可記錄於此：

```
日期：______ 驗證人：______
情境1：PASS / FAIL  備註：
情境2：PASS / FAIL  備註：
情境3：PASS / FAIL  備註：
整體：PASS / FAIL
```
