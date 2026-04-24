# Synergy AI 文件索引

> **產品：** Synergy AI — Closer's Copilot（教練成交副駕駛）
> **版本：** MVP v2.0 | **更新：** 2026-04-24 | **模式：** VibeCoding full

---

## 文件清單

| # | 檔案 | 用途 | 對應 VibeCoding 範本 |
| :---: | :--- | :--- | :--- |
| 01 | [01_prd.md](./01_prd.md) | 產品需求文件（Personas、OKRs、Epic、範圍、風險） | 02 |
| 02 | [02_bdd.md](./02_bdd.md) | BDD 情境（4 個 feature、24 個 scenario） | 03 |
| 03 | [03_adr.md](./03_adr.md) | 架構決策記錄（9 條決策 + 相依圖） | 04 |
| 04 | [04_architecture.md](./04_architecture.md) | 系統架構（C4 三層 + DDD Context + 資料模型） | 05 |
| 05 | [05_api.md](./05_api.md) | API 規範（REST 端點 + schema） | 06 |
| 06 | [06_modules.md](./06_modules.md) | 模組規格與測試（9 個模組 + 測試範例） | 07 |
| 07 | [07_structure.md](./07_structure.md) | 專案結構（apps/ + packages/ + modules/） | 08 |
| 08 | [08_design_dependencies.md](./08_design_dependencies.md) | 設計與依賴（類別圖、套件清單、SOLID 檢核） | 09 |
| 09 | [09_frontend_ia.md](./09_frontend_ia.md) | 前端資訊架構（11 頁 + 3 旅程 + 導航） | 17 |
| 10 | [10_security.md](./10_security.md) | 安全與合規（威脅模型、RLS、OWASP、上線 checklist） | 13 |
| 11 | [11_deployment.md](./11_deployment.md) | 部署維運（CI/CD、SLO、成本、runbook） | 14 |

**未產出（可後續補）**：
- 程式碼審查指南（11）— 建議跑 `/check-quality` 時動態產生
- 前端架構細節（12）— 已在 09_frontend_ia.md 涵蓋
- 文檔維護指南（15）— 隨 Git 慣例即可
- WBS（16）— 由 `/task-init` 下一步產出

---

## 閱讀順序建議

### 新加入的工程師
1. `01_prd.md`（為什麼做）
2. `04_architecture.md`（怎麼做整體）
3. `07_structure.md`（檔案放哪）
4. 自己領域的 `06_modules.md §對應模組`

### 新加入的 PM / 設計師
1. `01_prd.md`
2. `09_frontend_ia.md`
3. `02_bdd.md`（行為定義）

### Tech Lead 決策
1. `03_adr.md`（所有決策脈絡）
2. `04_architecture.md`
3. `10_security.md` + `11_deployment.md`

---

## 參考原始文件

| 檔案 | 性質 |
| :--- | :--- |
| `system_design_docs/01_synergy_ai_prd.md` | 原 PRD v1.0（已被本系列 `01_prd.md` 取代） |
| `system_design_docs/健康直銷AI系統_模組分層與MVP規劃.docx` | 客戶策略文件 A（MVP 收斂依據） |
| `system_design_docs/健康直銷AI平台_跨品牌擴張策略評估_麥肯錫分析.docx` | 客戶策略文件 B（Phase 2+ 擴張藍圖） |

---

## 下一步

1. **`/task-init`**：從本文件集產出 WBS（建議 full 模式）
2. **`/pm-choose`**：確認前端 package manager（pnpm 推薦）
3. **`/plan`**：為 Week 1-2 的問卷系統建立實作計畫
4. **`/tdd`**：進入開發循環

---

## 版本記錄

| 版本 | 日期 | 變更 |
| :--- | :--- | :--- |
| v2.0 | 2026-04-24 | 初版產出（11 份文件），依客戶兩份新策略文件收斂為 4 功能 MVP |
| v2.0.1 | 2026-04-24 | **ADR-008 翻轉**：提醒通道改為 LINE Messaging API 優先、Email 為備援。同步更新 PRD（US-D03 升 Must、依賴、風險 R-06/R-07、時程）、架構圖、API（LINE webhook 端點）、模組（NotificationChannel + fallback 路由）、BDD（新增 2 個 fallback scenarios）、依賴（line-bot-sdk）、部署（成本 +800 NTD、LINE OA 審核 checklist）、project.json |
