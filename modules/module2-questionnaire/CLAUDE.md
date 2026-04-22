# CLAUDE.md - Synergy Questionnaire AI

> **專案:** synergy-questionnaire-ai
> **描述:** Synergy AI 平台 — 模組 2「AI 問卷評估」POC：依健康問卷填答產出新手教練可用的行銷建議（健康研判摘要 + 產品組合 + 話術 + 下一步行動）
> **語言:** Python 3.12 (backend) / TypeScript (frontend)
> **建立:** 2026-04-21
> **PRD:** `rawdata/01_synergy_ai_prd.md` §7 模組 2

## 開發流程

遵循 `.claude/guides/WORKFLOW.md` 的標準流程：

```
/task-next → /plan → /tdd → /verify
```

## 技術棧

| 層級 | 技術 |
| :--- | :--- |
| Backend | FastAPI + Pydantic v2 + uvicorn |
| 套件管理 | **uv**（禁用 pip / poetry） |
| LLM 抽象層 | **LiteLLM**（Gemini 優先，可擴充其他 provider） |
| LLM 模型 | Google Gemini（`gemini-2.5-flash` 預設；複雜推理可升到 `gemini-2.5-pro`） |
| Frontend | Vite 6 + React 19 + TypeScript + Tailwind CSS v4 + React Router 7 |
| UI 風格 | Apple（規範在 `.claude/ui/apple/DESIGN.md`） |
| 測試 | pytest + pytest-asyncio（backend）、Playwright（E2E，選配） |
| 執行環境 | 純本機：`localhost:3000`（前端）+ `localhost:8000`（後端） |

## 領域術語

| 術語 | 定義 |
| :--- | :--- |
| FORM | Family / Occupation / Recreation / Money — 客戶背景資料框架 |
| 重生計畫 | 健康管理執行計畫（產品使用 + 生活調整） |
| 2:1 商談 | 經營者 + 上線 對 客戶 的諮詢模式 |
| Lead / 名單分級 | 問卷結果分級（高/中/低潛力） |
| 新手教練 | 第一線經營者（內部用戶），POC 主要服務對象 |

## 資料來源

所有問卷、產品參考資料放在 `rawdata/`：

- `01_synergy_ai_prd.md` — PRD（模組 2 定義）
- `App Script-全心健康計畫｜初次健康評估問卷.docx` — 正式健康問卷原稿
- `諮詢問卷.xlsx` / `諮詢問卷_含產品建議.xlsx` — 問卷結構 + 既有產品對應
- `product_catalog.xlsx` — 產品目錄
- `Synergy 產品圖片連結.docx` — 產品圖片 URL

**解析後的結構化資料** 放在 `data/schemas/`（questionnaire.json、product_catalog.json 等）。

## 專案結構

```
synergy/
├── backend/                  # FastAPI 服務
│   ├── app/
│   │   ├── api/              # 路由 (POST /advise, GET /questionnaire/schema)
│   │   ├── services/         # 業務邏輯（LLM pipeline、產品規則引擎）
│   │   ├── schemas/          # Pydantic models
│   │   └── core/             # config、LiteLLM client、logging
│   ├── tests/                # pytest
│   ├── pyproject.toml
│   └── .venv/
├── frontend/                 # Vite SPA（React + React Router）
│   ├── src/
│   │   ├── main.tsx          # Vite entry + BrowserRouter
│   │   ├── App.tsx           # 路由定義
│   │   ├── routes/           # Home、Questionnaire、Advice
│   │   ├── components/       # ui、questionnaire、advice
│   │   ├── lib/              # api、types、conditions、markdown...
│   │   └── index.css         # Tailwind v4 + Apple tokens
│   ├── vite.config.ts        # /api → http://localhost:8000 proxy
│   └── package.json
├── data/
│   └── schemas/              # 解析 rawdata 後的 JSON schema
├── docs/                     # ADR、設計筆記
├── rawdata/                  # 原始文件（不編輯）
└── .claude/
    └── taskmaster-data/      # WBS、plans、project.json
```

## 核心輸出契約（LLM 產出結構）

POC 的 `/advise` API 應回傳四段結構化內容：

```json
{
  "summary": "問卷健康研判摘要（3-5 句，含風險重點）",
  "recommended_products": [
    { "sku": "...", "name": "...", "reason": "...", "image_url": "..." }
  ],
  "sales_scripts": [
    { "scenario": "開場 / 異議 / 收尾", "script": "...", "taboo": "..." }
  ],
  "next_actions": [
    { "action": "安排 2:1 商談 / 提供試用 / 轉上線", "why": "..." }
  ]
}
```

## 開發守則（僅本專案補充，其餘見 `.claude/rules/`）

- **LLM 成本**：POC 預設用 `gemini-2.5-flash`；所有 LLM 呼叫需記錄 prompt / completion tokens 到 log
- **Prompt 集中管理**：Prompt 模板放 `backend/app/services/prompts/*.py`，不散落在呼叫端
- **Schema-first**：問卷與輸出格式用 Pydantic 定義，LLM 輸出強制以 `response_format` / JSON mode 解析
- **個資遮蔽**：log 記錄時遮蔽姓名、電話、Email（`core/pii.py`）
- **LiteLLM 統一入口**：禁止直接呼叫 google-generativeai / openai，一律走 `core/llm_client.py`

## 擴充路線圖（POC 之後）

1. 接 Module 1（貼文生成）共用 LLM pipeline
2. 加入 audit log + PostgreSQL 儲存問卷 + 建議結果
3. 加入管理者後台（檢視新手教練使用情況）
