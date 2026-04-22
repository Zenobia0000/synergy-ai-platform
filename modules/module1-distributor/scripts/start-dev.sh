#!/bin/bash
# =============================================================
# Personal Content Distributor v2 - 開發環境啟動腳本
# 用法: bash scripts/start-dev.sh
# =============================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()   { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()  { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

# --------------------------------------------------
# 1. 檢查前置需求
# --------------------------------------------------
log "檢查前置需求..."

command -v docker >/dev/null 2>&1 || fail "Docker 未安裝"
docker info >/dev/null 2>&1     || fail "Docker Desktop 未啟動，請先開啟"
ok "Docker Desktop 運行中"

command -v node >/dev/null 2>&1  || fail "Node.js 未安裝"
ok "Node.js $(node --version)"

if [ ! -d "$PROJECT_ROOT/.venv" ]; then
  fail "Python 虛擬環境不存在，請先執行: uv venv .venv && uv pip install -r backend/requirements.txt"
fi
ok "Python 虛擬環境存在"

# --------------------------------------------------
# 1.5 檢查 backend/.env (validate_runtime 需要非空 secrets)
# --------------------------------------------------
if [ ! -f "$PROJECT_ROOT/backend/.env" ]; then
  fail "backend/.env 不存在 — 請執行: cp backend/.env.example backend/.env 然後填入 N8N_WEBHOOK_SECRET 與 SECRET_KEY"
fi
if grep -q "N8N_WEBHOOK_SECRET=your-webhook-secret-here" "$PROJECT_ROOT/backend/.env"; then
  fail "backend/.env 仍是預設 placeholder — 請編輯並填入真實的 N8N_WEBHOOK_SECRET / SECRET_KEY"
fi
if grep -qE "^SECRET_KEY=(change-me-in-production)?$" "$PROJECT_ROOT/backend/.env"; then
  fail "backend/.env 的 SECRET_KEY 仍是預設值或為空 — 請填入真實值"
fi
ok "backend/.env 已設定"

# --------------------------------------------------
# 2. 啟動 PostgreSQL + n8n (Docker)
# --------------------------------------------------
log "檢查 Docker 基礎設施 (postgres + n8n)..."

NEED_INFRA=0
docker ps --format '{{.Names}}' | grep -q content_distributor_db || NEED_INFRA=1
docker ps --format '{{.Names}}' | grep -q content_distributor_n8n || NEED_INFRA=1

if [ "$NEED_INFRA" -eq 1 ]; then
  log "啟動 postgres + n8n..."
  docker compose up -d postgres n8n
  # 等待 postgres healthy
  for i in $(seq 1 15); do
    if docker exec content_distributor_db pg_isready -U postgres >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if docker exec content_distributor_db pg_isready -U postgres >/dev/null 2>&1; then
    ok "PostgreSQL + n8n 啟動成功"
  else
    fail "PostgreSQL 啟動逾時"
  fi
else
  ok "PostgreSQL + n8n 已在運行"
fi

# --------------------------------------------------
# 3. 執行 Alembic migration (如有新的)
# --------------------------------------------------
log "檢查資料庫 migration..."
# shellcheck disable=SC1091
source "$PROJECT_ROOT/.venv/Scripts/activate" 2>/dev/null || source "$PROJECT_ROOT/.venv/bin/activate"
cd "$PROJECT_ROOT/backend"
if ! alembic upgrade head; then
  fail "Alembic migration 失敗 — 檢查上方錯誤訊息"
fi
ok "資料庫 migration 完成"

# --------------------------------------------------
# 4. 啟動後端 (背景)
# --------------------------------------------------
log "啟動 FastAPI 後端 (port 8000)..."

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
  warn "Port 8000 已有服務運行，跳過啟動"
else
  cd "$PROJECT_ROOT/backend"
  uvicorn app.main:app --reload --port 8000 &
  BACKEND_PID=$!

  # 等待啟動
  for i in $(seq 1 10); do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done

  if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    ok "FastAPI 後端啟動成功 (PID: $BACKEND_PID)"
  else
    fail "FastAPI 後端啟動失敗 — 檢查 backend/.env 的 secrets 是否填妥"
  fi
fi

# --------------------------------------------------
# 5. 安裝前端依賴 (如需要)
# --------------------------------------------------
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
  log "安裝前端依賴..."
  npm install
  ok "前端依賴安裝完成"
fi

# --------------------------------------------------
# 6. 啟動前端 (前台)
# --------------------------------------------------
log "啟動 Vite 前端 (port 3000)..."
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  開發環境就緒！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "  前端:    ${CYAN}http://localhost:3000${NC}"
echo -e "  後端:    ${CYAN}http://localhost:8000${NC}"
echo -e "  API 文檔: ${CYAN}http://localhost:8000/api/v1/docs${NC}"
echo -e "  n8n:     ${CYAN}http://localhost:5678${NC}"
echo ""
echo -e "  按 ${YELLOW}Ctrl+C${NC} 停止前端，後端會一起停止"
echo ""

# 前端跑在前台，Ctrl+C 時清理後端
cleanup() {
  echo ""
  log "正在停止服務..."
  [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && ok "後端已停止"
  ok "開發環境已關閉"
}
trap cleanup EXIT

npm run dev
