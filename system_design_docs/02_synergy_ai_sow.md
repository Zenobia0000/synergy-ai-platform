# Synergy AI — 軟體需求分析暨工作說明書 (SOW)

> **版本:** v1.0 | **日期:** 2026-03-25 | **狀態:** 草稿
> **關聯文件:** `01_synergy_ai_prd.md`
> **分析等級:** Tier 1 軟體需求分析

---

## 1. 專案概述

### 1.1 專案範圍

基於 PRD 定義的六大功能模組，本 SOW 定義軟體交付範圍、階段劃分、技術規格、驗收標準與後續規劃。

### 1.2 交付目標

交付一套以 Web 為主要介面的 AI 營運平台，涵蓋：
- 消費者端：問卷填寫、健康評估報告、衛教內容
- 經營者端：名單管理、商談輔助、客戶追蹤
- 管理者端：績效儀表板、培訓追蹤、團隊管理

### 1.3 技術基礎

| 層級 | 技術 | 說明 |
| :--- | :--- | :--- |
| 前端 | Vite + React 18 + TypeScript | shadcn/ui + Tailwind CSS |
| 後端 | FastAPI (Python) | REST API、排程管理、Webhook |
| 資料庫 | PostgreSQL | 結構化資料儲存 |
| 自動化引擎 | n8n (本地自架) | 工作流自動化、多平台分發 |
| AI 服務 | Claude API / OpenAI API | 文案生成、問卷分析、話術推薦 |
| 訊息平台 | LINE OA / Facebook / X / IG | 社群分發與互動 |

---

## 2. 開發階段劃分

### Phase 1：基礎架構與核心 CRM（Week 1-4）

**目標**：建立客戶資料管理基礎，能手動管理名單與客戶狀態。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 1.1 | 客戶資料模型 | 設計並實作客戶、名單、問卷、狀態等核心資料模型 | Alembic migration 通過，CRUD API 可用 |
| 1.2 | 名單管理 API | Lead CRUD、標籤、分級、搜尋、篩選 | API 測試覆蓋率 ≥ 80% |
| 1.3 | 客戶狀態機 | 定義狀態流轉（新名單→已聯繫→已填問卷→已商談→成交/追蹤中/流失） | 狀態流轉 API 正確，非法流轉被阻擋 |
| 1.4 | 名單管理前端 | 名單列表、搜尋、篩選、狀態標籤 | 頁面可正確渲染、TypeScript 無型別錯誤 |
| 1.5 | 客戶詳情頁 | 客戶基本資料、狀態歷程、備註 | 可新增/編輯客戶資料 |

#### 資料模型初版

```
Lead (名單)
├── id: UUID
├── name: string
├── contact_method: enum (LINE, phone, email, messenger)
├── contact_value: string
├── source: enum (social_media, referral, event, seo)
├── status: enum (new, contacted, questionnaire_done, consultation_booked, converted, tracking, lost)
├── priority: enum (high, medium, low)
├── tags: string[]
├── assigned_to: FK → User
├── created_at: datetime
└── updated_at: datetime

Customer (客戶)
├── id: UUID
├── lead_id: FK → Lead
├── form_data: JSONB (family, occupation, recreation, money)
├── health_profile: JSONB
├── plan_status: enum (not_started, in_progress, completed)
├── purchase_history: relation
├── created_at: datetime
└── updated_at: datetime

QuestionnaireResponse (問卷回應)
├── id: UUID
├── lead_id: FK → Lead
├── questionnaire_version: string
├── responses: JSONB
├── analysis_result: JSONB (AI 分析結果)
├── recommended_products: JSONB
├── priority_score: float
├── created_at: datetime
└── completed_at: datetime

StatusHistory (狀態歷程)
├── id: UUID
├── lead_id: FK → Lead
├── from_status: enum
├── to_status: enum
├── changed_by: FK → User
├── note: text
└── changed_at: datetime
```

---

### Phase 2：問卷評估系統（Week 5-8）

**目標**：建立健康問卷流程，實作 AI 問卷分析與名單自動分級。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 2.1 | 問卷設計器 | 可配置問卷欄位、選項、分段填答 | 管理者可建立/編輯問卷模板 |
| 2.2 | 問卷填答前端 | 消費者友善的問卷填答介面，支援隱私模式 | 支援分段填答、中斷續填 |
| 2.3 | AI 問卷分析 | 根據回答生成健康需求研判與產品建議 | 分析結果包含需求等級、建議產品、風險提示 |
| 2.4 | 名單自動分級 | 根據問卷分析結果自動設定 Lead priority | 分級規則可配置，分級結果可人工覆寫 |
| 2.5 | 分流規則引擎 | 可配置的分流條件與動作 | 規則命中時自動執行對應動作 |

#### 分流規則初版設計

```yaml
rules:
  - name: "直接進商談"
    conditions:
      - priority_score >= 80
      - has_budget_history: true
      - distance_km <= 60
    action: auto_book_consultation

  - name: "先給內容培養"
    conditions:
      - priority_score >= 50
      - priority_score < 80
    action: enter_nurture_sequence

  - name: "轉上線協助"
    conditions:
      - complexity_score >= 70
      - or:
        - has_medical_condition: true
        - budget_concern: true
    action: escalate_to_upline

  - name: "先給試用品"
    conditions:
      - taste_concern: true
      - priority_score >= 60
    action: send_trial
```

---

### Phase 3：商談與成交支援（Week 9-12）

**目標**：建立商談預約、異議處理知識庫，提升成交效率。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 3.1 | 預約系統 | 2:1 商談時間預約、Google Calendar 整合、自動提醒 | 可成功預約，提醒準時送達 |
| 3.2 | 商談摘要生成 | 商談前自動彙整客戶問卷+FORM 資料為一頁摘要 | 摘要包含關鍵資訊、風險提示 |
| 3.3 | 異議處理知識庫 | CRUD 管理常見異議與建議回覆，支援 AI 搜尋 | 可搜尋關鍵字取得建議回覆 |
| 3.4 | 試用品管理 | 試用品寄送記錄、回訪排程 | 可記錄試用品狀態、到期自動提醒回訪 |
| 3.5 | 成交流程 | 成交記錄、產品訂購關聯、客戶轉移 | 成交後自動將 Lead 轉為 Customer |

---

### Phase 4：客戶管理與陪跑（Week 13-16）

**目標**：建立客戶健康管理計畫追蹤與衛教推播系統。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 4.1 | 重生計畫模板 | 可配置的健康管理計畫模板 | 管理者可建立/編輯計畫模板 |
| 4.2 | 計畫執行追蹤 | 每日 checkin、進度記錄、里程碑 | 客戶可記錄每日執行，經營者可查看進度 |
| 4.3 | 衛教內容庫 | 衛教文章/影片分類管理 | 內容可按標籤/階段篩選 |
| 4.4 | 自動推播引擎 | 依客戶計畫階段自動推播衛教內容 | 推播準時且內容與階段匹配 |
| 4.5 | 回訪提醒系統 | 未成交追蹤提醒、舊客關懷提醒、續購提醒 | 提醒準時且包含客戶摘要 |

---

### Phase 5：AI 內容行銷引擎（Week 17-20）

**目標**：建立社群內容生成與私訊回覆輔助系統。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 5.1 | 文案生成引擎 | 根據素材/成果生成社群貼文文案 | 生成文案可直接發布，品質達可用水準 |
| 5.2 | 見證故事包裝 | 將 B/A 成果轉化為見證故事 | 自動排版 B/A 對照、生成故事文案 |
| 5.3 | 私訊回覆助手 | 根據對話情境推薦回覆話術 | 推薦話術與情境相關，經營者可一鍵使用 |
| 5.4 | 對話引導腳本 | 從私訊引導至問卷的對話流程 | 引導腳本邏輯正確，可配置分支 |
| 5.5 | n8n 整合 | 貼文自動發布至 FB/X/LINE/IG | 發布成功率 ≥ 95% |

---

### Phase 6：團隊管理與儀表板（Week 21-24）

**目標**：建立團隊績效管理與培訓追蹤系統。

#### 交付項目

| 編號 | 交付項目 | 描述 | 驗收標準 |
| :--- | :--- | :--- | :--- |
| 6.1 | 目標設定系統 | 個人/團隊月目標 CRUD | 可設定、修改、查看目標 |
| 6.2 | 績效看板 | 拜訪率/成交率/活躍度即時看板 | 數據準確、即時更新 |
| 6.3 | 團隊轉化漏斗 | 從名單到成交的漏斗視覺化 | 漏斗各階段數據準確 |
| 6.4 | 培訓追蹤系統 | MEGA 培訓進度、任務分派、完成追蹤 | 可分派任務、追蹤完成度 |
| 6.5 | 異常提醒 | 進度落後、活躍度下降自動告警 | 告警準時且規則可配置 |

---

## 3. 資料欄位規格

### 3.1 健康問卷欄位（初版）

| 欄位群組 | 欄位 | 型別 | 必填 | 隱私等級 |
| :--- | :--- | :--- | :--- | :--- |
| 基本資料 | 性別 | enum | Y | 低 |
| 基本資料 | 年齡區間 | enum (20-29/30-39/40-49/50-59/60+) | Y | 低 |
| 基本資料 | 居住地區 | string | Y | 低 |
| 健康現況 | 目前最困擾的健康問題（複選） | enum[] | Y | 中 |
| 健康現況 | 是否有慢性病或長期用藥 | boolean + text | N | 高 |
| 健康現況 | BMI 區間 | enum | N | 中 |
| 健康經驗 | 過去嘗試過的健康管理方式（複選） | enum[] | Y | 低 |
| 健康經驗 | 過去投入的最高單次費用 | enum (5K以下/5K-1W/1W-3W/3W+) | N | 中 |
| 健康經驗 | 減重/健康管理經驗年數 | enum | N | 低 |
| 生活習慣 | 運動頻率 | enum | Y | 低 |
| 生活習慣 | 飲食型態 | enum | Y | 低 |
| 意向 | 最想達成的健康目標 | text | Y | 低 |
| 意向 | 願意投入的月預算區間 | enum | N | 中 |
| 意向 | 偏好的溝通方式 | enum (LINE/電話/見面/視訊) | Y | 低 |

> **隱私模式**：高隱私等級欄位預設隱藏，消費者可選擇不填。系統以已填欄位進行分析。

### 3.2 FORM 資料結構

| 類別 | 欄位 | 型別 | 說明 |
| :--- | :--- | :--- | :--- |
| **F**amily | 婚姻狀態 | enum | 已婚/未婚/其他 |
| Family | 子女數 | int | — |
| Family | 家庭健康狀況備註 | text | 自由文字 |
| **O**ccupation | 職業類別 | enum | 上班族/自營/自由業/家管/退休/其他 |
| Occupation | 工時模式 | enum | 正常/輪班/彈性 |
| **R**ecreation | 休閒興趣 | text | 自由文字 |
| Recreation | 社交活躍度 | enum | 高/中/低 |
| **M**oney | 收入區間 | enum | 3W以下/3-5W/5-8W/8W+/不透露 |
| Money | 決策自主度 | enum | 完全自主/需與家人商量/無法自主 |

### 3.3 客戶狀態機定義

```
[new] ──私訊接觸──→ [contacted]
  │                      │
  │                  邀請填問卷
  │                      ↓
  │               [questionnaire_done]
  │                      │
  │                  AI 分析分流
  │                      ↓
  │              [consultation_booked]
  │                      │
  │              ┌───商談結果───┐
  │              ↓             ↓
  │         [converted]   [tracking]
  │              │             │
  │         啟動計畫     定期追蹤
  │              │             │
  │              │        ┌────┴────┐
  │              │        ↓         ↓
  │              │   [converted] [lost]
  │              │
  │         [plan_active]
  │              │
  │         [plan_completed]
  │              │
  │         [advocacy] ──轉介紹──→ 新 [new]
  │
  └──超過90天無互動──→ [lost]
```

### 3.4 名單分級評分模型（初版）

| 評分維度 | 權重 | 高分條件 |
| :--- | :--- | :--- |
| 健康需求強度 | 25% | 多項健康困擾、有明確目標 |
| 預算意願 | 20% | 曾投入高費用、願意投入合理預算 |
| 決策自主度 | 15% | 完全自主決策 |
| 地理距離 | 15% | 60km 以內 |
| 互動活躍度 | 15% | 問卷完整度高、回覆速度快 |
| 來源品質 | 10% | 轉介紹 > 活動 > 社群 > SEO |

- **高潛力（80-100 分）**：直接預約商談
- **中潛力（50-79 分）**：進入培養序列
- **低潛力（0-49 分）**：列入長期追蹤池

---

## 4. API 設計概要

### 4.1 核心端點

```
# 名單管理
POST   /api/v1/leads                     # 建立名單
GET    /api/v1/leads                     # 查詢名單（支援篩選、分頁）
GET    /api/v1/leads/{id}                # 名單詳情
PATCH  /api/v1/leads/{id}                # 更新名單
PATCH  /api/v1/leads/{id}/status         # 狀態流轉
GET    /api/v1/leads/{id}/history        # 狀態歷程

# 問卷系統
GET    /api/v1/questionnaires            # 問卷模板列表
POST   /api/v1/questionnaires            # 建立問卷模板
POST   /api/v1/questionnaire-responses   # 提交問卷回應
GET    /api/v1/questionnaire-responses/{id}/analysis  # 取得 AI 分析結果

# 客戶管理
POST   /api/v1/customers                 # 建立客戶（從成交 Lead 轉入）
GET    /api/v1/customers/{id}            # 客戶詳情
PATCH  /api/v1/customers/{id}            # 更新客戶資料

# 商談管理
POST   /api/v1/consultations             # 預約商談
GET    /api/v1/consultations             # 商談列表
PATCH  /api/v1/consultations/{id}        # 更新商談結果
GET    /api/v1/consultations/{id}/summary  # AI 生成商談摘要

# 健康計畫
POST   /api/v1/plans                     # 建立計畫
GET    /api/v1/plans/{id}                # 計畫詳情
POST   /api/v1/plans/{id}/checkins       # 每日 checkin
GET    /api/v1/plans/{id}/progress       # 進度報表

# 知識庫
GET    /api/v1/objections                # 異議處理知識庫搜尋
POST   /api/v1/objections                # 新增異議處理

# 內容行銷
POST   /api/v1/content/generate          # AI 文案生成
POST   /api/v1/content/testimony         # AI 見證故事生成
POST   /api/v1/content/reply-suggest     # AI 回覆話術推薦

# 團隊管理
POST   /api/v1/goals                     # 設定目標
GET    /api/v1/dashboard/personal        # 個人績效儀表板
GET    /api/v1/dashboard/team            # 團隊績效儀表板
GET    /api/v1/dashboard/funnel          # 轉化漏斗
GET    /api/v1/training/progress         # 培訓進度

# 提醒系統
GET    /api/v1/reminders                 # 提醒列表
PATCH  /api/v1/reminders/{id}/dismiss    # 處理提醒
```

### 4.2 API 回應格式

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20
  }
}
```

---

## 5. 整合架構

### 5.1 n8n 工作流清單

| 工作流 | 觸發方式 | 說明 |
| :--- | :--- | :--- |
| lead-capture | Webhook | 從社群平台接收私訊 Lead |
| questionnaire-analysis | Webhook | 問卷提交後觸發 AI 分析 |
| auto-routing | Webhook | 問卷分析完成後自動分流 |
| consultation-reminder | Cron (每日) | 商談前提醒 |
| follow-up-reminder | Cron (每日) | 未成交追蹤提醒 |
| health-plan-reminder | Cron (每日) | 重生計畫每日提醒 |
| content-publish | Webhook | 內容多平台分發 |
| engagement-monitor | Cron (每小時) | 社群互動數據抓取 |
| repurchase-reminder | Cron (每日) | 續購提醒 |
| performance-report | Cron (每週) | 週績效報表生成 |

### 5.2 外部服務整合

| 服務 | 用途 | 整合方式 |
| :--- | :--- | :--- |
| Claude API | 文案生成、問卷分析、話術推薦 | REST API |
| Facebook Graph API | FB Page 貼文發布/互動監控 | OAuth + REST |
| X API v2 | X 貼文發布/互動監控 | OAuth + REST |
| LINE Messaging API | LINE OA 推播/互動 | Webhook + REST |
| Instagram Graph API | IG 貼文發布/互動監控 | OAuth + REST |
| Google Calendar API | 商談預約同步 | OAuth + REST |

---

## 6. 驗收標準總表

### 6.1 功能驗收

| 階段 | 驗收標準 |
| :--- | :--- |
| Phase 1 | 可完成名單 CRUD、客戶狀態流轉、前端列表與詳情頁正確渲染 |
| Phase 2 | 問卷可填答、AI 分析結果正確、分流規則正確觸發 |
| Phase 3 | 可預約商談、摘要正確生成、異議知識庫可搜尋 |
| Phase 4 | 計畫可追蹤、衛教推播準時、提醒系統正常 |
| Phase 5 | AI 文案可用、私訊助手正確推薦、n8n 多平台發布成功率 ≥ 95% |
| Phase 6 | 儀表板數據準確、培訓追蹤正常、告警準時 |

### 6.2 非功能驗收

| 項目 | 驗收標準 |
| :--- | :--- |
| 效能 | 頁面載入 < 2s、API 回應 < 500ms |
| 測試覆蓋率 | 後端 ≥ 80%、前端 ≥ 70% |
| 安全 | 無硬編碼秘密、輸入驗證、SQL injection 防護 |
| 可用性 | 支援 Chrome / Safari / Edge 最新兩版 |

---

## 7. 風險評估

| 風險 | 影響 | 機率 | 緩解措施 |
| :--- | :--- | :--- | :--- |
| 社群平台 API 變動 | 發布/監控功能中斷 | 中 | Adapter pattern 隔離平台差異 |
| AI 生成品質不穩定 | 文案/分析不可用 | 中 | 人工審核流程、prompt 持續優化 |
| 個資法規風險 | 法律糾紛 | 低 | 隱私模式、資料加密、同意書機制 |
| 問卷欄位不足/過多 | 分析不準確/填答率低 | 中 | 分段填答、持續迭代問卷設計 |
| 經營者數位素養不足 | 系統使用率低 | 高 | 簡化 UI、引導式操作、培訓教學 |

---

## 8. 時程總覽

```
Week  1-4   ████████ Phase 1: 基礎架構與核心 CRM
Week  5-8   ████████ Phase 2: 問卷評估系統
Week  9-12  ████████ Phase 3: 商談與成交支援
Week 13-16  ████████ Phase 4: 客戶管理與陪跑
Week 17-20  ████████ Phase 5: AI 內容行銷引擎
Week 21-24  ████████ Phase 6: 團隊管理與儀表板
```

**總工期估算**：24 週（約 6 個月）

---

## 9. 後續規劃文件清單

以下文件建議於各 Phase 啟動前產出：

| 文件 | 對應階段 | 說明 |
| :--- | :--- | :--- |
| 03_data_model_specification.md | Phase 1 | 完整 ERD、欄位定義、索引策略 |
| 04_routing_rules_specification.md | Phase 2 | 分流規則引擎詳細設計 |
| 05_ai_prompt_design.md | Phase 2, 5 | AI 提示詞設計與品質標準 |
| 06_integration_architecture.md | Phase 3, 5 | n8n 工作流詳細設計、外部 API 串接規格 |
| 07_ui_wireframes.md | Phase 1-6 | 各功能頁面線框圖 |
| 08_security_and_privacy.md | Phase 1 | 個資保護、加密、同意書機制 |
| 09_testing_strategy.md | Phase 1 | 測試策略、覆蓋率要求、E2E 測試案例 |
| 10_deployment_guide.md | Phase 6 | 部署架構、CI/CD、監控 |
