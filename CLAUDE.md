# CLAUDE.md - n8n_rpa_post

> **專案:** Personal Content Distributor v2 (n8n 個人品牌內容分發平台)
> **描述:** Web 介面管理多平台貼文發佈與監控，結合 n8n 自動化引擎
> **語言:** TypeScript (前端) + Python (後端)
> **建立:** 2026-03-19

## 技術棧

| 層級 | 技術 | 說明 |
|------|------|------|
| 前端 | Vite + React 18 + TypeScript | shadcn/ui + Tailwind CSS |
| 後端 | FastAPI (Python) | REST API、排程管理、Webhook |
| 資料庫 | PostgreSQL | content_queue、publish_logs、monitor_data |
| 自動化 | n8n (本地自架) | 多平台分發、定時監控 |
| 目標平台 | FB Page、IG、X、LINE OA | 社群分發目標 |

## 專案結構

```
n8n_rpa_post/
├── frontend/          # Vite + React + shadcn/ui
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── types/
│       └── lib/
├── backend/           # FastAPI
│   ├── app/
│   │   ├── api/       # API routes
│   │   ├── core/      # 設定、安全
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # 業務邏輯
│   │   └── main.py    # 入口
│   ├── alembic/       # DB migrations
│   ├── tests/
│   └── requirements.txt
├── docs/              # 專案文件 (PRD、架構等)
└── n8n/               # n8n workflow JSON exports
```

## 開發流程

遵循 `.claude/WORKFLOW.md` 的標準流程：
/task-next → /plan → /tdd → /verify

## 專案規則

已載入 `.claude/rules/` 中的通用規則（自動生效）：
- coding-style: 不可變性、檔案大小
- development-workflow: 研究先行、Plan-TDD-Review
- security: commit 前安全檢查
- testing: 80%+ 覆蓋率
- git-workflow: Conventional Commits

## 禁止事項

- 不在根目錄建立原始碼檔案 → 使用 frontend/src/ 或 backend/app/
- 不建立重複檔案 (v2, enhanced_, new_) → 擴展現有
- 不硬編碼可配置的值 → 使用環境變數
- 不靜默吞噬錯誤 → 明確處理
- 不複製貼上程式碼 → 提取共用函式
- API Token / 密碼絕不進原始碼 → 使用 .env

## 強制要求

- 每完成一個功能後 commit
- 先搜尋現有實作再建立新檔案
- 前端修改必須確認 TypeScript 無型別錯誤
- 後端 API 必須有 Pydantic schema 驗證
- 資料庫變更必須透過 Alembic migration

## MVP 範圍 (2026-04-30)

- P0: Web 貼文 CRUD、排程發佈、FB/X/LINE 分發、狀態追蹤
- P1: 手動補發、監控儀表板、回覆彙整
- P2: Instagram 發佈、互動異常告警
- 認證機制: MVP 不實作，但架構預留

## 開發階段

1. Phase 1: 基礎架構 (前端骨架 + FastAPI + PostgreSQL + n8n Webhook)
2. Phase 2: 最小閉環 (Web → n8n → X 發佈 → 狀態回寫)
3. Phase 3: 多平台擴展 (Facebook、LINE adapter)
4. Phase 4: 監控功能 (n8n 定時監控 + Web 儀表板)
5. Phase 5: 完善擴展 (IG、補發、告警、UI 優化)
