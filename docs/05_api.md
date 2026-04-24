# API 設計規範 — Synergy AI Closer's Copilot

> **版本:** v1.0 | **更新:** 2026-04-24 | **狀態:** 草稿 | **對應架構:** `docs/04_architecture.md`

---

## 1. 設計約定

| 項目 | 規範 |
| :--- | :--- |
| **風格** | RESTful + JSON |
| **Base URL** | Production: `https://api.synergy-ai.tw/v1` / Staging: `https://api-staging.synergy-ai.tw/v1` |
| **格式** | `application/json` (UTF-8) |
| **資源路徑** | 小寫、連字符、複數（e.g., `/leads`、`/questionnaire-templates`） |
| **欄位命名** | `snake_case` |
| **日期格式** | ISO 8601 UTC（e.g., `2026-05-01T14:00:00Z`） |
| **認證** | Supabase JWT in `Authorization: Bearer <jwt>` |
| **版本控制** | URL 路徑 `/v1/...` |
| **Tenant** | 由 JWT 的 `tenant_id` claim 決定，不在 URL |

---

## 2. 通用行為

### 分頁
簡單分頁：`?page=1&page_size=25`（預設 25，最大 100）

回應含：
```json
{
  "data": [...],
  "pagination": { "page": 1, "page_size": 25, "total": 137 }
}
```

### 排序
`?sort_by=created_at`（升序）/ `?sort_by=-created_at`（降序）

### 過濾
`?status=talked&health_level=A&last_contact_after=2026-05-01`

### 冪等性
非 GET 請求可帶 `Idempotency-Key` header，伺服器 24h 內對同 key 返回快取結果（用於問卷送出、摘要重生）。

---

## 3. 錯誤處理

統一格式：

```json
{
  "error": {
    "type": "invalid_request_error",
    "code": "parameter_missing",
    "message": "缺少必要參數 email",
    "param": "email",
    "request_id": "req_01HWX3..."
  }
}
```

| 錯誤碼 | HTTP | 描述 |
| :--- | :--- | :--- |
| `resource_not_found` | 404 | 資源不存在 |
| `parameter_invalid` | 400 | 參數格式無效 |
| `parameter_missing` | 400 | 缺少必要參數 |
| `authentication_failed` | 401 | JWT 無效或過期 |
| `permission_denied` | 403 | 無權限（如跨 tenant 存取、非本人客戶） |
| `rate_limit_exceeded` | 429 | 超出速率限制 |
| `questionnaire_token_expired` | 410 | 問卷連結失效（> 30 天） |
| `lead_status_invalid_transition` | 422 | 狀態機拒絕（如已成交不可回退） |
| `llm_generation_failed` | 503 | LLM 服務暫時不可用，已 retry 3 次 |
| `internal_server_error` | 500 | 伺服器錯誤 |

---

## 4. 安全性

- **TLS**：強制 HTTPS（TLS 1.3）
- **速率限制**：
  - 問卷端點（無 auth）：每 IP 10 req/min
  - 教練端點（JWT auth）：每 user 60 req/min
  - 回應含 `RateLimit-Limit / RateLimit-Remaining / RateLimit-Reset`
- **CORS**：只允許 `https://app.synergy-ai.tw` 與本機開發來源
- **安全 Headers**：HSTS、CSP、X-Content-Type-Options、Referrer-Policy
- **OWASP API Top 10**：已考量（輸入驗證、授權檢查、敏感資料、日誌）

---

## 5. API 端點清單

### 5.1 問卷（Questionnaire）— 無需登入

#### `GET /v1/questionnaires/{token}` — 取得填答頁（題目 + 進度）

- **授權**：無（token 本身即憑證）
- **路徑參數**：`token` (UUIDv4)
- **回應**：`200 OK` → `QuestionnaireSession`

```json
{
  "token": "a1b2c3d4-...",
  "template_version": "v1.0",
  "coach": { "name": "阿明", "brand": "Synergy" },
  "questions": [
    {
      "key": "sleep_hours",
      "type": "single_choice",
      "text": "過去 6 週每天睡眠時數？",
      "options": ["< 4 小時", "4-6 小時", "6-8 小時", "> 8 小時"],
      "required": true,
      "redactable": false
    }
  ],
  "progress": { "answered": 0, "total": 20 },
  "expires_at": "2026-05-24T00:00:00Z"
}
```

#### `PATCH /v1/questionnaires/{token}/answers` — 儲存中途進度

- **授權**：無
- **請求體**：

```json
{
  "answers": [
    { "question_key": "sleep_hours", "value": "4-6 小時" },
    { "question_key": "family_disease", "value": null, "is_redacted": true }
  ]
}
```

- **回應**：`200 OK` → `{ "saved": 2, "progress": { "answered": 10, "total": 20 } }`

#### `POST /v1/questionnaires/{token}/submit` — 送出問卷

- **授權**：無
- **冪等**：支援 `Idempotency-Key`
- **請求體**：`{ "prospect": { "name": "王小姐", "contact": "0912345678" } }`
- **回應**：`201 Created`

```json
{
  "lead_id": "lead_01HWX...",
  "public_summary": {
    "health_level": "B",
    "findings": [
      "睡眠品質偏低，需留意",
      "家族病史需定期追蹤",
      "飲食均衡度尚可"
    ],
    "disclaimer": "本摘要僅供健康參考，非醫療診斷。"
  },
  "briefing_status": "pending"
}
```

備註：`briefing_status` 初始為 `pending`，由背景任務更新為 `ready`。

---

### 5.2 商談摘要（Briefing）— 需教練登入

#### `GET /v1/leads/{lead_id}/briefing` — 取得商談摘要

- **授權**：JWT（須為該 lead 所屬 coach）
- **回應**：`200 OK` → `Briefing`

```json
{
  "id": "brf_01HWX...",
  "lead_id": "lead_01HWX...",
  "status": "ready",
  "content": {
    "pain_points": [
      "連續 6 週睡眠 < 6 小時",
      "家族糖尿病史",
      "上次減重失敗過 2 次"
    ],
    "recommended_products": [
      {
        "sku": "SY-A001",
        "name": "產品A",
        "reason": "含褪黑激素，對應睡眠問題（第 12 題）",
        "monthly_price_twd": 3500
      }
    ],
    "expected_objections": [
      {
        "objection": "我朋友吃了沒效",
        "suggested_response": "每個人體質不同，建議先做 2 週試用..."
      }
    ],
    "entry_angle": "從睡眠問題切入，再帶到整體健康管理",
    "confidence": 0.85
  },
  "generated_at": "2026-05-01T10:32:00Z",
  "llm_model": "gemini-2.5-flash"
}
```

若 `status=pending` → 回 `200` 但 `content: null`，前端需輪詢。

#### `POST /v1/leads/{lead_id}/briefing/regenerate` — 重新生成摘要

- **授權**：JWT
- **速率限制**：每 lead 每小時最多 3 次
- **回應**：`202 Accepted` → `{ "briefing_id": "brf_...", "status": "pending" }`

---

### 5.3 客戶管理（Leads / CRM）— 需教練登入

#### `GET /v1/leads` — 列表

- **授權**：JWT
- **查詢參數**：
  - `status`：`new` / `talked` / `closed_won` / `closed_lost`
  - `health_level`：`A` / `B` / `C`
  - `q`：姓名關鍵字搜尋
  - `sort_by`：`-created_at`（預設）、`-last_contact_at`、`name`
  - `page`、`page_size`
- **回應**：`200 OK`

```json
{
  "data": [
    {
      "id": "lead_01HWX...",
      "name": "王小姐",
      "contact": "0912345678",
      "status": "talked",
      "health_level": "B",
      "red_flags": ["家族糖尿病史", "睡眠差"],
      "last_contact_at": "2026-05-01T14:00:00Z",
      "questionnaire_submitted_at": "2026-04-28T10:00:00Z",
      "note": "客戶希望下週再聯絡"
    }
  ],
  "pagination": { "page": 1, "page_size": 25, "total": 50 }
}
```

#### `GET /v1/leads/{id}` — 單筆詳情（含問卷答案）

- **授權**：JWT
- **回應**：`200 OK` → `Lead` + `answers[]` + `briefing`（nested）

#### `PATCH /v1/leads/{id}` — 更新客戶

- **授權**：JWT
- **請求體**（所有欄位可選）：

```json
{
  "status": "closed_won",
  "note": "客戶今天下單了"
}
```

- **狀態機驗證**：若違反狀態轉換規則，回 422 `lead_status_invalid_transition`
- **副作用**：
  - `status` 變為 `talked` → 自動建立 48h/7d/30d 提醒
  - `status` 變為 `closed_won` → 取消所有未發送提醒
  - `last_contact_at` 自動更新為 `now()`
- **回應**：`200 OK` → 更新後的 `Lead`

#### `GET /v1/leads/{id}/status-history` — 狀態變更歷程

- **授權**：JWT
- **回應**：

```json
{
  "data": [
    { "from": "new", "to": "talked", "at": "2026-05-01T14:00:00Z" },
    { "from": "talked", "to": "closed_won", "at": "2026-05-05T09:00:00Z" }
  ]
}
```

---

### 5.4 提醒（Reminders）— 內部 + 教練查詢

#### `GET /v1/reminders` — 查詢自己的待處理提醒

- **授權**：JWT
- **查詢參數**：`status=pending|sent|cancelled`、`lead_id`
- **回應**：

```json
{
  "data": [
    {
      "id": "rem_01HWX...",
      "lead_id": "lead_01HWX...",
      "lead_name": "王小姐",
      "kind": "48h",
      "due_at": "2026-05-03T14:00:00Z",
      "status": "pending"
    }
  ]
}
```

#### `POST /v1/internal/reminders/scan` — 排程器呼叫（內部）

- **授權**：服務間 API Key（不對外）
- **用途**：APScheduler 每小時呼叫，掃描到期提醒並發送
- **回應**：`200 OK` → `{ "scanned": 120, "sent_line": 4, "sent_email": 1, "failed": 0 }`

---

### 5.5 LINE 綁定 Webhook（Coach onboarding）

#### `POST /v1/line/webhook` — LINE Messaging API 事件入口

- **授權**：LINE X-Line-Signature 驗證
- **用途**：接收教練加入 LINE OA 好友事件（`follow` event），建立 `coaches.line_user_id` 綁定
- **請求體**：LINE 標準 webhook payload
- **回應**：`200 OK`（LINE 要求 1 秒內回應）
- **副作用**：
  - `follow` → 回 welcome 訊息 + 綁定引導（帶 coach token 的深連結）
  - `unfollow` → 標記 coach.line_user_id = null，後續提醒降級 Email

#### `POST /v1/coaches/me/line/bind` — 確認綁定

- **授權**：JWT
- **請求體**：`{ "line_bind_token": "..." }`（由 LINE webhook 發送的引導訊息帶入）
- **回應**：`200 OK` → `{ "line_bound": true, "line_user_id": "U..." }`

---

### 5.6 認證（Auth）— Supabase 直接提供

認證流程完全使用 Supabase Auth，不自建端點。前端直接呼叫：

- `supabase.auth.signInWithOtp({ email })` → 寄送 Magic Link
- Magic Link 點擊後回到 `app.synergy-ai.tw/auth/callback`
- 後端 FastAPI 透過 `Authorization: Bearer <jwt>` 驗證每個請求

後端 API 預期 JWT 含 claims：
```json
{
  "sub": "coach_01HWX...",
  "email": "aming@example.com",
  "tenant_id": "synergy",
  "role": "coach",
  "exp": 1715000000
}
```

---

## 6. 資料模型

### `Lead`

```json
{
  "id": "lead_01HWX...",
  "object": "lead",
  "tenant_id": "synergy",
  "coach_id": "coach_01HWX...",
  "name": "王小姐",
  "contact": "0912345678",
  "status": "new | talked | closed_won | closed_lost",
  "health_level": "A | B | C | null",
  "red_flags": ["家族糖尿病史"],
  "last_contact_at": "2026-05-01T14:00:00Z",
  "questionnaire_id": "q_01HWX...",
  "briefing_id": "brf_01HWX...",
  "note": "客戶備註",
  "created_at": "2026-04-28T10:00:00Z",
  "updated_at": "2026-05-01T14:00:00Z"
}
```

### `Briefing`

見 5.2 回應範例。

### `Reminder`

```json
{
  "id": "rem_01HWX...",
  "object": "reminder",
  "tenant_id": "synergy",
  "lead_id": "lead_01HWX...",
  "coach_id": "coach_01HWX...",
  "kind": "48h | 7d | 30d",
  "due_at": "2026-05-03T14:00:00Z",
  "sent_at": null,
  "status": "pending | sent | cancelled | failed",
  "channel": "line | email",
  "channel_attempts": [
    { "channel": "line", "attempted_at": "...", "result": "failed", "reason": "user_not_bound" },
    { "channel": "email", "attempted_at": "...", "result": "sent" }
  ],
  "created_at": "2026-05-01T14:00:00Z"
}
```

### `QuestionnaireAnswer`

```json
{
  "question_key": "sleep_hours",
  "value": "4-6 小時",
  "is_redacted": false,
  "answered_at": "2026-04-28T10:05:00Z"
}
```

---

## 7. Webhook（Phase 2 預留）

MVP **不提供** webhook。Phase 2 會新增：
- `lead.created` — 新名單建立
- `lead.status_changed` — 狀態變更
- `briefing.ready` — 摘要生成完成

---

## 8. OpenAPI / Swagger

FastAPI 自動產生：
- Staging: `https://api-staging.synergy-ai.tw/docs`
- OpenAPI JSON: `https://api-staging.synergy-ai.tw/openapi.json`

Production 預設關閉 `/docs`，只對內部啟用。

---

## 9. 版本演進政策

- **Breaking change**：bump major（`/v1` → `/v2`），保留舊版 6 個月
- **Additive change**：同一 major 版本內新增欄位
- **Deprecation**：透過 `Sunset` header 通知 3 個月前
