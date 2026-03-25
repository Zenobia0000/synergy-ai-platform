# Personal Content Distributor v2

> **n8n 個人品牌內容分發平台** — Web 介面管理多平台貼文發佈與監控

在單一 Web 介面建立貼文，透過 n8n 自動分發至 Facebook Page、X、LINE、Instagram，並集中追蹤發佈狀態與互動數據。

---

## 技術棧

| 層級 | 技術 | 說明 |
| :--- | :--- | :--- |
| 前端 | Vite + React 18 + TypeScript | shadcn/ui + Tailwind CSS |
| 後端 | FastAPI (Python) | REST API、排程管理、Webhook |
| 資料庫 | PostgreSQL 16 | content_queue、publish_logs、monitor_data |
| 自動化 | n8n (本地自架) | 多平台分發、定時監控 |
| 目標平台 | FB Page、IG、X、LINE OA | 社群分發目標 |

---

## 快速開始

### 前置需求

- Node.js 18+
- Python 3.11+、[uv](https://docs.astral.sh/uv/)
- Docker Desktop (PostgreSQL + n8n)

### 首次環境建立（手動）

```bash
# 1. 建立 Python 虛擬環境
uv venv .venv

# 2. 啟用虛擬環境
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate     # Linux/Mac

# 3. 安裝 Python 套件
uv pip install -r backend/requirements.txt

# 4. 建立後端環境變數
cp backend/.env.example backend/.env   # 編輯 .env 填入實際設定

# 5. 安裝前端套件
cd frontend && npm install --legacy-peer-deps && cd ..
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
uvicorn app.main:app --reload --port 8888
```

**4. 前端**

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

**5. n8n**

- 管理介面: http://localhost:5678
- 匯入 `n8n/workflows/publish_main.json`
- 配置平台 API Credentials

### 服務入口

| 服務 | 網址 |
| :--- | :--- |
| 前端 Web UI | http://localhost:3000 |
| 後端 API 文檔 | http://localhost:8888/api/v1/docs |
| 後端 Health | http://localhost:8888/health |
| n8n 管理介面 | http://localhost:5678 |

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
│   └── workflows/
├── docs/                     # 專案文檔 (17 份，編號排序)
├── docker-compose.yml        # PostgreSQL + n8n
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
| DELETE | `/api/v1/contents/:id` | 刪除 (僅 draft) |
| POST | `/api/v1/contents/:id/schedule` | 設定排程 |
| DELETE | `/api/v1/contents/:id/schedule` | 取消排程 |
| POST | `/api/v1/contents/:id/publish` | 立即發佈 |
| POST | `/api/v1/webhooks/publish-result` | n8n 回報發佈結果 |

所有回應使用統一信封格式 `{ success, data, error, meta }`。

---

## 開發進度

| Phase | 狀態 | 內容 |
| :--- | :--- | :--- |
| Phase 0: 初始化 | ✅ 完成 | 專案結構、文檔、WBS |
| Phase 1: 基礎架構 | ✅ 完成 | FastAPI + PostgreSQL + Alembic + React Query |
| Phase 2: 最小閉環 | ✅ 完成 | CRUD API + 前端串接 + n8n Workflow 模板 + 排程觸發 |
| Phase 3: 多平台擴展 | ⏳ 待處理 | FB、LINE adapter |
| Phase 4: 監控功能 | ⏳ 待處理 | 監控儀表板 + 互動數據 |
| Phase 5: 完善擴展 | ⏳ 待處理 | IG、告警、認證預留、E2E |

**MVP 目標:** 2026-04-30

詳細 WBS: [.claude/taskmaster-data/wbs.md](.claude/taskmaster-data/wbs.md)

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
