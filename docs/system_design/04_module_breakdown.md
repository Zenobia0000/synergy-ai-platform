# Synergy AI — 模組分解與後續規劃

> **版本:** v1.0 | **日期:** 2026-03-25
> **關聯文件:** `01_synergy_ai_prd.md`, `02_synergy_ai_sow.md`

---

## 1. 系統架構總覽

```
┌─────────────────────────────────────────────────────────────────┐
│                        Synergy AI Platform                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │  消費者 Web  │ │  經營者 Web  │ │  管理者 Web  │   ← 前端層    │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                │
│         │               │               │                        │
│  ───────┴───────────────┴───────────────┴────────────           │
│                                                                   │
│  ┌──────────────────────────────────────────────────┐            │
│  │              FastAPI Backend (REST API)            │ ← API 層  │
│  ├──────────────────────────────────────────────────┤            │
│  │  Auth │ Lead │ Quest │ Consult │ Plan │ Content  │            │
│  │  Svc  │ Svc  │ Svc   │ Svc     │ Svc  │ Svc     │            │
│  └──────────────────┬───────────────────────────────┘            │
│                     │                                             │
│  ┌──────────┐ ┌─────┴─────┐ ┌───────────┐                      │
│  │ PostgreSQL│ │ n8n Engine │ │ Claude API │  ← 基礎設施層       │
│  └──────────┘ └───────────┘ └───────────┘                      │
│                     │                                             │
│  ┌──────────────────┴───────────────────────────────┐            │
│  │  FB API │ X API │ LINE API │ IG API │ GCal API   │ ← 外部整合 │
│  └──────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 模組依賴關係

```
Phase 1: 基礎架構與核心 CRM
    │
    ├──→ Phase 2: 問卷評估系統（依賴 Lead 模型）
    │       │
    │       ├──→ Phase 3: 商談與成交支援（依賴問卷分析結果）
    │       │       │
    │       │       └──→ Phase 4: 客戶管理與陪跑（依賴成交流程）
    │       │
    │       └──→ Phase 5: AI 內容行銷引擎（依賴 Lead 資料）
    │
    └──→ Phase 6: 團隊管理與儀表板（依賴所有模組資料）
```

**關鍵路徑**：Phase 1 → 2 → 3 → 4（客戶生命週期主線）

---

## 3. 各模組技術細節

### 3.1 模組 1：AI 獲客行銷

#### 資料庫表

```sql
-- 社群貼文
CREATE TABLE social_posts (
    id UUID PRIMARY KEY,
    author_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    media_urls JSONB,
    platforms TEXT[] NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, scheduled, published, failed
    scheduled_at TIMESTAMPTZ,
    published_at TIMESTAMPTZ,
    ai_generated BOOLEAN DEFAULT FALSE,
    engagement_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lead 來源追蹤
CREATE TABLE lead_sources (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    source_type VARCHAR(50) NOT NULL,  -- social_post, seo, referral, event
    source_ref VARCHAR(255),            -- 具體來源 ID
    utm_campaign VARCHAR(255),
    first_touch_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 核心服務

| 服務 | 職責 |
| :--- | :--- |
| ContentGenerationService | 呼叫 Claude API 生成文案 |
| SocialPublishService | 透過 n8n Webhook 發布到各平台 |
| LeadCaptureService | 從社群私訊自動建立 Lead |
| EngagementTrackingService | 定時抓取各平台互動數據 |

---

### 3.2 模組 2：AI 問卷評估

#### 資料庫表

```sql
-- 問卷模板
CREATE TABLE questionnaire_templates (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    sections JSONB NOT NULL,        -- 分段定義
    scoring_rules JSONB,            -- 評分規則
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 問卷回應
CREATE TABLE questionnaire_responses (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    template_id UUID REFERENCES questionnaire_templates(id),
    responses JSONB NOT NULL,
    privacy_mode BOOLEAN DEFAULT FALSE,
    completion_rate FLOAT,
    analysis_result JSONB,
    priority_score FLOAT,
    recommended_products JSONB,
    routing_action VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 分流規則
CREATE TABLE routing_rules (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    priority INT NOT NULL,          -- 規則優先級（數字越小越先執行）
    conditions JSONB NOT NULL,      -- 條件組合
    action VARCHAR(50) NOT NULL,    -- auto_book, nurture, escalate, send_trial
    action_params JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### AI 分析流程

```
問卷提交
    │
    ↓
[1] 結構化解析 ──→ 提取關鍵指標
    │
    ↓
[2] AI 健康需求研判 ──→ Claude API 分析健康狀態
    │
    ↓
[3] 產品適配匹配 ──→ 根據需求推薦產品組合
    │
    ↓
[4] 潛力評分 ──→ 根據評分模型計算分數
    │
    ↓
[5] 分流規則匹配 ──→ 執行最高優先級命中規則
    │
    ↓
[6] 結果通知 ──→ 通知經營者跟進
```

---

### 3.3 模組 3：AI 商談轉化

#### 資料庫表

```sql
-- 商談記錄
CREATE TABLE consultations (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    operator_id UUID REFERENCES users(id),
    upline_id UUID REFERENCES users(id),
    scheduled_at TIMESTAMPTZ,
    mode VARCHAR(20),               -- face_to_face, video, phone, line
    status VARCHAR(20) DEFAULT 'scheduled',  -- scheduled, completed, cancelled, no_show
    pre_summary JSONB,              -- AI 生成的商談前摘要
    result VARCHAR(20),             -- converted, interested, objection, rejected
    objections TEXT[],              -- 遇到的異議
    notes TEXT,
    follow_up_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 異議知識庫
CREATE TABLE objection_entries (
    id UUID PRIMARY KEY,
    category VARCHAR(100) NOT NULL,  -- price, trust, timing, family, product
    objection_text TEXT NOT NULL,
    suggested_responses JSONB NOT NULL,
    success_rate FLOAT,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 試用品記錄
CREATE TABLE trial_records (
    id UUID PRIMARY KEY,
    lead_id UUID REFERENCES leads(id),
    products JSONB NOT NULL,
    sent_at DATE,
    tracking_number VARCHAR(100),
    received_at DATE,
    feedback TEXT,
    follow_up_dates DATE[],
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, received, followed_up
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.4 模組 4：AI 客戶管理與陪跑

#### 資料庫表

```sql
-- 健康管理計畫
CREATE TABLE health_plans (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    template_id UUID,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    goals JSONB,
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, completed, abandoned
    completion_rate FLOAT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 每日 checkin
CREATE TABLE plan_checkins (
    id UUID PRIMARY KEY,
    plan_id UUID REFERENCES health_plans(id),
    checkin_date DATE NOT NULL,
    items JSONB NOT NULL,           -- [{task, completed, note}]
    mood VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(plan_id, checkin_date)
);

-- 衛教內容
CREATE TABLE education_content (
    id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content_type VARCHAR(20) NOT NULL,  -- article, video, infographic
    body TEXT,
    media_url VARCHAR(500),
    tags TEXT[],
    target_plan_stage VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 提醒
CREATE TABLE reminders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    lead_id UUID REFERENCES leads(id),
    customer_id UUID REFERENCES customers(id),
    type VARCHAR(50) NOT NULL,      -- follow_up, repurchase, checkin, consultation
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, dismissed, snoozed, completed
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 3.5 模組 5：AI 內容行銷引擎

#### AI Prompt 設計概要

| 功能 | Prompt 策略 |
| :--- | :--- |
| 貼文文案生成 | 角色：社群行銷專家。輸入：成果素材 + 平台 + 風格。輸出：平台適配文案 |
| 見證故事包裝 | 角色：故事撰寫者。輸入：B/A 數據 + 客戶背景。輸出：情感故事 + 數據佐證 |
| 私訊回覆推薦 | 角色：溝通教練。輸入：對話歷史 + 客戶狀態。輸出：3 個回覆選項（溫和/專業/直接） |
| 對話引導腳本 | 角色：銷售顧問。輸入：當前對話節點。輸出：引導到下一步的話術 |

#### n8n 工作流設計

```
[貼文發布工作流]
Webhook 觸發 → 格式轉換 → 平行發布：
    ├─→ FB Page API
    ├─→ X API
    ├─→ LINE OA API
    └─→ IG API
→ 結果回寫 → 失敗告警
```

---

### 3.6 模組 6：AI 團隊管理

#### 資料庫表

```sql
-- 目標
CREATE TABLE goals (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    period VARCHAR(20) NOT NULL,    -- monthly, weekly
    period_start DATE NOT NULL,
    metrics JSONB NOT NULL,         -- {visits_target, conversions_target, ...}
    actuals JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 培訓記錄
CREATE TABLE training_records (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    program_name VARCHAR(255) NOT NULL,  -- e.g., "MEGA 新人培訓"
    tasks JSONB NOT NULL,               -- [{task_name, due_date, completed, completed_at}]
    progress FLOAT DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

#### 儀表板指標

```
個人儀表板
├── 本月目標進度
│   ├── 拜訪數 / 目標拜訪數
│   ├── 商談數 / 目標商談數
│   └── 成交數 / 目標成交數
├── 漏斗轉化率
│   ├── 名單 → 聯繫率
│   ├── 聯繫 → 問卷率
│   ├── 問卷 → 商談率
│   └── 商談 → 成交率
└── 待辦提醒
    ├── 今日回訪
    ├── 商談預約
    └── 未處理名單

團隊儀表板
├── 團隊月目標進度
├── 成員排行榜
├── 培訓完成度
├── 異常告警
│   ├── 連續 3 天無活動的成員
│   ├── 成交率低於平均 50% 的成員
│   └── 培訓進度落後的成員
└── 漏斗比較（本月 vs 上月）
```

---

## 4. 跨模組資料流

```
[模組1: 獲客]
    │ Lead 資料
    ↓
[模組2: 評估]
    │ 問卷結果 + 分級
    ↓
[模組3: 商談]
    │ 成交/未成交
    ├──→ 成交 ──→ [模組4: 客戶管理]
    │                   │ 計畫完成
    │                   ↓
    │              [模組5: 成果轉介紹]
    │                   │ 新 Lead
    │                   ↓
    │              [模組1: 獲客] (循環)
    │
    └──→ 未成交 ──→ [模組4: 追蹤提醒] ──→ [模組3: 再次商談]

    所有模組數據 ──→ [模組6: 團隊管理儀表板]
```

---

## 5. 後續規劃：待產出文件

### 5.1 Phase 1 啟動前必須

| 文件 | 內容 | 負責 | 預計完成 |
| :--- | :--- | :--- | :--- |
| 資料模型規格書 | 完整 ERD、所有表欄位定義、索引策略、migration 計畫 | 後端工程師 | Phase 1 W1 |
| UI 線框圖 - CRM | 名單列表、客戶詳情、狀態管理頁面設計 | UI/UX | Phase 1 W1 |
| API 規格書 v1 | OpenAPI spec for Phase 1 endpoints | 後端工程師 | Phase 1 W1 |

### 5.2 Phase 2 啟動前必須

| 文件 | 內容 | 負責 | 預計完成 |
| :--- | :--- | :--- | :--- |
| 問卷欄位定義 | 所有問卷欄位、選項、驗證規則、隱私等級 | 產品經理 + 領域專家 | Phase 1 W4 |
| 分流規則規格書 | 所有分流條件組合、優先級、衝突處理 | 產品經理 | Phase 1 W4 |
| AI Prompt 設計書 v1 | 問卷分析 prompt、評分模型 prompt | AI 工程師 | Phase 1 W4 |
| 名單評分模型 | 評分維度、權重、閾值、校準方法 | 產品經理 + 數據分析 | Phase 1 W4 |

### 5.3 Phase 3 啟動前必須

| 文件 | 內容 | 負責 | 預計完成 |
| :--- | :--- | :--- | :--- |
| 異議知識庫初版 | 常見異議分類、建議回覆、來源 | 領域專家 | Phase 2 W4 |
| 預約系統規格 | 預約流程、Google Calendar 整合、提醒機制 | 後端工程師 | Phase 2 W4 |

### 5.4 Phase 5 啟動前必須

| 文件 | 內容 | 負責 | 預計完成 |
| :--- | :--- | :--- | :--- |
| AI Prompt 設計書 v2 | 文案生成、見證包裝、話術推薦 prompt | AI 工程師 | Phase 4 W2 |
| 平台 API 整合規格 | 各平台 API 權限、限制、格式 | 後端工程師 | Phase 4 W4 |
| n8n 工作流設計書 | 所有自動化工作流的節點設計 | 自動化工程師 | Phase 4 W4 |

### 5.5 通用文件

| 文件 | 內容 | 負責 | 預計完成 |
| :--- | :--- | :--- | :--- |
| 安全與隱私規格書 | 加密方案、個資保護、同意書、資料保留政策 | 安全工程師 | Phase 1 W2 |
| 測試策略 | 單元/整合/E2E 測試策略、覆蓋率要求 | QA | Phase 1 W1 |
| 部署架構 | 部署環境、CI/CD、監控、告警 | DevOps | Phase 1 W2 |

---

## 6. MVP 範圍建議

如果需要縮小範圍先交付 MVP，建議聚焦：

### MVP（12 週）

| 模組 | 範圍 |
| :--- | :--- |
| 核心 CRM | Lead CRUD、狀態管理、手動標籤 |
| 問卷系統 | 固定問卷（不含設計器）、AI 分析、自動分級 |
| 商談支援 | 預約記錄（不含 Calendar 整合）、摘要生成、異議知識庫 |
| 客戶管理 | 客戶資料、提醒系統 |

### Post-MVP

| 模組 | 範圍 |
| :--- | :--- |
| AI 內容行銷 | 文案生成、私訊助手、n8n 整合 |
| 團隊管理 | 目標、績效看板、培訓追蹤 |
| 成果與轉介紹 | 報表生成、B/A 圖文、轉介紹機制 |
