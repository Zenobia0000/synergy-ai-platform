# 專案結構指南 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19

---

## 設計原則

- **按功能組織**: 相關功能放一起（非按類型分散）
- **明確職責**: 每個目錄單一職責
- **一致命名**: 前端 `PascalCase.tsx`、後端 `snake_case.py`、測試 `test_` 開頭
- **配置外部化**: 配置與程式碼分離（`.env`）
- **前後端分離**: frontend/ 與 backend/ 獨立管理

---

## 頂層結構

```plaintext
n8n_rpa_post/
├── .claude/                  # Claude Code 配置
│   ├── agents/               # 專業 Agent 定義 (13 個)
│   ├── commands/             # Slash Commands (16 個)
│   ├── rules/                # 自動載入規則 (7 個)
│   ├── skills/               # 領域知識 Skill (8 個)
│   ├── taskmaster-data/      # WBS 任務追蹤
│   │   ├── wbs.md            # 工作分解結構
│   │   └── project.json      # 專案元資料
│   └── settings.json         # Claude Code 設定
├── frontend/                 # React 前端應用
├── backend/                  # FastAPI 後端 API
├── docs/                     # 專案文檔 (PRD、架構、ADR 等)
├── n8n/                      # n8n Workflow JSON exports
├── VibeCoding_Workflow_Templates/  # 工作流模板庫 (參考)
├── .gitignore
├── CLAUDE.md                 # 專案規則 (SSOT)
└── README.md
```

---

## 前端結構 (frontend/)

```plaintext
frontend/
├── public/                   # 靜態資源
├── src/
│   ├── components/           # 共用元件
│   │   ├── ui/               # shadcn/ui 基礎元件 (Atoms)
│   │   ├── AppSidebar.tsx    # 側邊欄導航
│   │   ├── ContentCard.tsx   # 貼文卡片
│   │   ├── Layout.tsx        # 頁面佈局
│   │   ├── MetricCard.tsx    # 指標卡片
│   │   ├── NavLink.tsx       # 導航連結
│   │   ├── PlatformTag.tsx   # 平台標籤
│   │   ├── ReplyItem.tsx     # 回覆項目
│   │   └── StatusBadge.tsx   # 狀態標記
│   ├── pages/                # 頁面路由
│   │   ├── Index.tsx         # 首頁 (→ ContentManagement)
│   │   ├── ContentManagement.tsx   # 貼文管理列表
│   │   ├── CreateContent.tsx       # 建立/編輯貼文
│   │   ├── MonitorDashboard.tsx    # 監控儀表板
│   │   ├── SettingsPage.tsx        # 設定頁面
│   │   └── NotFound.tsx            # 404 頁面
│   ├── hooks/                # 自定義 Hooks
│   │   ├── use-mobile.tsx    # 響應式偵測
│   │   ├── use-theme.ts      # 主題切換
│   │   └── use-toast.ts      # Toast 通知
│   ├── types/                # TypeScript 型別定義
│   │   └── content.ts        # 內容相關型別
│   ├── data/                 # Mock 資料 (開發用)
│   │   └── mock.ts
│   ├── lib/                  # 工具函式
│   │   └── utils.ts          # cn() 等通用工具
│   ├── App.tsx               # 路由配置
│   ├── main.tsx              # 入口點
│   └── index.css             # 全域樣式 (Tailwind)
├── package.json              # 依賴與腳本
├── vite.config.ts            # Vite 配置
├── tailwind.config.ts        # Tailwind 配置
├── tsconfig.json             # TypeScript 配置
├── vitest.config.ts          # 測試配置
├── playwright.config.ts      # E2E 測試配置
└── eslint.config.js          # ESLint 配置
```

### 待建立目錄 (隨開發演進)

```plaintext
src/
├── services/                 # API 客戶端層 (Phase 1.6)
│   ├── api-client.ts         # axios/fetch 封裝
│   └── content-api.ts        # 內容 API 呼叫
├── stores/                   # 狀態管理 (如需要)
└── features/                 # 功能模組 (如需按功能組織)
```

---

## 後端結構 (backend/)

```plaintext
backend/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI 入口、middleware 配置
│   ├── core/                  # 跨功能共享
│   │   ├── __init__.py
│   │   ├── config.py          # Pydantic Settings (環境變數)
│   │   └── database.py        # SQLAlchemy async engine & session
│   ├── models/                # SQLAlchemy ORM Models
│   │   ├── __init__.py
│   │   └── content.py         # ContentQueue, PublishLog, MonitorData
│   ├── schemas/               # Pydantic Schemas (API 驗證)
│   │   ├── __init__.py
│   │   └── content.py         # ContentCreate, ContentUpdate, ContentResponse
│   ├── api/                   # API Routes
│   │   ├── __init__.py
│   │   └── v1/                # (待建立) 版本化 API
│   │       ├── __init__.py
│   │       ├── contents.py    # 內容 CRUD endpoints
│   │       ├── webhooks.py    # n8n Webhook 回報
│   │       └── monitor.py     # 監控數據查詢
│   └── services/              # 業務邏輯層
│       ├── __init__.py
│       ├── content_service.py # 內容管理邏輯
│       ├── publish_service.py # 發佈觸發邏輯
│       └── monitor_service.py # 監控數據邏輯
├── alembic/                   # 資料庫遷移
│   ├── versions/              # 遷移腳本
│   └── env.py
├── tests/                     # 測試
│   ├── __init__.py
│   ├── conftest.py            # 共用 fixtures
│   ├── unit/                  # 單元測試
│   └── integration/           # 整合測試
├── requirements.txt           # Python 依賴
├── .env.example               # 環境變數範本
└── alembic.ini                # Alembic 配置
```

---

## n8n 目錄 (n8n/)

```plaintext
n8n/
├── workflows/
│   ├── publish_main.json      # 主發佈 workflow
│   ├── monitor_engagement.json # 監控互動 workflow
│   └── alert_notification.json # 告警通知 workflow
└── README.md                  # Workflow 設定說明
```

---

## 文檔結構 (docs/)

```plaintext
docs/
├── 01_workflow_manual.md                 # 開發流程
├── 02_project_brief_and_prd.md           # PRD (已完成)
├── 03_behavior_driven_development_guide.md # BDD (已完成)
├── 04_architecture_decision_record.md    # ADR
├── 05_architecture_and_design_document.md # 架構設計 (已完成)
├── 06_api_design_specification.md        # API 設計 (已完成)
├── 07_module_specification_and_tests.md  # 模組規格 (已完成)
├── 08_project_structure_guide.md         # 專案結構 (本文)
├── 09_file_dependencies.md              # 檔案依賴 (已完成)
├── 10_class_relationships.md             # 類別關係 (已完成)
├── 11_code_review_and_refactoring_guide.md # Code Review
├── 12_frontend_architecture_specification.md # 前端架構
├── 13_security_and_readiness_checklists.md   # 安全檢查
├── 14_deployment_and_operations_guide.md     # 部署運維
├── 15_documentation_and_maintenance_guide.md # 文檔維護
├── 16_wbs_development_plan.md                # WBS 計畫
├── 17_frontend_information_architecture.md   # 前端 IA
└── n8n_content_distributor_formal_spec_final.docx # 正式規格 (原始)
```

---

## 演進原則

- 本結構是起點，依專案發展調整
- 頂層結構的重大變更需 ADR 記錄
- 前端如功能增多，考慮從 pages/ 演進為 features/ 組織
- 後端如服務增多，考慮拆分為獨立微服務
