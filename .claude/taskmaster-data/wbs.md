# WBS - Synergy Questionnaire AI (Module 2 POC)

**建立日期:** 2026-04-21
**最後更新:** 2026-04-21 19:45
**開發模式:** 完整 POC（3-5 天）
**專案描述:** 依健康問卷填答產出新手教練可用的行銷建議（健康研判摘要 + 產品組合 + 話術 + 下一步行動）
**PRD:** `rawdata/01_synergy_ai_prd.md` §7 模組 2

---

## 任務清單

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 1.1 | 專案初始化（目錄、uv、FastAPI 骨架） | ✅ 完成 | 高 | - | 0.5h | task-init 自動完成 |
| 1.2 | 需求分析（PRD §7 模組 2 + rawdata 盤點） | ✅ 完成 | 高 | - | 0.5h | task-init 自動完成 |
| 2.1 | 解析 rawdata 為 JSON schema | ✅ 完成 | 高 | 1.2 | 2h | [計畫](plans/2.1-parse-rawdata.md) — 37 tests PASS, 94% cov |
| 2.1.1 | └ 解析健康評估問卷 docx → questionnaire.json | ✅ 完成 | 高 | - | 1h | 併入 2.1 實作 |
| 2.1.2 | └ 解析 product_catalog.xlsx + 圖片連結 docx → products.json | ✅ 完成 | 高 | - | 1h | 併入 2.1 實作 |
| 2.1.3 | └ 解析諮詢問卷_含產品建議.xlsx → 產品對應規則 rules.json | ✅ 完成 | 中 | 2.1.2 | 0.5h | 併入 2.1 實作 |
| 2.2 | 定義輸出契約 Pydantic schemas | ✅ 完成 | 高 | 2.1 | 1h | 40 tests PASS, 100% cov |
| 2.3 | LiteLLM client + config（Gemini） | ✅ 完成 | 高 | 1.1 | 1h | 32 tests PASS, 88% cov, PII mask + 重試 |
| 3.1 | Prompt 工程 — 健康研判摘要 | ✅ 完成 | 高 | 2.2, 2.3 | 1.5h | 12 tests PASS, 100% cov |
| 3.2 | Prompt 工程 — 產品推薦（Rule-assisted） | ✅ 完成 | 高 | 2.1.3 | 1.5h | 37 tests PASS, 94% cov. 已知: rules.json 目前全為空 conditions，需後續補條件 |
| 3.3 | Prompt 工程 — 行銷話術 | ✅ 完成 | 高 | 3.1 | 1h | 12 tests PASS, 93% cov, 4 情境 |
| 3.4 | Prompt 工程 — 下一步行動 | ✅ 完成 | 中 | 3.1 | 0.5h | 17 tests PASS, 100% cov, 5 action 列舉 |
| 3.5 | 整合 Advice Service（串起 3.1-3.4） | ✅ 完成 | 高 | 3.1-3.4 | 1h | 13 tests PASS, 100% cov, asyncio.gather 雙 Stage 平行化 |
| 4.1 | API — `POST /advise` | ✅ 完成 | 高 | 3.5 | 0.5h | 14 tests PASS, 100% cov, 錯誤碼映射 504/502/500/422 |
| 4.2 | API — `GET /questionnaire/schema` | ✅ 完成 | 高 | 2.1.1 | 0.5h | 含 Pydantic 驗證 + cache |
| 4.3 | API — `GET /products` | ✅ 完成 | 中 | 2.1.2 | 0.5h | 支援 ?category ?limit 篩選 |
| 5.1 | 初始化 Next.js 16 + TypeScript + Tailwind | ✅ 完成 | 高 | - | 0.5h | build PASS, Next 16.2.4, api proxy + 基礎 Apple 樣式 |
| 5.2 | Apple UI 設計 tokens 套用 | ✅ 完成 | 中 | 5.1 | 1h | 完整 design tokens + 4 元件 (Button/Card/Input/Section) |
| 5.3 | 問卷填寫頁（動態渲染 schema） | ✅ 完成 | 高 | 4.2, 5.2 | 2h | 分段/驗證/條件顯示/進度條 |
| 5.4 | 建議結果頁（四段式 + 產品圖） | ✅ 完成 | 高 | 4.1, 5.2 | 2h | 6 元件，四段渲染，圖片 fallback |
| 5.5 | 複製按鈕、匯出（讓教練一鍵帶走話術） | ✅ 完成 | 中 | 5.4 | 0.5h | clipboard 含 SSR/HTTP fallback，Markdown 下載 |
| 6.1 | 單元測試 — schemas / parsers / services | ✅ 完成 | 高 | 2.1-3.5 | 2h | +48 tests, 整體 97% cov |
| 6.2 | 整合測試 — `/advise` mock LLM | ✅ 完成 | 高 | 4.1 | 1h | 8 integration tests（pipeline + API E2E） |
| 6.3 | 手動端到端驗證（3 個典型情境） | ✅ 完成 | 高 | 5.4 | 1h | 3 fixtures + e2e_verify.py CLI + checklist |
| 7.1 | README（啟動指令 + 架構圖） | ✅ 完成 | 中 | - | 0.5h | 517 行，13 章節 |
| 7.2 | 使用示範截圖 / GIF | ⏭️ 跳過 | 低 | 5.4 | 0.5h | POC 階段低優先，需人工 Demo 後補 |

### 狀態說明

- ✅ 完成
- 🔄 進行中
- ⏳ 待處理
- 🚫 阻塞
- ⏭️ 跳過

---

## 里程碑

| 里程碑 | 目標日期 | 包含任務 | 狀態 |
|--------|----------|----------|------|
| M1: 資料契約完成 | 2026-04-22 | 2.1, 2.2, 2.3 | ⏳ |
| M2: LLM Pipeline 可跑 | 2026-04-23 | 3.1-3.5, 4.1 | ⏳ |
| M3: 前端可完整操作 | 2026-04-24 | 5.1-5.5 | ⏳ |
| M4: POC 驗收通過 | 2026-04-25 | 6.1-6.3, 7.1 | ⏳ |

---

## 風險與阻塞

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| Gemini API 中文健康領域幻覺，給出錯誤醫療建議 | 高 | Prompt 加強「非醫療診斷」免責、強制 JSON schema、few-shot 拿正確範例 |
| 產品規則過於複雜，LLM 推薦不穩定 | 中 | 先用規則引擎篩候選（年齡/性別/需求），再交給 LLM 排序與寫理由 |
| rawdata 問卷結構不完整或多版本不一致 | 中 | 先手動對齊主版本，保留 ADR 記錄決策 |
| 問卷內容含個資（姓名/電話） | 高 | `core/pii.py` 遮蔽 log；前端不傳敏感欄位到 LLM |
| POC 時程緊（3-5 天） | 中 | P2 功能（5.5、7.2）可先跳過 |

---

## 下一步

執行 `/task-next` 取得建議任務，或 `/plan 2.1` 規劃第一個實作任務（解析 rawdata）。
