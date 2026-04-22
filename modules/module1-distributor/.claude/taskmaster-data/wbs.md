# WBS - Personal Content Distributor v2

**建立日期:** 2026-03-19
**最後更新:** 2026-04-08
**開發模式:** MVP
**專案描述:** n8n 個人品牌內容分發平台 — Web 介面管理多平台貼文發佈與監控

---

## 任務清單

### Phase 1: 基礎架構 (5-7 天)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 1.1 | 專案初始化與結構建立 | ✅ 完成 | 高 | - | 0.5h | CLAUDE.md、目錄結構 |
| 1.2 | 需求分析與文件整理 | ✅ 完成 | 高 | - | 1h | PRD、架構文件已存在 |
| 1.3 | PostgreSQL 資料庫設定 | ✅ 完成 | 高 | 1.1 | 1h | Docker Compose + PostgreSQL 16 |
| 1.4 | Alembic migration 初始化 | ✅ 完成 | 高 | 1.3 | 1h | 3 tables 建立完成 |
| 1.5 | FastAPI 基礎 API 骨架 | ✅ 完成 | 高 | 1.3 | 2h | 10 endpoints 已驗證 |
| 1.6 | 前端 API 串接層建立 | ✅ 完成 | 高 | 1.5 | 2h | API client + 7 hooks |
| 1.7 | Docker Compose 開發環境 | ⏭️ 跳過 | 中 | 1.3 | 1h | 已有 docker-compose.yml，後續補完 |

### Phase 2: 最小閉環 — Web → n8n → X 發佈 (3-5 天)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 2.1 | Content CRUD API 完整實作 | ✅ 完成 | 高 | 1.5 | 3h | 已在 1.5 完成，含驗證、分頁、篩選 |
| 2.2 | 前端貼文編輯器頁面 | ✅ 完成 | 高 | 2.1 | 4h | 建立/編輯/發佈/排程，API 串接完成 |
| 2.3 | 前端貼文列表頁面 | ✅ 完成 | 高 | 2.1 | 3h | 篩選/搜尋/刪除/發佈，輪詢 10s |
| 2.4 | n8n 發佈 Workflow 建立 (IG) | ✅ 完成 | 高 | 2.1 | 3h | 模板已建立，需在 n8n UI 匯入配置 |
| 2.5 | Webhook 回報 API (n8n → Backend) | ✅ 完成 | 高 | 2.1 | 2h | 已在 1.5 完成 webhooks.py |
| 2.6 | 排程觸發機制 | ✅ 完成 | 高 | 2.4, 2.5 | 2h | 30s 輪詢 + n8n webhook 觸發 |
| 2.7 | 發佈狀態即時更新 | ✅ 完成 | 高 | 2.5 | 2h | React Query 10s 輪詢已實作 |

### Phase 2.5: Phase 3 前置修復（Code Review 必修項，2026-04-08）

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 2.8 | C1: Webhook HMAC + secret fail-fast | ✅ 完成 | 高 | 2.5 | 0.5h | hmac.compare_digest + validate_runtime() |
| 2.9 | C2: Scheduler 競爭條件修復 | ✅ 完成 | 高 | 2.6 | 0.5h | UPDATE...RETURNING 原子 claim + retry cap |
| 2.10 | C3: 後端最小測試套件（15 tests） | ✅ 完成 | 高 | 2.1~2.7 | 1.5h | pytest + httpx + aiosqlite，覆蓋率 66% |
| 2.11 | H1: /schedule Pydantic ScheduleRequest | ✅ 完成 | 高 | 2.1 | 0.2h | 取代手寫 dict 解析 |
| 2.12 | H2: delete_content 204 status_code 修復 | ✅ 完成 | 中 | 2.1 | 0.2h | 錯誤路徑改 Response/JSONResponse |
| 2.13 | H4: PublishLog (content_id, platform) UNIQUE | ✅ 完成 | 高 | 2.5 | 0.4h | model + alembic migration + idempotent webhook |
| 2.14 | H5: api-client 防禦性 JSON parse | ✅ 完成 | 中 | 2.2 | 0.2h | 5xx HTML 不再炸 SyntaxError |
| 2.15 | 跨方言 connect_args 修正 | ✅ 完成 | 中 | C3 | 0.1h | sqlite vs asyncpg 差異 |
| 2.16 | 套用 Alembic migration 到 dev DB | ✅ 完成 | 高 | 2.13 | 0.1h | start-dev 腳本內含 alembic upgrade head |
| 2.17 | 修復 dev 啟動腳本 | ✅ 完成 | 中 | - | 0.5h | port 8000、.env 檢查、n8n 一併啟動、stop 改用 PID by port |
| 2.18 | 移除 lovable-tagger + 修 vite proxy port | ✅ 完成 | 中 | - | 0.2h | 解決 vite 8 peer dep 衝突 + proxy 8888→8000 |
| 2.19 | hooks 移除 stdout 污染 | ✅ 完成 | 低 | - | 0.2h | pre-tool-use / post-write 改寫 log 檔，消除 hook error |

### Phase 2.6: Instagram 端到端整合 (2026-04-08)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 2.20 | n8n IG workflow 修正 | ✅ 完成 | 高 | 2.4 | 0.6h | graph.facebook→graph.instagram、Wait 5s、error onError 連線、N8N_BLOCK_ENV_ACCESS_IN_NODE=false |
| 2.21 | Backend /publish 觸發 n8n bug 修復 | ✅ 完成 | 高 | 2.4 | 0.4h | 加 BackgroundTasks → publish_content_now，否則 status 卡 publishing |
| 2.22 | 完整 E2E 驗證 IG 發佈 | ✅ 完成 | 高 | 2.20, 2.21 | 0.3h | UI → API → n8n → IG → callback → status=success |
| 2.23 | docker-compose 注入 IG 與 webhook 環境變數 | ✅ 完成 | 高 | 2.20 | 0.1h | IG_USER_ID, IG_ACCESS_TOKEN, N8N_WEBHOOK_SECRET |
| 2.24 | MinIO 物件儲存整合 | ✅ 完成 | 中 | - | 0.5h | docker-compose 加 minio + minio-init bucket auto-create |
| 2.25 | Backend upload + proxy endpoints | ✅ 完成 | 中 | 2.24 | 0.6h | POST /uploads/image (multipart→MinIO), GET /uploads/{key} (stream proxy) |
| 2.26 | Frontend file picker UI | ✅ 完成 | 中 | 2.25 | 0.3h | CreateContent 圖片欄位整合上傳按鈕 |
| 2.27 | ngrok static domain 設定 | ✅ 完成 | 中 | 2.25 | 0.3h | PUBLIC_BASE_URL 注入 backend |
| 2.28 | 圖片預覽 ngrok interstitial 修復 | ✅ 完成 | 中 | 2.26 | 0.3h | DB 存相對 URL，trigger n8n 時才補絕對前綴 |
| 2.29 | 允許刪除失敗貼文 | ✅ 完成 | 低 | - | 0.1h | DELETABLE_STATUSES + ContentCard menu |

### Phase 3: 多平台擴展 (3-5 天)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 3.1 | X (Twitter) Adapter (n8n) | ⏳ 待處理 | 高 | 2.4 | 3h | Twitter API v2 發佈推文 |
| 3.2 | Facebook Page Adapter (n8n) | ⏳ 待處理 | 高 | 2.4 | 3h | Graph API 發佈文字+連結 |
| 3.3 | 平台路由邏輯 | ⏳ 待處理 | 高 | 3.1, 3.2 | 2h | n8n 依 platforms 欄位分派 |
| 3.4 | 平台專屬文案覆寫 | ⏳ 待處理 | 中 | 3.3 | 2h | fb_caption、x_caption 等 |
| 3.5 | 錯誤處理與重試機制 | ⏳ 待處理 | 高 | 3.3 | 2h | 4xx 停止、5xx 重試 1-3 次 |
| 3.6 | 手動補發 API + 前端 | ⏳ 待處理 | 中 | 3.5 | 2h | 對失敗平台單獨重發 |

### Phase 4: 監控功能 (5-7 天)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 4.1 | 監控數據 API | ⏳ 待處理 | 中 | 2.1 | 2h | monitor_data CRUD + 聚合查詢 |
| 4.2 | n8n 監控 Workflow | ⏳ 待處理 | 中 | 3.3 | 4h | 定時抓取各平台互動數據 |
| 4.3 | 監控儀表板頁面 | ⏳ 待處理 | 中 | 4.1 | 4h | MonitorDashboard 串接 API |
| 4.4 | 回覆內容彙整顯示 | ⏳ 待處理 | 中 | 4.2 | 3h | 集中顯示各平台留言 |
| 4.5 | 互動數據圖表 | ⏳ 待處理 | 低 | 4.3 | 2h | Recharts 趨勢圖 |

### Phase 5: 完善與擴展 (5-7 天)

| # | 任務 | 狀態 | 優先級 | 依賴 | 預估 | 備註 |
|---|------|------|--------|------|------|------|
| 5.1 | LINE Official Account Adapter (n8n) | ⏳ 待處理 | 低 | 3.3 | 3h | Messaging API 推送 |
| 5.2 | 互動異常告警 | ⏳ 待處理 | 低 | 4.2 | 3h | Email/LINE 通知 |
| 5.3 | 認證機制預留接口 | ⏳ 待處理 | 低 | 1.5 | 2h | JWT middleware 骨架 |
| 5.4 | 設定頁面 | ⏳ 待處理 | 低 | 2.1 | 2h | SettingsPage 串接 |
| 5.5 | UI 優化與響應式設計 | ⏳ 待處理 | 低 | 4.3 | 3h | 行動裝置適配 |
| 5.6 | E2E 測試 | ⏳ 待處理 | 中 | 4.3 | 3h | Playwright 關鍵流程 |

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
| M0: 專案初始化 | 2026-03-19 | 1.1, 1.2 | ✅ 完成 |
| M1: 基礎架構就緒 | 2026-03-26 | 1.3~1.7 | ✅ 完成 |
| M2: 最小閉環 (IG 發佈) | 2026-04-02 | 2.1~2.7 | ✅ 完成 |
| M2.5: Phase 3 前置修復 | 2026-04-08 | 2.8~2.19 | ✅ 完成 (12/12) |
| M2.6: Instagram E2E 整合 | 2026-04-08 | 2.20~2.29 | ✅ 完成 (10/10) — IG 發佈全流程通過 |
| M3: 多平台 MVP | 2026-04-12 | 3.1~3.6 | ⏳ 待處理 |
| M4: 監控功能 | 2026-04-22 | 4.1~4.5 | ⏳ 待處理 |
| M5: MVP 完成 | 2026-04-30 | 5.1~5.6 | ⏳ 待處理 |

---

## 風險與阻塞

| 風險 | 影響 | 緩解策略 |
|------|------|----------|
| 各平台 API 權限取得 | 無法發佈/監控 | 提前申請開發者帳號，Phase 2 前完成 X API 設定 |
| n8n Webhook 本地網路限制 | n8n 無法回報結果 | 使用 localhost 通訊，部署時考慮 reverse proxy |
| 各平台 API rate limit | 監控頻率受限 | 設定合理抓取間隔（30min+），加入 rate limit 處理 |
| 單人開發時程壓力 | MVP 延期 | 嚴格控制 P0 範圍，P1/P2 視進度調整 |
