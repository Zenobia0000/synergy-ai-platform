# API 設計規範 - n8n 個人品牌內容分發平台

> **版本:** v1.0 | **更新:** 2026-03-17 | **狀態:** 草稿 | **OpenAPI 定義:** `/docs/openapi.yaml` (待產生)

---

## 1. 設計約定

| 項目 | 規範 |
| :--- | :--- |
| **風格** | RESTful |
| **Base URL** | Production: `https://{domain}/api/v1` / Development: `http://localhost:3000/api/v1` |
| **格式** | `application/json` (UTF-8) |
| **資源路徑** | 小寫、連字符、複數 (e.g., `/contents`, `/publish-logs`) |
| **欄位命名** | `snake_case` |
| **日期格式** | ISO 8601 含時區 (e.g., `2026-03-20T09:00:00+08:00`) |
| **認證** | MVP: HTTP Basic Auth / 後續: NextAuth.js Session Token in Cookie |
| **版本控制** | URL 路徑 (`/api/v1/...`) |

---

## 2. 通用行為

### 回應信封格式

所有 API 使用一致的信封格式：

**成功回應：**

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

**列表回應：**

```json
{
  "success": true,
  "data": [ ... ],
  "meta": {
    "request_id": "req_abc123",
    "pagination": {
      "total": 42,
      "page": 1,
      "limit": 20,
      "has_more": true
    }
  }
}
```

### 分頁

偏移量分頁: `page` (預設 1) + `limit` (預設 20, 最大 100)

### 排序

`sort_by=field` (升序) / `sort_by=-field` (降序)

預設排序: `-created_at` (最新在前)

### 過濾

欄位名直接作為查詢參數:

```
/api/v1/contents?status=draft&platforms=fb,x
/api/v1/dashboard/contents?status=success&sort_by=-publish_at
```

### 冪等性

- `POST /contents/:id/publish` 與 `POST /contents/:id/retry` 支援 `Idempotency-Key` header
- 伺服器 24h 內對同 key 返回相同結果，防止重複發佈

---

## 3. 錯誤處理

```json
{
  "success": false,
  "data": null,
  "error": {
    "type": "invalid_request_error",
    "code": "parameter_missing",
    "message": "缺少必要參數 title",
    "param": "title",
    "request_id": "req_abc123"
  }
}
```

| 錯誤碼 | HTTP | 描述 | 對應 BDD |
| :--- | :--- | :--- | :--- |
| `parameter_missing` | 400 | 缺少必要參數 | `content_management.feature` → 缺少必填欄位 |
| `parameter_invalid` | 400 | 參數格式無效（如 x_caption 超過 280 字） | `platform_caption.feature` → X 文案超過限制 |
| `invalid_schedule_time` | 400 | 排程時間為過去時間 | `scheduled_publishing.feature` → 排程時間設定為過去 |
| `no_platform_selected` | 400 | 未選擇任何目標平台 | `scheduled_publishing.feature` → 排程時未選擇平台 |
| `invalid_status_transition` | 409 | 不合法的狀態轉換 | `status_transitions.feature` → 不合法的狀態轉換 |
| `resource_not_found` | 404 | 資源不存在 | - |
| `delete_not_allowed` | 403 | 非草稿狀態不可刪除 | `content_management.feature` → 不可刪除已發佈貼文 |
| `authentication_failed` | 401 | 認證失敗 | - |
| `rate_limit_exceeded` | 429 | 超出速率限制 | - |
| `internal_server_error` | 500 | 伺服器錯誤 | - |
| `n8n_unreachable` | 502 | n8n 服務無法連線 | - |
| `webhook_verification_failed` | 401 | n8n Webhook 簽名驗證失敗 | - |

---

## 4. 安全性

| 項目 | 策略 |
| :--- | :--- |
| **TLS** | 強制 HTTPS (Cloudflare / Nginx reverse proxy) |
| **輸入驗證** | Zod schema 驗證所有請求體與查詢參數 |
| **SQL 注入** | Prisma ORM 參數化查詢 |
| **XSS** | React 預設 escape；富文本輸出使用 DOMPurify 清理 |
| **Webhook 驗證** | n8n 回報時驗證 HMAC-SHA256 簽名 (`X-N8N-Signature` header) |
| **速率限制** | 基於 IP，一般 API: 100 req/min；發佈/重試: 10 req/min |
| **安全 Headers** | HSTS, X-Content-Type-Options: nosniff, X-Frame-Options: DENY |
| **敏感資料** | API Token 不經由本系統 API 傳遞，僅存於 n8n Credentials |

---

## 5. API 端點定義

### 資源: 貼文 (Contents)

**路徑:** `/api/v1/contents`

對應 BDD: `content_management.feature`, `platform_caption.feature`

---

#### `POST /contents` - 建立貼文

- **說明**: 建立新貼文，預設狀態為 `draft`
- **對應 BDD**: 成功建立一篇新貼文、缺少必填欄位
- **請求體**: `ContentCreate`
- **回應**: `201 Created` → `Content`

**請求範例：**

```json
{
  "title": "三月品牌經營心得",
  "master_caption": "這個月學到的三件事...",
  "image_url": "https://example.com/images/march.jpg",
  "platforms": "fb,x,line",
  "fb_caption": null,
  "x_caption": "品牌經營三要點",
  "line_message": null
}
```

**回應範例：**

```json
{
  "success": true,
  "data": {
    "id": "cont_a1b2c3d4",
    "title": "三月品牌經營心得",
    "master_caption": "這個月學到的三件事...",
    "image_url": "https://example.com/images/march.jpg",
    "platforms": "fb,x,line",
    "publish_at": null,
    "status": "draft",
    "fb_caption": null,
    "ig_caption": null,
    "x_caption": "品牌經營三要點",
    "line_message": null,
    "retry_count": 0,
    "last_error": null,
    "created_at": "2026-03-17T14:30:00+08:00",
    "updated_at": "2026-03-17T14:30:00+08:00"
  },
  "meta": {
    "request_id": "req_abc123"
  }
}
```

**驗證規則：**

| 欄位 | 規則 |
| :--- | :--- |
| `title` | 必填，1-200 字元 |
| `master_caption` | 必填，1-10000 字元 |
| `image_url` | 選填，需為有效 URL |
| `platforms` | 必填，逗號分隔，值限 `fb,ig,x,line` |
| `x_caption` | 選填，最多 280 字元 |

---

#### `GET /contents` - 貼文列表

- **說明**: 取得貼文列表，支援分頁、狀態篩選、排序
- **參數**: `page`, `limit`, `sort_by`, `status`
- **回應**: `200 OK` → `{ data: Content[], meta: { pagination } }`

**請求範例：**

```
GET /api/v1/contents?status=draft&sort_by=-created_at&page=1&limit=20
```

---

#### `GET /contents/:id` - 取得貼文詳情

- **說明**: 取得單筆貼文完整資訊
- **回應**: `200 OK` → `Content`
- **錯誤**: `404` resource_not_found

---

#### `PUT /contents/:id` - 更新貼文

- **說明**: 更新貼文內容（僅 `draft` 狀態可完整編輯）
- **對應 BDD**: 編輯既有貼文
- **請求體**: `ContentUpdate`（部分更新）
- **回應**: `200 OK` → `Content`
- **限制**: `status` 為 `success` 時僅允許更新 `title`（用於管理標記）

**請求範例：**

```json
{
  "master_caption": "更新後的文案內容...",
  "x_caption": "更新後的 X 文案"
}
```

---

#### `DELETE /contents/:id` - 刪除貼文

- **說明**: 刪除貼文（僅 `draft` 狀態可刪除）
- **對應 BDD**: 刪除草稿貼文、不可刪除已發佈的貼文
- **回應**: `204 No Content`
- **錯誤**: `403` delete_not_allowed（非 draft 狀態）

---

### 資源: 排程與發佈 (Schedule & Publish)

**路徑:** `/api/v1/contents/:id/...`

對應 BDD: `scheduled_publishing.feature`, `multi_platform_distribution.feature`

---

#### `POST /contents/:id/schedule` - 設定排程

- **說明**: 為貼文設定排程發佈時間，狀態從 `draft` 轉為 `queued`
- **對應 BDD**: 設定排程時間後自動發佈、排程時間設定為過去時間、排程時未選擇平台
- **請求體**: `ScheduleCreate`
- **回應**: `200 OK` → `Content`（更新後）
- **冪等**: 支援 `Idempotency-Key`

**請求範例：**

```json
{
  "publish_at": "2026-03-20T09:00:00+08:00"
}
```

**驗證規則：**

| 規則 | 錯誤碼 |
| :--- | :--- |
| `publish_at` 必須為未來時間 | `invalid_schedule_time` |
| 貼文必須已選擇至少一個 `platforms` | `no_platform_selected` |
| 貼文 `status` 必須為 `draft` | `invalid_status_transition` |

---

#### `DELETE /contents/:id/schedule` - 取消排程

- **說明**: 取消排程，狀態從 `queued` 回到 `draft`
- **對應 BDD**: 取消已排程的貼文
- **回應**: `200 OK` → `Content`（更新後）
- **限制**: 僅 `queued` 狀態可取消

---

#### `POST /contents/:id/publish` - 立即發佈

- **說明**: 立即觸發 n8n 工作流發佈，狀態轉為 `publishing`
- **對應 BDD**: 立即發佈貼文
- **回應**: `202 Accepted` → `Content`（狀態已更新，發佈非同步進行）
- **冪等**: 支援 `Idempotency-Key`

**回應範例：**

```json
{
  "success": true,
  "data": {
    "id": "cont_a1b2c3d4",
    "status": "publishing",
    "publish_at": "2026-03-17T14:35:00+08:00"
  },
  "meta": {
    "request_id": "req_def456",
    "message": "發佈已觸發，請透過 SSE 或輪詢取得最新狀態"
  }
}
```

---

#### `POST /contents/:id/retry` - 補發失敗平台

- **說明**: 對失敗的平台重新觸發發佈，已成功平台不受影響
- **對應 BDD**: 單一平台手動補發、防止重複發送
- **請求體**: `RetryRequest`（選填，可指定平台）
- **回應**: `202 Accepted` → `Content`
- **冪等**: 支援 `Idempotency-Key`

**請求範例：**

```json
{
  "platforms": ["fb"]
}
```

若不帶 `platforms`，自動補發所有失敗的平台。

**驗證規則：**

| 規則 | 錯誤碼 |
| :--- | :--- |
| 貼文 `status` 須為 `partial_success` 或 `failed` | `invalid_status_transition` |
| 指定的平台必須是失敗狀態（不可對已成功平台補發） | `parameter_invalid` |
| `retry_count` 未達上限 (3) | `parameter_invalid` |

---

### 資源: n8n Webhook 回報 (Internal)

**路徑:** `/api/v1/webhooks/n8n`

此為內部 API，僅供 n8n 工作流回報結果使用。

---

#### `POST /webhooks/n8n/publish-result` - 發佈結果回報

- **說明**: n8n 發佈工作流完成後回報各平台結果
- **對應 BDD**: `multi_platform_distribution.feature`, `error_handling.feature`
- **驗證**: 必須包含有效的 `X-N8N-Signature` header (HMAC-SHA256)
- **請求體**: `PublishResultPayload`
- **回應**: `200 OK`

**請求範例：**

```json
{
  "content_id": "cont_a1b2c3d4",
  "workflow_execution_id": "exec_xyz789",
  "results": [
    {
      "platform": "fb",
      "status": "success",
      "external_post_id": "123456789_987654321",
      "response_summary": "Page post created successfully"
    },
    {
      "platform": "x",
      "status": "success",
      "external_post_id": "1234567890123456789",
      "response_summary": "Tweet created"
    },
    {
      "platform": "line",
      "status": "failed",
      "external_post_id": null,
      "response_summary": "401 Unauthorized - Invalid channel access token"
    }
  ]
}
```

**伺服器處理邏輯：**

```
1. 驗證 HMAC 簽名
2. 對每個 result 寫入 publish_logs
3. 計算整體狀態:
   - 全部 success → content.status = "success"
   - 部分 success → content.status = "partial_success"
   - 全部 failed → content.status = "failed", content.retry_count += 1
4. 更新 content_queue.last_error (取第一個失敗的 response_summary)
5. 透過 SSE 推送狀態更新至前端
```

---

### 資源: 發佈紀錄 (Publish Logs)

**路徑:** `/api/v1/contents/:id/logs`

對應 BDD: `publish_status_tracking.feature`

---

#### `GET /contents/:id/logs` - 取得發佈紀錄

- **說明**: 取得特定貼文的所有發佈執行紀錄
- **對應 BDD**: 查看詳細發佈日誌
- **參數**: `platform`（選填，篩選特定平台）
- **回應**: `200 OK` → `{ data: PublishLog[] }`

**回應範例：**

```json
{
  "success": true,
  "data": [
    {
      "log_id": "log_001",
      "content_id": "cont_a1b2c3d4",
      "platform": "fb",
      "status": "failed",
      "external_post_id": null,
      "response_summary": "401 Unauthorized - Token expired",
      "workflow_execution_id": "exec_xyz789",
      "created_at": "2026-03-20T09:00:05+08:00"
    },
    {
      "log_id": "log_002",
      "content_id": "cont_a1b2c3d4",
      "platform": "fb",
      "status": "success",
      "external_post_id": "123456789_987654321",
      "response_summary": "Page post created successfully (retry)",
      "workflow_execution_id": "exec_abc012",
      "created_at": "2026-03-20T10:15:00+08:00"
    }
  ],
  "meta": {
    "request_id": "req_ghi789"
  }
}
```

---

### 資源: 監控儀表板 (Dashboard)

**路徑:** `/api/v1/dashboard`

對應 BDD: `monitoring_dashboard.feature`, `publish_status_tracking.feature`

---

#### `GET /dashboard/overview` - 狀態統計總覽

- **說明**: 取得所有貼文的狀態分布統計
- **對應 BDD**: 在監控儀表板看到所有已發佈貼文的狀態總覽
- **回應**: `200 OK`

**回應範例：**

```json
{
  "success": true,
  "data": {
    "total": 42,
    "by_status": {
      "draft": 5,
      "queued": 2,
      "publishing": 1,
      "success": 28,
      "partial_success": 4,
      "failed": 2
    }
  },
  "meta": {
    "request_id": "req_jkl012"
  }
}
```

---

#### `GET /dashboard/contents` - 已發佈貼文列表（含互動數據）

- **說明**: 取得已發佈貼文列表，每筆包含各平台最新互動數據
- **對應 BDD**: 查看各平台互動數據、篩選特定平台
- **參數**: `page`, `limit`, `sort_by`, `status`, `platform`
- **回應**: `200 OK`

**回應範例：**

```json
{
  "success": true,
  "data": [
    {
      "id": "cont_a1b2c3d4",
      "title": "三月品牌經營心得",
      "status": "success",
      "publish_at": "2026-03-20T09:00:00+08:00",
      "platforms": "fb,x,line",
      "engagement": {
        "fb": {
          "external_post_id": "123456789_987654321",
          "likes": 42,
          "comments": 8,
          "shares": 3,
          "fetched_at": "2026-03-20T12:30:00+08:00"
        },
        "x": {
          "external_post_id": "1234567890123456789",
          "likes": 15,
          "comments": 2,
          "shares": 5,
          "fetched_at": "2026-03-20T12:30:00+08:00"
        },
        "line": {
          "external_post_id": null,
          "likes": 0,
          "comments": 0,
          "shares": 0,
          "fetched_at": null
        }
      }
    }
  ],
  "meta": {
    "request_id": "req_mno345",
    "pagination": {
      "total": 28,
      "page": 1,
      "limit": 20,
      "has_more": true
    }
  }
}
```

---

#### `GET /dashboard/contents/:id/engagement` - 互動數據歷史

- **說明**: 取得特定貼文在各平台的互動數據歷史趨勢
- **參數**: `platform`（選填）, `limit`（預設 50）
- **回應**: `200 OK`

**回應範例：**

```json
{
  "success": true,
  "data": {
    "content_id": "cont_a1b2c3d4",
    "history": [
      {
        "platform": "fb",
        "likes": 42,
        "comments": 8,
        "shares": 3,
        "fetched_at": "2026-03-20T12:30:00+08:00"
      },
      {
        "platform": "fb",
        "likes": 38,
        "comments": 6,
        "shares": 2,
        "fetched_at": "2026-03-20T12:00:00+08:00"
      }
    ]
  },
  "meta": {
    "request_id": "req_pqr678"
  }
}
```

---

#### `GET /dashboard/contents/:id/replies` - 回覆內容

- **說明**: 取得特定貼文在各平台的留言/回覆內容
- **對應 BDD**: 在儀表板集中查看各平台的留言/回覆內容
- **參數**: `platform`（選填）, `page`, `limit`, `sort_by`（預設 `-created_at`）
- **回應**: `200 OK`

**回應範例：**

```json
{
  "success": true,
  "data": [
    {
      "platform": "fb",
      "author": "John Doe",
      "content": "很棒的分享！",
      "created_at": "2026-03-20T11:45:00+08:00"
    },
    {
      "platform": "x",
      "author": "@user123",
      "content": "同意這個觀點",
      "created_at": "2026-03-20T10:30:00+08:00"
    }
  ],
  "meta": {
    "request_id": "req_stu901",
    "pagination": {
      "total": 10,
      "page": 1,
      "limit": 20,
      "has_more": false
    }
  }
}
```

---

### 資源: 即時狀態推送 (SSE)

**路徑:** `/api/v1/sse`

---

#### `GET /sse/contents/:id/status` - 訂閱貼文狀態更新

- **說明**: Server-Sent Events 串流，即時推送貼文發佈狀態變更
- **對應 BDD**: 發佈過程中即時更新狀態
- **回應**: `text/event-stream`

**事件格式：**

```
event: status_update
data: {"content_id":"cont_a1b2c3d4","status":"publishing","platform_updates":[{"platform":"fb","status":"success","external_post_id":"123"}]}

event: status_update
data: {"content_id":"cont_a1b2c3d4","status":"partial_success","platform_updates":[{"platform":"line","status":"failed","error":"401 Unauthorized"}]}
```

---

#### `GET /sse/dashboard` - 訂閱儀表板更新

- **說明**: 訂閱全域狀態更新（任何貼文狀態變更或新監控數據）
- **回應**: `text/event-stream`

**事件格式：**

```
event: content_status_changed
data: {"content_id":"cont_a1b2c3d4","status":"success"}

event: engagement_updated
data: {"content_id":"cont_a1b2c3d4","platform":"fb","likes":42,"comments":8}
```

---

## 6. 資料模型

### `Content`

```json
{
  "id": "string (cont_...)",
  "title": "string",
  "master_caption": "string",
  "image_url": "string | null",
  "platforms": "string (comma-separated: fb,ig,x,line)",
  "publish_at": "string (ISO 8601) | null",
  "status": "draft | queued | publishing | success | partial_success | failed",
  "fb_caption": "string | null",
  "ig_caption": "string | null",
  "x_caption": "string | null",
  "line_message": "string | null",
  "retry_count": "integer",
  "last_error": "string | null",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)"
}
```

### `ContentCreate`

```json
{
  "title": "string (required, 1-200 chars)",
  "master_caption": "string (required, 1-10000 chars)",
  "image_url": "string | null (optional, valid URL)",
  "platforms": "string (required, comma-separated, values: fb,ig,x,line)",
  "fb_caption": "string | null (optional)",
  "ig_caption": "string | null (optional)",
  "x_caption": "string | null (optional, max 280 chars)",
  "line_message": "string | null (optional)"
}
```

### `ContentUpdate`

```json
{
  "title": "string (optional, 1-200 chars)",
  "master_caption": "string (optional, 1-10000 chars)",
  "image_url": "string | null (optional)",
  "platforms": "string (optional)",
  "fb_caption": "string | null (optional)",
  "ig_caption": "string | null (optional)",
  "x_caption": "string | null (optional, max 280 chars)",
  "line_message": "string | null (optional)"
}
```

### `ScheduleCreate`

```json
{
  "publish_at": "string (required, ISO 8601, must be future time)"
}
```

### `RetryRequest`

```json
{
  "platforms": "string[] (optional, e.g. [\"fb\", \"line\"])"
}
```

### `PublishResultPayload`

```json
{
  "content_id": "string (required)",
  "workflow_execution_id": "string (required)",
  "results": [
    {
      "platform": "string (required, fb|ig|x|line)",
      "status": "string (required, success|failed)",
      "external_post_id": "string | null",
      "response_summary": "string"
    }
  ]
}
```

### `PublishLog`

```json
{
  "log_id": "string (log_...)",
  "content_id": "string",
  "platform": "fb | ig | x | line",
  "status": "success | failed",
  "external_post_id": "string | null",
  "response_summary": "string | null",
  "workflow_execution_id": "string | null",
  "created_at": "string (ISO 8601)"
}
```

### `EngagementData`

```json
{
  "platform": "fb | ig | x | line",
  "external_post_id": "string | null",
  "likes": "integer",
  "comments": "integer",
  "shares": "integer",
  "fetched_at": "string (ISO 8601) | null"
}
```

### `Reply`

```json
{
  "platform": "fb | ig | x | line",
  "author": "string",
  "content": "string",
  "created_at": "string (ISO 8601)"
}
```

---

## 7. API 端點總覽

| Method | Path | 說明 | 優先級 |
| :--- | :--- | :--- | :--- |
| `POST` | `/contents` | 建立貼文 | P0 |
| `GET` | `/contents` | 貼文列表 | P0 |
| `GET` | `/contents/:id` | 取得貼文詳情 | P0 |
| `PUT` | `/contents/:id` | 更新貼文 | P0 |
| `DELETE` | `/contents/:id` | 刪除草稿貼文 | P0 |
| `POST` | `/contents/:id/schedule` | 設定排程 | P0 |
| `DELETE` | `/contents/:id/schedule` | 取消排程 | P0 |
| `POST` | `/contents/:id/publish` | 立即發佈 | P0 |
| `POST` | `/contents/:id/retry` | 補發失敗平台 | P1 |
| `POST` | `/webhooks/n8n/publish-result` | n8n 發佈結果回報 | P0 |
| `GET` | `/contents/:id/logs` | 發佈紀錄 | P0 |
| `GET` | `/dashboard/overview` | 狀態統計總覽 | P0 |
| `GET` | `/dashboard/contents` | 已發佈貼文列表（含互動） | P1 |
| `GET` | `/dashboard/contents/:id/engagement` | 互動數據歷史 | P1 |
| `GET` | `/dashboard/contents/:id/replies` | 回覆內容 | P1 |
| `GET` | `/sse/contents/:id/status` | 訂閱貼文狀態 (SSE) | P1 |
| `GET` | `/sse/dashboard` | 訂閱儀表板更新 (SSE) | P2 |
