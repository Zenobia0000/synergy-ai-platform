# CLAUDE.md - Synergy AI Platform (Monorepo)

> **專案:** synergy-ai-platform
> **描述:** Synergy AI 平台 monorepo，含兩個 POC 模組
> **建立:** 2026-04-22
> **結構:** 資料夾式 monorepo，各模組獨立技術棧、獨立啟動

## 模組

| 模組 | 路徑 | 功能 | 技術棧 |
| :--- | :--- | :--- | :--- |
| module1-distributor | `modules/module1-distributor/` | 個人品牌內容分發（Web + n8n 自動化） | FastAPI + PostgreSQL + Vite/React 18 + shadcn/ui + n8n |
| module2-questionnaire | `modules/module2-questionnaire/` | AI 問卷評估（健康問卷 → 行銷建議） | FastAPI (uv) + Vite/React 19 + Tailwind v4 + Apple tokens |

每個模組都有自己的 `CLAUDE.md`，進入該目錄工作時以子模組為主。根層 `CLAUDE.md`（本檔）只定義跨模組規範。

## 切換工作區

在 Claude Code 中主要有兩種模式：

### 模式 A：跨模組工作（停在根目錄）
- Claude 可同時讀取兩個模組的程式碼與文件
- 適合做整合、共用邏輯抽取、跨模組重構
- 指令跑全域時（如 `grep`、`glob`），CWD = `D:\project\synergy\`

### 模式 B：單模組專注開發（進入子模組）
- `cd modules/module2-questionnaire/`（或 module1）後做開發
- 子模組 CLAUDE.md 的規則優先套用
- build / dev / test 指令都從子模組根跑

## 共用資源（放根目錄）

- `.claude/rules/` — 編碼、測試、安全等通用規則
- `.claude/ui/` — UI 設計系統（Apple 等 57 套）
- `VibeCoding_Workflow_Templates/` — 流程模板（PRD、ADR、IA 等）
- `.gitignore`、`.gitattributes` — 全 repo 通用

## 不共用（各模組自己）

- `backend/`、`frontend/`、`docs/`、`tests/` 在各模組內
- 依賴清單（`package.json`、`pyproject.toml`、`requirements.txt`）各自獨立
- 各模組可以有不同 Python/Node 版本、不同套件管理工具

## Dev server 起法

### module2-questionnaire
```
cd modules/module2-questionnaire/frontend && npm install && npm run dev   # :3000
cd modules/module2-questionnaire/backend  && uv sync && uv run uvicorn app.main:app --reload   # :8000
```

### module1-distributor
```
cd modules/module1-distributor/frontend && npm install && npm run dev
cd modules/module1-distributor/backend  && pip install -r requirements.txt && uvicorn app.main:app --reload
# n8n 與 PostgreSQL：docker compose up（看 modules/module1-distributor/docker-compose.yml）
```

兩模組的後端預設 port 會衝突，需要時用環境變數 `PORT` 或 uvicorn `--port` 自行分流（例如 module1 用 :8001、module2 用 :8000）。

## Git 歷史

- `modules/module1-distributor/` 的歷史透過 `git subtree add` 匯入自原 `d:\project\n8n_rpa_post`
- `modules/module2-questionnaire/` 是本 repo 初始 commit 直接帶入
- 後續兩模組都在此 repo 維護，原 `d:\project\n8n_rpa_post` 不再獨立開發

## 共用開發守則（跨模組通用）

見 `.claude/rules/`：
- `coding-style.md` — 不可變性、檔案大小
- `development-workflow.md` — 研究先行、Plan-TDD-Review
- `security.md` — commit 前安全檢查
- `testing.md` — 80%+ 覆蓋率
- `git-workflow.md` — Conventional Commits
- `ui-design.md` — UI 風格載入與檢查（三階段）

## 預計共用

未來兩模組共同需要時，會在根層新增：

- `shared/` — 共用 TS 型別、Python schema、LLM prompt 模板
- `docs/adr/` — 跨模組架構決策記錄

這些在 POC 階段尚未抽取，避免過早抽象。
