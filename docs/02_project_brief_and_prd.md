# 專案簡報與產品需求文件 (PRD) - n8n 個人品牌內容分發平台

> **版本:** v1.0 | **更新:** 2026-03-17 | **狀態:** 草稿

---

## 1. 專案總覽

| 項目 | 內容 |
| :--- | :--- |
| **專案名稱** | Personal Content Distributor v2（n8n 個人品牌內容分發平台） |
| **狀態** | 規劃中 |
| **目標發布日期** | 2026-04-30（MVP） |
| **核心團隊** | PM/Lead Engineer: kuanwei |

### 與 v1 的主要差異

| 項目 | v1（原始規劃） | v2（本版） |
| :--- | :--- | :--- |
| **內容管理** | Google Sheets 作為輕量 CMS | Web 介面，使用者直接在瀏覽器編輯貼文 |
| **發佈機制** | n8n 排程讀取 Sheets | Web 觸發 + n8n Webhook 排程發佈 |
| **監控能力** | Google Sheets Log 回寫 | Web 監控儀表板，即時查看各平台回覆與成效 |
| **互動追蹤** | 不在範圍 | 定時監控貼文，抓取各平台回覆/互動數據 |

---

## 2. 商業目標

| 項目 | 內容 |
| :--- | :--- |
| **背景與痛點** | 1. 個人品牌經營者需在多平台重複貼文，格式各異且容易出錯 2. 發佈成功與否缺少集中紀錄，失敗難追查 3. 各平台回覆/互動分散，無法統一監控 4. Google Sheets 作為 CMS 體驗不佳，非技術用戶難以上手 |
| **策略契合度** | 以 Web 前端提升使用體驗，結合 n8n 自動化能力，打造個人可用的內容分發與監控平台 |
| **成功指標** | 主要: 單一介面完成多平台發佈，發佈成功率 ≥ 95% / 次要: 監控儀表板可在 5 分鐘內反映各平台最新互動數據 |

---

## 3. 使用者故事與允收標準

### Epic 1: 內容管理與發佈

| ID | 描述 (As a / I want to / So that) | 允收標準 | 優先級 |
| :--- | :--- | :--- | :--- |
| US-001 | As a 內容建立者, I want to 在 Web 介面上編輯貼文（標題、文案、圖片、排程時間、目標平台）, so that 我不需要操作 Google Sheets。 | 1. 可建立/編輯/刪除貼文 2. 支援富文本或 Markdown 編輯 3. 可預覽各平台格式 | P0 |
| US-002 | As a 內容建立者, I want to 設定排程時間讓系統自動發佈, so that 我不需要守在電腦前手動發文。 | 1. 可選擇立即發佈或排程 2. 排程時間到時自動觸發 n8n 工作流 3. 發佈狀態即時更新 | P0 |
| US-003 | As a 內容建立者, I want to 同一份母內容自動轉成各平台適合的格式, so that 我不需要為每個平台分別調整。 | 1. 支援平台專屬文案欄位覆寫 2. 自動適配各平台字數/格式限制 | P0 |
| US-004 | As a 管理者, I want to 知道每個平台是否發送成功、外部貼文 ID 與失敗原因, so that 我能快速定位問題。 | 1. 發佈結果即時顯示在 Web 介面 2. 可查看詳細錯誤日誌 | P0 |
| US-005 | As a 管理者, I want to 對失敗的平台進行單獨補發, so that 不需要整批重跑。 | 1. 可選擇特定平台重新發佈 2. 已成功平台不會重複發送 | P1 |

### Epic 2: 監控與互動追蹤

| ID | 描述 (As a / I want to / So that) | 允收標準 | 優先級 |
| :--- | :--- | :--- | :--- |
| US-006 | As a 管理者, I want to 在監控儀表板看到所有已發佈貼文的狀態總覽, so that 我能一眼掌握全局。 | 1. 顯示各平台發佈狀態（成功/失敗/待發） 2. 支援篩選與排序 | P0 |
| US-007 | As a 管理者, I want to 看到各平台貼文的回覆與互動數據（讚、留言、分享）, so that 我能評估內容成效。 | 1. 定時從各平台 API 抓取互動數據 2. 數據呈現在監控儀表板 | P1 |
| US-008 | As a 管理者, I want to 在儀表板集中查看各平台的留言/回覆內容, so that 我不需要逐一登入各平台查看。 | 1. 顯示最新留言/回覆 2. 標示來源平台 3. 支援時間排序 | P1 |
| US-009 | As a 管理者, I want to 當貼文互動異常（如大量負評或零互動）時收到通知, so that 我能及時處理。 | 1. 可設定告警規則 2. 透過 Email/LINE 通知 | P2 |

---

## 4. 範圍與限制

| 項目 | 內容 |
| :--- | :--- |
| **功能範圍 (In Scope)** | - Web 前端：貼文編輯器、發佈管理、監控儀表板 - 後端 API：內容 CRUD、排程管理、n8n Webhook 整合 - n8n 工作流：多平台分發（Facebook Page、Instagram Professional、X、LINE Official Account）、定時監控貼文互動 - 監控數據：各平台貼文狀態、互動數據（讚/留言/分享）、回覆內容彙整 |
| **非功能需求** | 性能: 頁面載入 < 2s、API 回應 < 500ms / 安全: API Token 不硬編碼、用戶認證 / 可用性: 支援主流瀏覽器 |
| **不做什麼 (Out of Scope)** | - 留言回覆功能（僅監控，不在 Web 上回覆） - 私訊管理 - 完整社群分析（如粉絲成長趨勢、最佳發文時段） - 多租戶/團隊協作 - AI 自動生成內容 - 付費/商業化功能 - 複雜多媒體工作流（Reels、自動裁圖、影片轉檔） |
| **假設與依賴** | 假設: 使用者已有各平台開發者帳號與 API 權限 / 依賴: n8n 自架或雲端實例、各平台 API 穩定性 |

---

## 5. 系統架構概要

### 5.1 技術堆疊（建議）

| 層級 | 技術 | 說明 |
| :--- | :--- | :--- |
| **前端** | Next.js / React | Web 介面：貼文編輯、發佈管理、監控儀表板 |
| **後端 API** | Next.js API Routes / Node.js | 內容 CRUD、排程管理、與 n8n 整合 |
| **資料庫** | PostgreSQL / SQLite | 儲存貼文、發佈紀錄、監控數據 |
| **自動化引擎** | n8n | 多平台分發、定時監控、錯誤重試 |
| **目標平台** | Facebook Page、Instagram Professional、X、LINE Official Account | 社群分發目標 |

### 5.2 架構分層

| 層級 | 元件 | 責任 |
| :--- | :--- | :--- |
| **Presentation Layer** | Web 前端 | 貼文編輯器、發佈管理介面、監控儀表板 |
| **API Layer** | 後端 API | 內容 CRUD、排程管理、Webhook 接收 n8n 回報 |
| **Data Layer** | 資料庫 | 儲存 content_queue、publish_logs、monitor_data |
| **Orchestration Layer** | n8n Main Workflow | Webhook 觸發/排程觸發、篩選資料、路由到各平台 adapter |
| **Adapter Layer** | FB / IG / X / LINE Adapters | 格式轉換、權限驗證、API 呼叫、解析回傳 |
| **Monitor Layer** | n8n Monitor Workflow | 定時抓取各平台貼文互動數據，回寫至資料庫 |
| **Notification Layer** | Email / LINE Admin Alert | 發佈失敗或互動異常時通知管理者 |

### 5.3 核心流程

**發佈流程：**
1. 使用者在 Web 介面建立/編輯貼文，設定排程時間與目標平台
2. 後端 API 儲存至資料庫，排程時間到時透過 n8n Webhook 觸發發佈
3. n8n 工作流讀取待發佈資料，標準化母文案，依平台路由
4. 各平台 adapter 呼叫對應 API 並取得結果
5. n8n 透過 Webhook 回報發佈結果至後端 API，更新資料庫
6. Web 介面即時顯示發佈狀態

**監控流程：**
1. n8n 定時排程（如每 30 分鐘）觸發監控工作流
2. 從資料庫讀取已發佈且有外部 post_id 的貼文
3. 各平台 adapter 呼叫 API 抓取互動數據（讚、留言、分享、回覆內容）
4. 回寫至資料庫 monitor_data 表
5. Web 監控儀表板即時呈現最新數據

### 5.4 資料模型

**content_queue（貼文佇列）**

| 欄位 | 型別 | 說明 |
| :--- | :--- | :--- |
| id | UUID | 每筆內容的唯一識別碼 |
| title | VARCHAR | 內容標題 |
| master_caption | TEXT | 母文案 |
| image_url | VARCHAR | 單張圖片連結 |
| platforms | VARCHAR | 目標平台清單（fb,ig,x,line） |
| publish_at | TIMESTAMP | 排程發佈時間 |
| status | VARCHAR | 整體狀態（draft/queued/publishing/success/partial_success/failed） |
| fb_caption | TEXT | Facebook 專屬文案 |
| ig_caption | TEXT | Instagram 專屬文案 |
| x_caption | TEXT | X 專屬文案 |
| line_message | TEXT | LINE 專屬訊息 |
| retry_count | INTEGER | 重試次數 |
| last_error | TEXT | 最近一次錯誤摘要 |
| created_at | TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | 更新時間 |

**publish_logs（發佈紀錄）**

| 欄位 | 型別 | 說明 |
| :--- | :--- | :--- |
| log_id | UUID | 單次平台執行的唯一編號 |
| content_id | UUID | 對應 content_queue.id |
| platform | VARCHAR | 本次執行的平台 |
| status | VARCHAR | 結果狀態（success/failed） |
| external_post_id | VARCHAR | 平台回傳的貼文 ID |
| response_summary | TEXT | API 回傳摘要 |
| workflow_execution_id | VARCHAR | n8n execution id |
| created_at | TIMESTAMP | 執行時間 |

**monitor_data（監控數據）**

| 欄位 | 型別 | 說明 |
| :--- | :--- | :--- |
| id | UUID | 唯一識別碼 |
| content_id | UUID | 對應 content_queue.id |
| platform | VARCHAR | 平台名稱 |
| external_post_id | VARCHAR | 平台貼文 ID |
| likes | INTEGER | 按讚數 |
| comments | INTEGER | 留言數 |
| shares | INTEGER | 分享數 |
| recent_replies | JSON | 最新回覆內容（陣列） |
| fetched_at | TIMESTAMP | 抓取時間 |

### 5.5 狀態機

| 狀態 | 意義 | 轉移條件 |
| :--- | :--- | :--- |
| draft | 草稿，尚未排程 | 使用者設定排程後轉為 queued |
| queued | 已排程，等待發送 | 排程時間到且 n8n 開始處理時轉為 publishing |
| publishing | 正在呼叫各平台 API | 全部成功轉 success |
| partial_success | 部分成功、部分失敗 | 可針對失敗平台補發 |
| success | 全部平台發佈成功 | 終態 |
| failed | 全部失敗或中止 | 人工修正或自動重試後可回 queued |

### 5.6 錯誤處理策略

- 4xx 類型錯誤視為配置或資料問題，記錄並停止該平台重試
- 5xx、timeout 或暫時性錯誤依 retry_count 自動重試 1-3 次
- 單一平台失敗不阻斷其他平台發送
- 已成功且有外部 post_id 的平台不重複發送
- 所有錯誤記錄至 publish_logs，Web 介面可查詢

---

## 6. MVP 範圍與驗收標準

### MVP 功能清單

| 功能 | MVP 範圍 | 優先級 |
| :--- | :--- | :--- |
| Web 貼文編輯器 | 基本 CRUD、排程設定、平台選擇 | P0 |
| 多平台發佈 | Facebook Page（文字+連結）、X（純文字）、LINE（文字訊息） | P0 |
| 發佈狀態追蹤 | Web 介面顯示各平台發佈結果 | P0 |
| 手動補發 | 對失敗平台單獨重發 | P1 |
| 監控儀表板 | 各平台互動數據（讚/留言/分享） | P1 |
| 回覆內容彙整 | 集中顯示各平台留言/回覆 | P1 |
| Instagram 發佈 | 單張圖片 + caption | P2 |
| 互動異常告警 | Email/LINE 通知 | P2 |

### MVP 驗收標準

1. 使用者可在 Web 介面建立貼文、設定排程與目標平台
2. 排程時間到時，n8n 自動將內容發佈至選定平台
3. 至少 3 個平台（FB、X、LINE）可完成成功發佈與結果回寫
4. 單一平台失敗時，不影響其他平台完成發送
5. Web 監控儀表板可顯示各平台發佈狀態
6. 可透過 Web 介面對失敗平台進行手動補發

---

## 7. 開發階段建議

| 階段 | 目標 | 產出 | 建議天數 |
| :--- | :--- | :--- | :--- |
| Phase 1 | 基礎架構 | Web 前端骨架 + 後端 API + 資料庫 + n8n Webhook 串接 | 5-7 天 |
| Phase 2 | 打通最小閉環 | Web 建立貼文 -> n8n -> X 發佈 -> 狀態回寫至 Web | 3-5 天 |
| Phase 3 | 多平台擴展 | 加入 Facebook、LINE adapter，平台路由邏輯 | 3-5 天 |
| Phase 4 | 監控功能 | n8n 定時監控工作流 + Web 監控儀表板 | 5-7 天 |
| Phase 5 | 完善與擴展 | Instagram 支援、補發機制、告警通知、UI 優化 | 5-7 天 |

---

## 8. 待辦問題與決策

| ID | 描述 | 狀態 | 備註 |
| :--- | :--- | :--- | :--- |
| Q-001 | 前端框架選型（Next.js vs 其他） | 待決定 | 需考慮 SSR 需求與開發效率 |
| Q-002 | 資料庫選型（PostgreSQL vs SQLite） | 待決定 | 單人使用 SQLite 足夠，多人則需 PostgreSQL |
| Q-003 | n8n 部署方式（自架 vs 雲端） | 待決定 | 影響 Webhook 串接方式 |
| Q-004 | 使用者認證機制（是否需要登入） | 待討論 | 單人使用可簡化，多人需完整認證 |
| Q-005 | 監控數據抓取頻率 | 待決定 | 需考慮各平台 API rate limit |
| D-001 | 從 Google Sheets CMS 改為 Web 介面 | 已決定 | 提升使用體驗，支援更豐富的互動功能 |
| D-002 | 新增監控儀表板功能 | 已決定 | 集中查看各平台回覆與互動數據 |
