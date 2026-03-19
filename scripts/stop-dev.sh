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

log "停止 uvicorn..."
taskkill //F //IM uvicorn.exe 2>/dev/null && ok "uvicorn 已停止" || ok "uvicorn 未在運行"

log "停止 node (Vite)..."
taskkill //F //IM node.exe 2>/dev/null && ok "node 已停止" || ok "node 未在運行"

log "停止 Docker 服務..."
cd "$(dirname "$0")/.."
docker compose stop 2>/dev/null && ok "Docker 服務已停止" || ok "Docker 服務未在運行"

echo ""
ok "所有服務已停止"
