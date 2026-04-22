# Synergy AI Platform

Synergy AI 平台 — 內部 POC monorepo，目前含兩個子模組。

## 模組

| 模組 | 功能 | 狀態 |
| :--- | :--- | :--- |
| [module1-distributor](modules/module1-distributor/) | Web 介面管理多平台貼文發佈與監控（FB / IG / X / LINE），結合 n8n 自動化 | POC |
| [module2-questionnaire](modules/module2-questionnaire/) | AI 問卷評估：依健康問卷產出新手教練可用的行銷建議 | POC |

## 快速開始

```bash
# 模組 2：問卷 POC
cd modules/module2-questionnaire/frontend && npm install && npm run dev

# 另開一個終端
cd modules/module2-questionnaire/backend && uv sync && uv run uvicorn app.main:app --reload
```

```bash
# 模組 1：內容分發
cd modules/module1-distributor
# 先起 PostgreSQL 與 n8n
docker compose up -d
# 啟動後端
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# 啟動前端（另開終端）
cd ../frontend && npm install && npm run dev
```

兩模組的後端預設都 listen 8000，同時跑時請指定不同 port。

## 目錄結構

```
synergy/
├── modules/
│   ├── module1-distributor/       # 貼文分發（原 n8n_rpa_post）
│   │   ├── backend/               # FastAPI + PostgreSQL
│   │   ├── frontend/              # Vite + React 18 + shadcn/ui
│   │   ├── n8n/                   # n8n workflow JSON
│   │   ├── docker-compose.yml
│   │   └── docs/
│   └── module2-questionnaire/     # AI 問卷評估
│       ├── backend/               # FastAPI (uv)
│       ├── frontend/              # Vite + React 19 + Tailwind v4
│       ├── rawdata/               # 原始問卷、產品目錄
│       ├── data/                  # 解析後 schema
│       └── docs/
├── .claude/                       # 共用 Claude Code 設定與規則
├── VibeCoding_Workflow_Templates/ # 共用文件模板
└── CLAUDE.md                      # Monorepo 入口指引
```

## 開發規則

各模組依自己的 `CLAUDE.md` 與 `docs/` 規範開發；跨模組共用規則在根 `CLAUDE.md` 與 `.claude/rules/`。

## License

見 [`LICENSE`](LICENSE)。
