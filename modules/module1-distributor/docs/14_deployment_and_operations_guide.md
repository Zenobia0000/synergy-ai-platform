# 部署與運維指南 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19

---

## 1. 部署架構

### 本地開發環境 (MVP)

```
┌─────────────────────────────────────────────────┐
│  Docker Compose (localhost)                      │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Frontend │  │ FastAPI  │  │   n8n    │      │
│  │ Vite Dev │  │ Uvicorn  │  │          │      │
│  │ :5173    │  │ :8000    │  │ :5678    │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
│       │              │              │             │
│       │    REST API   │   Webhook    │             │
│       └──────────────┤◄─────────────┘             │
│                      │                            │
│              ┌───────┴────────┐                   │
│              │  PostgreSQL    │                   │
│              │  :5432         │                   │
│              └────────────────┘                   │
└─────────────────────────────────────────────────┘
```

### 基礎設施元件

| 元件 | 用途 | 技術 | 連接埠 |
| :--- | :--- | :--- | :--- |
| 前端 | Web 介面 | Vite Dev Server | 5173 |
| 後端 | REST API | FastAPI + Uvicorn | 8000 |
| 自動化 | 工作流引擎 | n8n | 5678 |
| 資料庫 | 資料持久化 | PostgreSQL 16 | 5432 |

---

## 2. 環境配置

### Docker Compose (建議)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: content_distributor
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n:latest
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD:-postgres}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER:-admin}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD:-admin}
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      - postgres

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD:-postgres}@postgres:5432/content_distributor
      - N8N_BASE_URL=http://n8n:5678
      - N8N_WEBHOOK_SECRET=${N8N_WEBHOOK_SECRET}
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
  n8n_data:
```

### 本地開發 (不使用 Docker)

```bash
# 1. 啟動 PostgreSQL (已安裝)
# 2. 建立資料庫
createdb content_distributor

# 3. 後端
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # 編輯 .env
alembic upgrade head       # 執行 migration
uvicorn app.main:app --reload --port 8000

# 4. 前端
cd frontend
npm install
npm run dev                # http://localhost:5173

# 5. n8n (已安裝)
n8n start                  # http://localhost:5678
```

---

## 3. 部署檢查清單

### 首次部署

- [ ] PostgreSQL 已啟動且可連線
- [ ] 資料庫 `content_distributor` 已建立
- [ ] `.env` 已配置所有必要環境變數
- [ ] Alembic migration 已執行 (`alembic upgrade head`)
- [ ] FastAPI 啟動且 `/health` 回應正常
- [ ] n8n 啟動且管理介面可存取
- [ ] 前端啟動且可載入頁面
- [ ] 前端可成功呼叫後端 API (CORS 正確)

### 日常更新

- [ ] 拉取最新程式碼
- [ ] 檢查是否有新的 migration (`alembic upgrade head`)
- [ ] 檢查是否有新的依賴 (`pip install -r requirements.txt` / `npm install`)
- [ ] 重啟後端服務
- [ ] 驗證 `/health` 端點

---

## 4. 監控與告警

### 健康檢查

| 端點 | 預期回應 | 檢查頻率 |
| :--- | :--- | :--- |
| `GET /health` | `{"status": "ok", "version": "0.1.0"}` | 每分鐘 |
| n8n UI | HTTP 200 | 每 5 分鐘 |
| PostgreSQL | 連線成功 | 每分鐘 |

### 關鍵指標

| 類別 | 指標 | 閾值 |
| :--- | :--- | :--- |
| API | 回應時間 P95 | < 500ms |
| API | 錯誤率 | < 1% |
| 發佈 | 成功率 | ≥ 95% |
| n8n | Workflow 執行成功率 | ≥ 95% |
| DB | 連線數 | < 20 |

### 告警規則

| 名稱 | 條件 | 通知方式 |
| :--- | :--- | :--- |
| 發佈失敗 | 單次發佈全平台失敗 | n8n → Email/LINE |
| API 無回應 | `/health` 連續 3 次失敗 | n8n 排程檢查 |
| 磁碟空間不足 | 使用率 > 90% | 系統監控 |

---

## 5. 備份與恢復

### 資料庫備份

```bash
# 手動備份
pg_dump -U postgres content_distributor > backup_$(date +%Y%m%d).sql

# 定時備份 (crontab)
0 2 * * * pg_dump -U postgres content_distributor | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz

# 恢復
psql -U postgres content_distributor < backup_20260319.sql
```

### n8n Workflow 備份

- 匯出 Workflow JSON 至 `n8n/workflows/` 目錄
- 納入 Git 版本控制
- 重大變更前手動匯出

---

## 6. 故障排除

### 常見問題

| 問題 | 可能原因 | 解決方案 |
| :--- | :--- | :--- |
| 前端無法呼叫 API | CORS 設定錯誤 | 檢查 `CORS_ORIGINS` 是否包含前端 URL |
| n8n Webhook 失敗 | FastAPI 未啟動 | 確認後端服務運行中 |
| 資料庫連線失敗 | PostgreSQL 未啟動或密碼錯誤 | 檢查 `DATABASE_URL` 和 PG 狀態 |
| Migration 失敗 | 資料庫 schema 衝突 | `alembic downgrade -1` 後重試 |
| 發佈至平台失敗 | API Token 過期 | 更新 n8n Credentials 中的 Token |

### 日誌位置

| 服務 | 日誌來源 |
| :--- | :--- |
| FastAPI | stdout (uvicorn) |
| n8n | n8n UI → Executions |
| PostgreSQL | Docker logs / pg_log |
| 前端 | 瀏覽器 Console |

---

## 7. 未來擴展 (超出 MVP)

| 需求 | 方案 |
| :--- | :--- |
| 公網部署 | Nginx reverse proxy + HTTPS (Let's Encrypt) |
| 多設備存取 | 部署至 VPS + 認證機制 |
| 高可用 | Docker Swarm / K8s |
| CDN | 前端靜態檔案部署至 Cloudflare Pages |
