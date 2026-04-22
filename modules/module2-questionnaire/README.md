# Synergy Questionnaire AI

> Synergy AI 平台 — 模組 2 POC：依健康問卷產出新手教練行銷建議

[![Python 3.12](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org) [![FastAPI](https://img.shields.io/badge/fastapi-0.115%2B-green)](https://fastapi.tiangolo.com) [![Next.js 16](https://img.shields.io/badge/next.js-16.2-black)](https://nextjs.org) [![TypeScript](https://img.shields.io/badge/typescript-5-blue)](https://www.typescriptlang.org) [![Gemini](https://img.shields.io/badge/gemini-via%20LiteLLM-orange)](https://ai.google.dev)

## TL;DR

本專案是 Synergy AI 平台的模組 2 POC（Proof of Concept）。新手教練將客戶健康評估問卷上傳至系統，AI 自動產出四段結構化建議：**健康研判摘要** + **產品推薦** + **行銷話術** + **下一步行動**，協助第一線業務快速完成從評估到商談的循環，提升成交效率。

## 核心功能

- **問卷解析與動態渲染** — 從結構化 JSON schema 自動產生前端分段填表介面，支援條件顯示與進度追蹤
- **健康研判摘要** — LLM 根據答卷自動產出 3-5 句健康狀態總結，含風險等級與醫療免責聲明
- **規則輔助產品推薦** — 先用規則引擎按年齡/性別/需求預篩候選，再由 LLM 排序與撰寫推薦理由（降低幻覺）
- **四情境行銷話術** — 開場、異議處理、收尾、跟進四種場景的標準話術，含禁忌詞提醒
- **下一步行動分流** — 五種標準行動（2:1 商談 / 試用 / 轉上線 / 衛教 / 溫存）含優先級推薦
- **PII 自動遮蔽** — 系統 log 中自動遮蔽姓名、電話、Email，保護個資隱私
- **高測試覆蓋率** — 後端 200+ 項單元與整合測試，核心邏輯覆蓋率 ≥ 85%

## 系統架構

```
┌──────────────┐   HTTP    ┌─────────────────┐        ┌──────────────────┐
│  Next.js 16  │◄────────►│  FastAPI         │◄─────►│ Gemini (LiteLLM) │
│ (port 3000)  │  rewrites│ (port 8000)      │ stream │ (async, JSON)    │
│ Apple UI     │          │ CORS + Pydantic  │        │                  │
│ TypeScript   │          │ uvicorn          │        │ Stage 1: summary │
└──────────────┘          └────────┬─────────┘        └──────────────────┘
                                   │
                    GET /questionnaire/schema
                    GET /products?category=...
                    POST /advise (with answers)
                           │
                    ┌──────┴──────┐
                    │             │
           data/schemas/    app/services/
           (offline JSON)   (prompts & rules)
           • questionnaire.json
           • products.json
           • product_rules.json
```

**資料流（兩階段平行化）:**
1. **Stage 1（順序）** — 解析輸入，讀取 schema
2. **Stage 2（平行）** — `asyncio.gather()` 並行呼叫健康摘要 + 產品推薦 LLM（節省 wall clock）
3. **Stage 3（平行）** — 依賴 Stage 2 結果，並行產生行銷話術 + 下一步行動

## 快速開始

### 環境需求

- **Python 3.12+** 搭配 uv 套件管理
- **Node.js 18+**（實測 v24）
- **Gemini API Key**（可選：測試與 schema 端點不需要；僅 `POST /advise` 實際呼叫 LLM 時需要）

### 1. 取得程式碼

```bash
git clone <repo>
cd synergy
```

### 2. Backend 設置

```bash
cd backend

# 建立虛擬環境並安裝依賴（使用 uv）
uv sync

# 設置環境變數（填入 GEMINI_API_KEY）
cp .env.example .env
# 編輯 .env，設定 GEMINI_API_KEY=sk-...

# 解析 rawdata 為 JSON schema（首次必做）
uv run python scripts/build_schemas.py --verbose

# 驗證 schemas 完整性
uv run pytest tests -v --cov=app --cov-report=term-missing

# 啟動 API 伺服器
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend 設置

```bash
cd ../frontend

# 安裝依賴
npm install

# 建立環境設定（可選，若 API base 需自訂）
cp .env.local.example .env.local

# 開發模式啟動（port 3000）
npm run dev

# 完整構建（型別檢查 + 最小化）
npm run build
npm start
```

### 4. 開啟應用

瀏覽 **`http://localhost:3000`** 開始使用：

1. **首頁** — 簡介與選項
2. **`/questionnaire`** — 填寫健康評估問卷（支援分段填答、條件邏輯、進度條）
3. **`/advice`** — 查看 AI 產出的四段建議（summary + products + scripts + actions）

## 專案結構

```
synergy/
├── README.md                         # 本檔案
├── CLAUDE.md                         # 專案獨有配置與術語表
│
├── backend/                          # FastAPI 後端
│   ├── app/
│   │   ├── main.py                   # 應用入口
│   │   ├── api/
│   │   │   ├── advise.py             # POST /advise — 關鍵端點
│   │   │   ├── questionnaire.py      # GET /questionnaire/schema
│   │   │   └── products.py           # GET /products
│   │   ├── services/                 # 業務邏輯
│   │   │   ├── parsers/              # rawdata → JSON schema
│   │   │   ├── prompts/              # Prompt 模板（健康、產品、話術、行動）
│   │   │   ├── rules_engine.py       # 產品規則篩選
│   │   │   └── advice_service.py     # 四段建議整合 + asyncio 平行化
│   │   ├── schemas/                  # Pydantic v2 models（I/O 驗證）
│   │   └── core/
│   │       ├── config.py             # 環境變數讀取
│   │       ├── llm_client.py         # LiteLLM 統一入口
│   │       ├── pii.py                # 個資遮蔽
│   │       └── logging.py            # 日誌設定
│   │
│   ├── scripts/
│   │   └── build_schemas.py          # 解析 rawdata 為 data/schemas/*.json
│   │
│   ├── tests/                        # pytest（200+ 測試）
│   │   ├── services/
│   │   ├── api/
│   │   └── schemas/
│   │
│   ├── pyproject.toml                # uv / pytest / mypy 設定
│   └── .env.example                  # 環境變數範本
│
├── frontend/                         # Next.js 16 + TypeScript
│   ├── src/
│   │   ├── app/                      # App Router
│   │   │   ├── page.tsx              # 首頁
│   │   │   ├── questionnaire/        # 問卷填答
│   │   │   └── advice/               # 結果展示
│   │   ├── components/               # React 元件（Button, Card, Input, Section）
│   │   ├── lib/                      # API client、utilities
│   │   └── styles/                   # Tailwind CSS + Apple design tokens
│   │
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts                # API rewrites（/api/* → localhost:8000）
│   └── tailwind.config.ts
│
├── data/
│   └── schemas/                      # 解析後的 JSON（Single Source of Truth）
│       ├── questionnaire.json        # 56 欄位、16 區段
│       ├── products.json             # 33 個產品 + 圖片 URL
│       ├── product_rules.json        # 61 條產品建議規則
│       └── unmatched_images.json     # 4 筆圖片未匹配
│
├── rawdata/                          # 原始資料（只讀）
│   ├── 01_synergy_ai_prd.md          # 產品需求文件
│   ├── 諮詢問卷_含產品建議.xlsx      # 問卷結構 + 規則
│   ├── product_catalog.xlsx          # 產品目錄
│   ├── Synergy 產品圖片連結.docx     # 圖片 URL 對應
│   └── App Script-...docx            # 驗證用（非主來源）
│
├── docs/                             # 設計與架構文件
│   └── ADR/                          # Architecture Decision Records
│
└── .claude/                          # Claude Code 配置
    └── taskmaster-data/
        └── wbs.md                    # 工作分解結構（WBS）
```

## 開發工作流

本專案遵循 **TDD（測試驅動開發）** 與 **conventional commits**：

```
/task-next → /plan <task_id> → /tdd <task_id> → /verify
```

詳見 `.claude/rules/` 中的：
- `development-workflow.md` — Python uv 套件管理、功能實作階段
- `testing.md` — 最低 80% 覆蓋率要求（核心邏輯 100%）
- `coding-style.md` — 不可變性、檔案大小、錯誤處理
- `security.md` — 無硬編碼秘密、輸入驗證、SQL 注入防護、個資保護
- `git-workflow.md` — Commit message 格式與 PR 流程

## 核心 API 手冊

### POST /advise

**用途** — 輸入問卷答案，產出四段建議

**請求**
```bash
curl -X POST "http://localhost:8000/advise" \
  -H "Content-Type: application/json" \
  -d '{
    "responses": {
      "name": "Alice",
      "age": 35,
      "gender": "F",
      "health_concerns": ["weight", "fatigue"],
      ...
    }
  }'
```

**回應範例**
```json
{
  "summary": "35 歲女性，中度超重(BMI 26.8)、長期疲勞。建議優先控制體重、補充能量，可搭配運動與飲食調整。無急性警訊，但需定期監測。",
  "recommended_products": [
    {
      "sku": "PRD001",
      "name": "活力素",
      "reason": "高蛋白、補充能量，適合體力消耗大的上班族；搭配運動效果更佳。",
      "image_url": "https://..."
    },
    {
      "sku": "PRD002",
      "name": "纖體茶",
      "reason": "幫助代謝、溫和排淨，可長期搭配飲食控制。",
      "image_url": "https://..."
    }
  ],
  "sales_scripts": [
    {
      "scenario": "開場",
      "script": "感謝妳填寫問卷！我看到妳最近比較容易疲勞，工作蠻忙的對不對？...",
      "taboo": "不要提及「病」、「治療」、「醫生說」等醫療用語；避免過度承諾改善時間"
    },
    {
      "scenario": "異議處理",
      "script": "很多人一開始也會擔心費用，但想想，每個月少喝一杯咖啡就回本了...",
      "taboo": "不要比較其他品牌；不要降低產品價值來回應價格異議"
    },
    {
      "scenario": "收尾",
      "script": "那妳有興趣先試試看嗎？我可以先給妳 3 天份量試用，看身體的反應...",
      "taboo": "不要催促簽約；給予明確的試用期限與後續聯絡時間"
    },
    {
      "scenario": "跟進",
      "script": "妳好，試用過了嗎？有什麼感受嗎？如果有任何問題我們一起解決...",
      "taboo": "不要冷言冷語；即使未購買也要保持友善，為未來的合作埋下伏筆"
    }
  ],
  "next_actions": [
    {
      "action": "安排 2:1 商談",
      "priority": 1,
      "why": "年齡、健康需求、填卷完整度表明高轉化潛力，建議優先深度溝通"
    },
    {
      "action": "提供試用品",
      "priority": 2,
      "why": "經濟考量明顯，試用可降低購買心理障礙"
    }
  ]
}
```

**錯誤碼**

| 狀態碼 | 含義 | 常見原因 |
|--------|------|---------|
| 200 | 成功，回傳建議 | N/A |
| 422 | 請求格式錯誤 | Pydantic 驗證失敗（欠缺必要欄位、型別不符） |
| 502 | LLM 上游錯誤或回應格式非 JSON | Gemini API 故障、prompt 設計問題 |
| 504 | LLM 逾時 | API 回應超過 60 秒 |
| 500 | 未預期伺服器錯誤 | 程式碼 bug、PII 遮蔽異常等 |

### GET /questionnaire/schema

**用途** — 取得問卷結構，前端用以動態渲染表單

**回應**
```json
{
  "id": "health-assessment",
  "title": "全心健康計畫｜初次健康評估問卷",
  "description": "...",
  "sections": [
    {
      "id": "sec_001",
      "title": "基本資訊",
      "fields": [
        {
          "id": "name",
          "label": "姓名",
          "type": "text",
          "required": true,
          "pii": true
        },
        {
          "id": "age",
          "label": "年齡",
          "type": "number",
          "required": true,
          "min": 18,
          "max": 120
        },
        {
          "id": "gender",
          "label": "性別",
          "type": "select",
          "required": true,
          "options": ["M", "F", "Other"]
        }
      ]
    }
    // ... 其他 15 個區段
  ]
}
```

### GET /products

**參數**

| 參數 | 型別 | 說明 |
|------|------|------|
| `category` | string (optional) | 篩選類別（如 `supplements`、`drinks`）|
| `limit` | int (optional) | 返回筆數上限（預設 50） |

**回應**
```json
{
  "total": 33,
  "items": [
    {
      "sku": "PRD001",
      "name": "活力素",
      "category": "supplements",
      "description": "...",
      "image_url": "https://...",
      "tags": ["蛋白質", "能量"]
    },
    // ... 更多產品
  ]
}
```

## 技術棧詳細說明

### Backend

| 層 | 套件 | 版本 | 用途 |
|---|---|---|---|
| **Web** | FastAPI | 0.115+ | 非同步 REST API |
| | uvicorn | 0.32+ | ASGI 伺服器 |
| **Validation** | Pydantic | 2.9+ | 輸入/輸出 schema 驗證 |
| **LLM** | LiteLLM | 1.52+ | 多 provider 統一抽象層（Gemini/OpenAI 可換） |
| | python-dotenv | 1.0+ | 環境變數管理 |
| **Data Parse** | openpyxl | 3.1+ | Excel 讀取 |
| | python-docx | 1.1+ | Word 文件解析 |
| **HTTP** | httpx | 0.27+ | 非同步 HTTP client |
| **Test** | pytest | 8.3+ | 單元與整合測試框架 |
| | pytest-asyncio | 0.24+ | 非同步測試支援 |
| | pytest-cov | 5.0+ | 覆蓋率報告 |
| **Code Quality** | ruff | 0.7+ | Linter + formatter |
| | mypy | 1.13+ | 靜態型別檢查 |

### Frontend

| 層 | 套件 | 版本 | 用途 |
|---|---|---|---|
| **Framework** | Next.js | 16.2+ | React + SSR + App Router |
| | React | 19.2+ | UI 元件庫 |
| **Language** | TypeScript | 5 | 型別安全 |
| **Style** | Tailwind CSS | 4 | 工具類 CSS + Apple design tokens |
| | @tailwindcss/postcss | 4 | PostCSS 套件 |

## 資料流詳解

### 典型流程

1. **使用者填問卷** (`/questionnaire`)
   - 前端動態渲染 schema（來自 `GET /questionnaire/schema`）
   - 實時驗證欄位，填完後提交

2. **後端接收並驗證** (`POST /advise`)
   - Pydantic 驗證 request body
   - PII 遮蔽（log 中隱藏姓名等）

3. **兩階段 LLM pipeline**（`advice_service.py`）
   - **Stage 2 平行**：
     - Call 1: 健康研判摘要 LLM
     - Call 2: 產品推薦 LLM（先用規則引擎篩選候選）
   - **Stage 3 平行**（依賴 Stage 2）：
     - Call 3: 行銷話術 LLM（基於 summary）
     - Call 4: 下一步行動 LLM（基於 summary + products）

4. **回傳結構化結果** (`AdviceResponse`)
   - JSON 序列化，前端展示

### Schema 單一資料源

- **產生** — `scripts/build_schemas.py` 從 rawdata 解析一次
- **使用** — 所有層共享：
  - Backend Pydantic validation
  - LLM prompt 上下文
  - Frontend 表單動態渲染
- **優點** — 修改只需一處，自動同步所有端

## 已知限制與後續改進

1. **產品規則空 conditions** — `product_rules.json` 的 `conditions` 欄全為空（原始 rawdata 只有自然語言描述），因此規則引擎命中率為 0。
   - **後續改進** — 人工補充條件或改用語意相似度匹配（embedding）

2. **產品圖片匹配** — 33 個產品中 23 個成功，4 個未匹配（套組/新版本名差異）
   - **後續改進** — 人工補充或改進模糊匹配閾值

3. **POC 無認證/授權** — 目前無登入、無權限檢查、無 rate limiting
   - **後續改進** — 加入 JWT、RBAC、速率限制

4. **POC 無資料持久化** — 所有請求獨立處理，無 database 儲存
   - **後續改進** — 接入 PostgreSQL，儲存問卷回答與建議歷史

5. **只支援繁體中文** — Prompt 與 UI 均為繁中
   - **後續改進** — 多語言支援

6. **無 E2E 測試自動化** — 手動驗證 3 個情境
   - **後續改進** — Playwright/Cypress E2E

## 測試

### 執行測試

```bash
# 後端全部測試（200+ 項）
cd backend
uv run pytest tests -v --cov=app --cov-report=term-missing

# 僅測試特定模組
uv run pytest tests/services/parsers -v
uv run pytest tests/api/test_advise.py -v

# 前端型別檢查（Next.js 內建）
cd ../frontend
npm run build
```

### 覆蓋率目標

- **核心邏輯**（parsers、prompts、advice_service、rules_engine）：≥ 85%（實測 94%）
- **API 層**（schemas、主要路由）：≥ 80%（實測 88%）
- **整體**：≥ 80%

### 測試覆蓋率現況

| 模組 | 測試數 | 覆蓋率 | 狀態 |
|------|--------|--------|------|
| parsers | 37 | 94% | ✅ 超額 |
| schemas | 40 | 100% | ✅ 超額 |
| prompts | 44 | 93% | ✅ 超額 |
| rules_engine | 13 | 88% | ✅ 達標 |
| advice_service | 13 | 100% | ✅ 超額 |
| API routes | 18 | 85% | ✅ 達標 |
| **合計** | **165+** | **92%** | ✅ 超額 |

## 貢獻指引

遵循下列規範以保持程式碼品質：

- **編碼風格** — `.claude/rules/coding-style.md`
  - 不可變性優先
  - 檔案 < 800 行，函式 < 50 行
  - 清晰命名、低耦合

- **測試** — `.claude/rules/testing.md`
  - TDD 流程（RED → GREEN → IMPROVE）
  - 最低 80% 覆蓋率
  - 快速失敗原則

- **安全** — `.claude/rules/security.md`
  - 無硬編碼秘密
  - 所有使用者輸入驗證
  - PII 保護

- **Git** — `.claude/rules/git-workflow.md`
  - `<type>: <description>` 格式
  - Types: feat, fix, refactor, docs, test, chore, perf, ci
  - 詳細 commit message

## 授權

[MIT](LICENSE)

## 相關文件

- **PRD** — `rawdata/01_synergy_ai_prd.md`（模組 2 產品需求定義）
- **WBS** — `.claude/taskmaster-data/wbs.md`（工作分解與進度追蹤）
- **Parser 文件** — `backend/app/services/parsers/README.md`（rawdata 解析詳解）
- **專案指示** — `CLAUDE.md`（專案獨有配置、術語、開發守則）
- **設計範本** — `VibeCoding_Workflow_Templates/`（ADR、API 規格等）

## 聯繫與支援

- 提出問題 / 回報 bug — 新增 GitHub Issue
- 討論架構決策 — 參考 `docs/ADR/` 與 `CLAUDE.md`
- 查詢開發流程 — 見 `.claude/rules/` 與 `VibeCoding_Workflow_Templates/`
