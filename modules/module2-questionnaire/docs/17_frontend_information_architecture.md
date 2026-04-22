# 前端資訊架構（Frontend IA）— Synergy Questionnaire AI

> **專案:** synergy-questionnaire-ai POC
> **最後更新:** 2026-04-22
> **參照模板:** `VibeCoding_Workflow_Templates/17_frontend_information_architecture_template.md`
> **對應 Q&A:** `.claude/qa-history/2026-04-22-033935-ui-site.md`

---

## 1. 核心價值主張

**一句話說明：** 新手教練透過 AI 問卷評估，快速把「填問卷的客戶資料」轉成可直接使用的健康研判 + 產品組合 + 話術 + 下一步行動，降低商談準備時間。

**兩個角色對應價值：**
- **一般使用者** — 填完問卷就能拿到個人化健康研判與產品推薦，不被推銷話術打擾。
- **新手教練** — 不必從零組織建議，系統提供話術模板與建議流程，把經驗值補起來。

---

## 2. 資訊架構原則

1. **角色導向分流**：使用者與教練看到的內容不重疊 — 話術、下一步行動等銷售資訊永遠不對一般使用者顯示。
2. **單一入口假登入**：`/login` 選角色後寫入 `sessionStorage.role`，後續路由依角色 guard。
3. **Session 生命週期**：同一個 tab 內 `role`、`pending_advice_request`、`last_advice_result` 同生共死；關閉瀏覽器即清空（POC 階段不持久化）。
4. **Apple 極簡視覺哲學**：單一 Apple Blue 作為互動色、黑與淺灰二元對比、大量留白、單行標題不換行。
5. **健康內容可讀優先**：Body 17px、行高 1.47，確保長段健康摘要閱讀順暢。

---

## 3. 頁面清單與使用者旅程

### 頁面對照表

| 路徑 | 角色 | 頁面名 | 目的 | 主要 CTA |
|---|---|---|---|---|
| `/` | 公開 | Home / 歡迎 | 介紹 POC 定位，引導登入 | `前往登入` |
| `/login` | 公開 | Login / 角色選擇 | 假登入，寫入 role | `以使用者身份進入` / `以新手教練身份進入` |
| `/u/questionnaire` | user | Questionnaire | 填寫健康問卷（FORM + 健康） | `送出並查看結果` |
| `/u/result` | user | User Result | 展示健康摘要 + 推薦產品 | `再填一次` |
| `/coach` | coach | Coach Dashboard | 讀最近一筆結果，顯示完整建議 | （內含下列匯出動作） |
| `/coach/advice` | coach | Coach Advice | 同上路由重導，保留 URL 可書籤 | `複製全文 MD` / `下載 MD` |

### 使用者旅程

#### A. 一般使用者路徑
```
/ → /login（選「使用者」） → /u/questionnaire → 送出 → /u/result
```
- `/u/result` 不顯示話術、下一步行動。
- Header 顯示身份標記「使用者」，可點「切換角色」回 `/login`。

#### B. 新手教練路徑（續 A 之後）
```
使用者填完問卷 → 教練切換角色：/login（選「教練」）→ /coach
```
- `/coach` 自動讀 `sessionStorage.last_advice_result`；若無資料顯示空狀態 + CTA「請先以使用者身份填寫問卷」。
- 若有資料：顯示完整建議（摘要 + 產品 + 話術 + 下一步），並提供「複製 Markdown」「下載 Markdown」。

### 角色 Guard 規則

| 情境 | 行為 |
|---|---|
| 未選 role 直接進 `/u/*` 或 `/coach*` | 導 `/login` |
| `role=user` 進 `/coach*` | 導 `/u/questionnaire`（或顯示權限提示） |
| `role=coach` 進 `/u/questionnaire`、`/u/result` | 允許（教練可代填） |
| `/coach` 無 `last_advice_result` | 顯示空狀態，不 redirect |

---

## 4. URL 規範

- 角色名詞前綴：`/u/`（user）、`/coach/`（coach）— 避免用內部代號（如 `/u1`、`/u2`）
- 頁面名用語意動詞或名詞：`/questionnaire`、`/result`、`/advice`
- 不使用複數：`/u/result`（單筆結果）而非 `/u/results`
- 小寫、連字號分隔（如未來有 `/coach/product-catalog`）

---

## 5. 導航設計

### Header（共用）

- **左側品牌**：`Synergy AI` — 點擊導向 `/`
- **中間** (選配)：角色標記徽章 — 如「使用者模式」「教練模式」
- **右側**：
  - 未登入（無 role）→ 「登入」按鈕
  - 已登入 → 「切換角色」文字連結（實際上 clear sessionStorage 後 redirect `/login`）
- **樣式**：白底、底部 1px 邊線、高度 56px、`position: sticky`

> POC 不使用 Apple 原生的毛玻璃導覽列（`rgba(0,0,0,0.8) + backdrop-filter`），改用亮色 Header 以配合健康題材的親和感。

### Footer（共用）

- 左側：`© 2026 Synergy POC · WBS 模組 2`
- 右側：小字 `Powered by Gemini 2.5`
- 高度 48px、淺灰文字 `--color-fg-subtle`、背景同 `--color-bg`

### 頁內區塊導航
`/coach` 的完整建議頁使用單欄垂直捲動（無側邊導航）；主要區塊：摘要 → 推薦產品 → 話術 → 下一步行動 → 匯出工具列。

---

## 6. 每頁 IA 細節

### 6.1 Home `/`

| 欄位 | 內容 |
|---|---|
| 目的 | 介紹 POC 性質、引導到登入 |
| 主要區塊 | Hero 標題 + 副標 · 後端健康檢查卡片 · 「前往登入」CTA |
| 主 CTA | `前往登入` → `/login` |
| 資料需求 | `GET /api/health` |
| 狀態 | 空、載入中、成功、錯誤 |

### 6.2 Login `/login`

| 欄位 | 內容 |
|---|---|
| 目的 | 假登入，選角色寫入 sessionStorage |
| 主要區塊 | 標題 · 兩個卡片式角色入口（使用者 / 新手教練） |
| 主 CTA | 卡片本身即 CTA，點擊 = 選擇該角色 |
| 資料需求 | 無（純前端） |
| 狀態 | 空（若已有 role，顯示「目前為 X 身份，繼續或切換」） |

### 6.3 Questionnaire `/u/questionnaire`

| 欄位 | 內容 |
|---|---|
| 目的 | 填寫健康問卷 |
| 主要區塊 | 進度條 · 分段問卷（FORM + 健康） · 底部上一步 / 下一步 / 送出 |
| 主 CTA | `送出並查看結果` |
| 資料需求 | `GET /api/questionnaire/schema` 取 schema；`POST /api/advise` 提交 |
| 狀態 | 載入中、錯誤（重試）、填寫中、送出中 |
| Role guard | `user` 或 `coach` 均允許 |

### 6.4 User Result `/u/result`

| 欄位 | 內容 |
|---|---|
| 目的 | 使用者看精簡版健康研判 + 產品推薦 |
| 主要區塊 | 健康摘要 Card · 推薦產品 Grid（ProductCard）· 回到問卷 CTA |
| 主 CTA | `再填一次` → `/u/questionnaire` |
| 資料需求 | 從 sessionStorage 讀 `last_advice_result` |
| 隱藏欄位 | **不顯示** 話術（sales_scripts）與下一步（next_actions） |
| 狀態 | 無資料（導回問卷）、有資料 |
| Role guard | 僅 `user`；`coach` 被導去 `/coach` |

### 6.5 Coach `/coach` 與 `/coach/advice`

| 欄位 | 內容 |
|---|---|
| 目的 | 教練看完整建議（摘要 + 產品 + 話術 + 下一步） |
| 主要區塊 | 工具列（複製 MD / 下載 MD / 再生成）· SummaryCard · ProductsGrid · ScriptsList · NextActionsList |
| 主 CTA | `複製全文 Markdown`、`下載 Markdown` |
| 資料需求 | `sessionStorage.last_advice_result`；若需重新呼叫用 `POST /api/advise` |
| 狀態 | 無資料（顯示空狀態引導）、有資料、重新生成中、錯誤 |
| Role guard | 僅 `coach` |

---

## 7. 空狀態 / 錯誤狀態規範

| 情境 | 文案 | CTA |
|---|---|---|
| `/coach` 無 sessionStorage | 「目前沒有問卷結果 — 請先以『使用者』身份填寫一份問卷」 | `切換角色去填寫` |
| `/u/result` 無 sessionStorage | 「尚未填寫問卷」 | `前往問卷` |
| API 連線失敗 | 「連線失敗，請確認後端是否啟動」 | `重試` |
| 問卷載入失敗 | 「無法載入問卷」 | `重試` |

---

## 8. 無障礙與響應式

- 所有互動元件 focus ring: `outline: 2px solid var(--color-focus)`、`outline-offset: 2px`
- 表單欄位必有 `<label>` + `aria-required` 標示
- 容器最大寬度 `--container-max`（建議 960px），小螢幕使用 16px padding
- 問卷頁單欄流版面，避免橫向捲動
- 色彩對比：Apple 設計本身 AA+（黑/淺灰、Apple Blue/白均 >4.5:1）

---

## 9. 共用資料字典（sessionStorage）

| Key | 型別 | 寫入時機 | 清除時機 |
|---|---|---|---|
| `role` | `"user" \| "coach"` | `/login` 選角色時 | 關閉 tab；點「切換角色」 |
| `pending_advice_request` | `Answers`（問卷原始答案） | 問卷送出前暫存 | 成功取得建議後（保留或清除皆可） |
| `last_advice_result` | `AdviceResponse` | 取得建議後寫入 | 關閉 tab；重新問卷時覆寫 |

---

## 10. 已知 IA 限制 / 未來擴充

- POC 無資料持久化，教練無法看「過去某使用者」的結果
- 無權限系統，角色只是前端 sessionStorage 假角色，後端無驗證
- 無多語系
- 話術/產品資料全部來自 LLM 單次回應，不支援快取比對

> 這些限制在模組 2 進入 GA 階段時應由 ADR 逐一處理。
