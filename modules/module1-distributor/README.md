# Personal Content Distributor v2

> **n8n 個人品牌內容分發平台** — Web 介面管理多平台貼文發佈與監控

在單一 Web 介面建立貼文，透過 n8n 自動分發至 Facebook Page、X、LINE、Instagram，並集中追蹤發佈狀態與互動數據。

---

## 技術棧

| 層級 | 技術 | 說明 |
| :--- | :--- | :--- |
| 前端 | Vite + React 18 + TypeScript | shadcn/ui + Tailwind CSS，dev port 3000 |
| 後端 | FastAPI (Python) | REST API、排程管理、Webhook，dev port 8000 |
| 資料庫 | PostgreSQL 16 | content_queue、publish_logs、monitor_data |
| 物件儲存 | MinIO (S3-compatible) | 圖片上傳，私有 bucket + backend proxy |
| 自動化 | n8n (本地自架) | 多平台分發、定時監控，port 5678 |
| 公開隧道 | ngrok / cloudflared | 讓 Meta API 能抓本機上傳的圖片 |
| 目標平台 | Instagram (✅ 已串通)、FB Page、X、LINE OA | 社群分發目標 |

---

## 快速開始

### 前置需求

- Node.js 18+
- Python 3.11+、[uv](https://docs.astral.sh/uv/)（套件管理一律走 uv，禁用全域 pip）
- Docker Desktop（PostgreSQL + n8n + MinIO）
- ngrok ≥ 3.20（給 Meta API 抓本機圖片用，**或** cloudflared）

### 首次環境建立

```bash
# 1. 建立 Python 虛擬環境（root .venv）
uv venv .venv

# 2. 啟用虛擬環境
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # Linux/Mac

# 3. 安裝 Python 套件
uv pip install -r backend/requirements.txt

# 4. 建立後端環境變數
cp backend/.env.example backend/.env
#    必填：N8N_WEBHOOK_SECRET、SECRET_KEY（強隨機字串）
#    填 IG 後：IG_ACCESS_TOKEN、IG_USER_ID
#    填 ngrok 後：PUBLIC_BASE_URL=https://your-domain.ngrok-free.dev

# 5. 建立 docker-compose 環境變數
cp .env.example .env
#    必填：N8N_WEBHOOK_SECRET（要與 backend/.env 完全一致）
#    必填：IG_ACCESS_TOKEN、IG_USER_ID（n8n workflow 用）

# 6. 安裝前端套件
cd frontend && npm install && cd ..
```

### Instagram 設定（一次性）

1. IG 帳號 → 切換成 Business / Creator
2. （Facebook Login 流程）建 FB Page → Linked accounts → 連 IG
   或（Instagram Login 流程）直接走 Meta App Instagram Business Login
3. 在 [Meta for Developers](https://developers.facebook.com/apps) 建 Meta App，加 Instagram product，授權 `instagram_basic` + `instagram_content_publish`
4. Graph API Explorer 取得 Page Access Token (`EAA…` 走 `graph.facebook.com`) 或 Instagram Login Token (`IGAA…` 走 `graph.instagram.com`)
5. 取得 Instagram Business Account ID（17 位數）
6. 把 token + ID 寫進 root `.env` 的 `IG_ACCESS_TOKEN` / `IG_USER_ID`

### ngrok 設定（給 Meta 抓本機圖片）

```bash
# 1. 註冊 ngrok 並 claim 一個免費 static domain
#    https://dashboard.ngrok.com/domains
# 2. 把你的 authtoken 寫入
ngrok config add-authtoken <your-authtoken>
# 3. 啟動 tunnel（每次 dev session 都要跑）
ngrok http --domain=your-domain.ngrok-free.dev 8000
# 4. 把這個 domain 寫進 backend/.env
#    PUBLIC_BASE_URL=https://your-domain.ngrok-free.dev
```

### 一鍵啟動（推薦）

**Windows:**

```bash
scripts\start-dev.bat
```

**Linux / Mac / Git Bash:**

```bash
bash scripts/start-dev.sh
```

腳本會自動完成：Docker 啟動 → DB migration → 後端啟動 → 前端啟動。

停止所有服務：

```bash
# Windows
scripts\stop-dev.bat

# Linux / Mac / Git Bash
bash scripts/stop-dev.sh
```

### 手動啟動

如果不使用腳本，可以分步啟動：

**1. 環境準備**

```bash
cp backend/.env.example backend/.env   # 首次需要，編輯環境變數
```

**2. 啟動 Docker 基礎設施**

```bash
docker compose up -d
```

**3. 後端**

```bash
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # Linux/Mac

cd backend
uv pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**4. 前端**

```bash
cd frontend
npm install
npm run dev
```

**5. n8n**

- 管理介面: http://localhost:5678（admin/admin）
- 匯入 `n8n/workflows/publish_main.json`
- 在 n8n UI 點 **Publish**，啟用 workflow

**6. ngrok（給 IG 抓圖）**

```bash
ngrok http --domain=your-domain.ngrok-free.dev 8000
```

### 服務入口

| 服務 | 網址 | 備註 |
| :--- | :--- | :--- |
| 前端 Web UI | http://localhost:3000 | Vite dev server |
| 後端 API 文檔 | http://localhost:8000/api/v1/docs | Swagger UI |
| 後端 Health | http://localhost:8000/health | |
| n8n 管理介面 | http://localhost:5678 | admin / admin |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| MinIO S3 API | http://localhost:9000 | backend 內部使用 |

---

## 專案結構

```
n8n_rpa_post/
├── frontend/                 # Vite + React + shadcn/ui
│   └── src/
│       ├── components/       # UI 元件 (ContentCard, StatusBadge, ...)
│       ├── pages/            # 頁面 (ContentManagement, CreateContent, ...)
│       ├── hooks/            # React Query hooks (useContents, ...)
│       ├── services/         # API client (fetch 封裝)
│       └── types/            # TypeScript 型別定義
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── api/v1/           # API routes (contents, webhooks)
│   │   ├── core/             # config, database
│   │   ├── models/           # SQLAlchemy models (3 tables)
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # 業務邏輯 + 排程觸發
│   ├── alembic/              # DB migrations
│   └── tests/
├── n8n/                      # n8n workflow JSON exports
│   └── workflows/            # publish_main.json (IG via graph.instagram.com)
├── docs/                     # 專案文檔 (17 份，編號排序)
├── scripts/                  # start-dev / stop-dev (bash + bat)
├── docker-compose.yml        # PostgreSQL + n8n + MinIO + minio-init
├── .env.example              # 給 docker-compose 的 root .env 範本
└── CLAUDE.md                 # 開發規則 (SSOT)
```

---

## API 端點

| 方法 | 路徑 | 說明 |
| :--- | :--- | :--- |
| GET | `/health` | 健康檢查 |
| POST | `/api/v1/contents` | 建立貼文 |
| GET | `/api/v1/contents` | 列表 (分頁+篩選+排序) |
| GET | `/api/v1/contents/:id` | 取得單筆 |
| PUT | `/api/v1/contents/:id` | 更新貼文 |
| DELETE | `/api/v1/contents/:id` | 刪除 (允許 draft / failed) |
| POST | `/api/v1/contents/:id/schedule` | 設定排程（Pydantic ScheduleRequest）|
| DELETE | `/api/v1/contents/:id/schedule` | 取消排程 |
| POST | `/api/v1/contents/:id/publish` | 立即發佈（觸發 BackgroundTask → n8n）|
| POST | `/api/v1/uploads/image` | 上傳本機圖片到 MinIO（multipart, ≤8MB, jpg/png）|
| GET | `/api/v1/uploads/{key}` | 圖片公開 proxy（ngrok 對外，IG 透過此端點抓圖）|
| POST | `/api/v1/webhooks/publish-result` | n8n 回報發佈結果（HMAC 簽名驗證）|

所有回應使用統一信封格式 `{ success, data, error, meta }`。

---

## 開發進度

| Phase | 狀態 | 內容 |
| :--- | :--- | :--- |
| Phase 0: 初始化 | ✅ 完成 | 專案結構、文檔、WBS |
| Phase 1: 基礎架構 | ✅ 完成 | FastAPI + PostgreSQL + Alembic + React Query |
| Phase 2: 最小閉環 | ✅ 完成 | CRUD API + 前端串接 + n8n Workflow 模板 + 排程觸發 |
| Phase 2.5: 前置修復 | ✅ 完成 | Code Review CRITICAL/HIGH 修補 + 後端測試套件（15 tests, 66% cov） |
| Phase 2.6: IG E2E 整合 | ✅ 完成 | **Instagram 全流程貫通**：UI 上傳 → MinIO → ngrok → n8n → IG → 狀態回報 |
| Phase 3: 多平台擴展 | ⏳ 待處理 | X、FB Page、LINE adapter |
| Phase 4: 監控功能 | ⏳ 待處理 | 監控儀表板 + 互動數據 |
| Phase 5: 完善擴展 | ⏳ 待處理 | 告警、認證預留、E2E test |

**MVP 目標:** 2026-04-30

詳細 WBS: [.claude/taskmaster-data/wbs.md](.claude/taskmaster-data/wbs.md)

### Instagram 整合架構

```
┌─────────┐    POST /uploads      ┌─────────┐  put_object  ┌───────┐
│Frontend │ ───multipart────────► │ Backend │ ───────────► │ MinIO │
│  :3000  │                       │  :8000  │              │ :9000 │
└────┬────┘                       └────┬────┘              └───┬───┘
     │                                 │                       │
     │ POST /publish                   │                       │
     └────────────────────────────────►│                       │
                                       │ trigger n8n           │
                                       ▼                       │
                                  ┌────────┐                   │
                                  │  n8n   │                   │
                                  │ :5678  │                   │
                                  └───┬────┘                   │
                                      │ POST graph.instagram.com
                                      │ image_url=ngrok+/uploads/xxx
                                      ▼                       ▲
                              ┌───────────────┐               │ stream
                              │  Instagram    │ ─────fetch────┤
                              │ Graph API     │  via ngrok    │
                              └───────────────┘               │
                                                              │
                                            backend proxy ────┘
```

---

## 文檔

完整文檔位於 `docs/`，共 17 份：

| 類別 | 文檔 |
| :--- | :--- |
| 流程 | `01` 工作流手冊 |
| 規劃 | `02` PRD、`03` BDD 場景 |
| 架構 | `04` ADR (6 筆決策)、`05` 架構設計、`06` API 設計 |
| 設計 | `07` 模組規格、`08` 專案結構、`09` 檔案依賴、`10` 類別關係 |
| 品質 | `11` Code Review、`12` 前端架構、`17` 前端 IA |
| 安全部署 | `13` 安全檢查、`14` 部署運維 |
| 維護 | `15` 文檔維護、`16` WBS 計畫 |

---

## 開發流程

使用 Claude Code 輔助開發:

```
/task-next → /plan → /tdd → /verify
```

規則自動載入自 `.claude/rules/`（編碼風格、安全、測試、Git 等 7 條）。

---

## License

MIT
