# 07 — 平台帳號與權限

> **對口窗口:** IT / 營運窗口
> **最晚交付日:** Phase 4 W4（建議 Phase 1 就開始申請）
> **用途:** 串接各社群平台 API，實現多平台自動發布與互動監控

---

## 為什麼要提前準備

平台開發者帳號申請通常需要 1-4 週審核。
如果等到要用的時候才申請，Phase 5 會直接卡死。

**建議 Phase 1 就開始辦理**，即使要到 Phase 5 才用。

---

## 你需要準備什麼

### 1. 各社群平台開發者帳號（0.7.1）

**檔案名稱建議:** `platform_accounts_checklist.xlsx`

| 平台 | 需要的東西 | 目前狀態 | 備註 |
| :--- | :--- | :--- | :--- |
| **Facebook** | | | |
| | Facebook Page（粉專） | 有 / 沒有 | Page ID: |
| | Meta Developer 帳號 | 有 / 沒有 | |
| | Meta App（已建立） | 有 / 沒有 | App ID: |
| | pages_manage_posts 權限 | 已申請/未申請 | 需要 Business 驗證 |
| | pages_read_engagement 權限 | 已申請/未申請 | 用於互動監控 |
| **Instagram** | | | |
| | IG Professional 帳號 | 有 / 沒有 | 需先從個人轉專業帳號 |
| | 已連結 Facebook Page | 有 / 沒有 | IG API 透過 FB Graph API 存取 |
| | instagram_basic 權限 | 已申請/未申請 | |
| | instagram_content_publish 權限 | 已申請/未申請 | |
| **X (Twitter)** | | | |
| | X Developer Account | 有 / 沒有 | |
| | Elevated Access（如需要） | 有 / 沒有 | Free tier 可能不夠 |
| | OAuth 2.0 設定 | 有 / 沒有 | |
| **LINE OA** | | | |
| | LINE Official Account | 有 / 沒有 | |
| | LINE Developers Console 帳號 | 有 / 沒有 | |
| | Messaging API Channel | 有 / 沒有 | Channel ID: |
| | Webhook URL 已設定 | 有 / 沒有 | |
| **Google** | | | |
| | Google Cloud 專案 | 有 / 沒有 | |
| | Calendar API 已啟用 | 有 / 沒有 | |
| | OAuth 2.0 Consent Screen | 有 / 沒有 | |

#### 請逐項確認，標註目前狀態。沒有的請標「沒有」，我們會給申請指引。

---

### 2. API Token / Key（0.7.2）

> **安全提醒：不可放在文件、Email、聊天中傳遞**

交付方式（擇一）：
1. 直接設定在開發環境的 `.env` 檔案中（由 IT 窗口操作）
2. 透過密碼管理工具（如 1Password、Bitwarden）分享
3. 面對面口頭告知 + 現場設定

需要的 Token/Key 清單：

| 平台 | Token 類型 | 說明 |
| :--- | :--- | :--- |
| Facebook | Page Access Token (Long-lived) | 用於發文、讀取互動 |
| Instagram | 透過 Facebook Token | 同上 |
| X | API Key + API Secret | OAuth 2.0 認證 |
| X | Access Token + Access Secret | 代表帳號發文 |
| LINE | Channel Access Token | 用於發送訊息 |
| LINE | Channel Secret | 用於驗證 Webhook |
| Google | OAuth Client ID + Secret | 用於 Calendar 整合 |
| Claude API | API Key | 用於 AI 功能 |

---

### 3. LINE OA 設定（0.7.3）

**檔案名稱建議:** `line_oa_setup.md`

請確認以下設定：

| 設定項目 | 目前狀態 | 需要的狀態 |
| :--- | :--- | :--- |
| 帳號方案 | 免費/輕用量/標準 | 視推播量決定 |
| Messaging API 已啟用 | 是/否 | 是 |
| Auto-reply 設定 | 開啟/關閉 | 需要討論（可能要關閉，改由系統處理） |
| Greeting Message | 有/無 | 需要討論 |
| Rich Menu | 有/無 | 未來可能需要 |

#### 需要確認的問題
- LINE OA 目前每月推播量大約多少？（影響方案選擇）
- 目前有沒有已經在用的自動回覆？（避免衝突）
- 是否需要 LINE Login 功能？（讓消費者用 LINE 帳號登入系統）

---

### 4. Google Calendar 整合帳號（0.7.4）

**檔案名稱建議:** `google_calendar_setup.md`

| 項目 | 說明 |
| :--- | :--- |
| 用哪個 Google 帳號？ | 建議用組織帳號，非個人 |
| 需要存取哪些日曆？ | 每個經營者各自的？還是共用一個？ |
| 同步方向 | 系統 → Google Calendar（單向）？還是雙向？ |
| 已有的預約工具 | 目前有沒有在用 Calendly 之類的工具？ |

---

## 交付方式

1. Checklist 表格放入此資料夾
2. Token/Key 透過安全管道傳遞（不放在此資料夾）
3. 通知產品經理 + 後端工程師

## 驗收標準

- [ ] 所有平台帳號狀態已確認
- [ ] 缺少的帳號已開始申請流程
- [ ] API Token 已透過安全方式交付
- [ ] LINE OA Messaging API 已啟用
- [ ] Google Calendar OAuth 已設定
