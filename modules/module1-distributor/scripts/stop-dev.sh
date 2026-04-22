#!/bin/bash
# =============================================================
# 停止所有開發服務
# 用法: bash scripts/stop-dev.sh
# =============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[INFO]${NC} $1"; }
ok()  { echo -e "${GREEN}[OK]${NC}   $1"; }

log "停止 FastAPI 後端 (port 8000)..."
# 找出佔用 8000 port 的 PID 並結束 — 比 taskkill /IM uvicorn.exe 精準
BACKEND_PID=$(netstat -ano 2>/dev/null | grep -E "TCP\s+.*:8000\s.*LISTENING" | awk '{print $NF}' | head -1)
if [ -n "$BACKEND_PID" ]; then
  taskkill //F //PID "$BACKEND_PID" >/dev/null 2>&1 && ok "後端已停止 (PID: $BACKEND_PID)" || ok "後端未在運行"
else
  ok "後端未在運行"
fi

log "停止 Vite 前端 (port 3000)..."
# 同樣依 port 找 PID，避免誤殺其他 node 程序
FRONTEND_PID=$(netstat -ano 2>/dev/null | grep -E "TCP\s+.*:3000\s.*LISTENING" | awk '{print $NF}' | head -1)
if [ -n "$FRONTEND_PID" ]; then
  taskkill //F //PID "$FRONTEND_PID" >/dev/null 2>&1 && ok "前端已停止 (PID: $FRONTEND_PID)" || ok "前端未在運行"
else
  ok "前端未在運行"
fi

log "停止 Docker 服務 (postgres + n8n)..."
cd "$(dirname "$0")/.."
docker compose stop 2>/dev/null && ok "Docker 服務已停止" || ok "Docker 服務未在運行"

echo ""
ok "所有服務已停止"
