# 模組規格與測試案例 - n8n 個人品牌內容分發平台

> **版本:** v1.0 | **更新:** 2026-03-17 | **狀態:** 草稿

**對應架構文件**: `docs/architecture_and_design_document.md` 第 8 部分
**對應 BDD Feature**: `docs/behavior_driven_development_guide.md`

---

## 模組: ContentService（內容管理服務）

### 規格: createContent

**描述**: 建立新貼文，驗證必填欄位與平台文案限制，儲存至資料庫並回傳建立結果。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. `title` 為非空字串，1-200 字元 2. `master_caption` 為非空字串，1-10000 字元 3. `platforms` 至少包含一個有效平台值（fb/ig/x/line） 4. `x_caption` 若提供，不超過 280 字元 |
| **後置條件** | 1. 資料庫新增一筆 content_queue 記錄 2. 回傳的 `status` 為 `"draft"` 3. `retry_count` 為 0 4. `created_at` 與 `updated_at` 已設定 |
| **不變性** | 1. `id` 為唯一 UUID 2. 新建貼文 `status` 永遠為 `"draft"` |

---

#### TC-CM-001: 成功建立貼文（正常路徑）

- **Arrange**: 準備有效的 ContentCreate 資料（title, master_caption, platforms="fb,x,line"）
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 回傳 Content 物件，status="draft"，retry_count=0，id 為有效 UUID

#### TC-CM-002: 缺少必填欄位 title

- **Arrange**: 準備 ContentCreate 資料，title 為空字串
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 拋出 ValidationError，code="parameter_missing"，param="title"

#### TC-CM-003: 缺少必填欄位 master_caption

- **Arrange**: 準備 ContentCreate 資料，master_caption 為 undefined
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 拋出 ValidationError，code="parameter_missing"，param="master_caption"

#### TC-CM-004: X 文案超過 280 字元

- **Arrange**: 準備 ContentCreate 資料，x_caption 為 281 字元字串
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 拋出 ValidationError，code="parameter_invalid"，param="x_caption"

#### TC-CM-005: master_caption 超過上限 10000 字元

- **Arrange**: 準備 ContentCreate 資料，master_caption 為 10001 字元
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 拋出 ValidationError，code="parameter_invalid"，param="master_caption"

#### TC-CM-006: platforms 包含無效平台值

- **Arrange**: 準備 ContentCreate 資料，platforms="fb,twitter"
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 拋出 ValidationError，code="parameter_invalid"，param="platforms"

#### TC-CM-007: 選填欄位為 null 時正常建立

- **Arrange**: 準備 ContentCreate 資料，image_url=null, fb_caption=null, x_caption=null
- **Act**: 呼叫 `contentService.createContent(data)`
- **Assert**: 回傳 Content 物件，選填欄位為 null

---

### 規格: updateContent

**描述**: 更新既有貼文。draft 狀態可完整編輯，success 狀態僅允許更新 title。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. `id` 對應的貼文存在 2. 更新欄位通過驗證（同 createContent 規則） |
| **後置條件** | 1. 資料庫中該筆記錄已更新 2. `updated_at` 已更新為當前時間 3. 未提供的欄位保持不變 |
| **不變性** | 1. `id`、`created_at` 不可變更 2. `status`、`retry_count` 不透過此方法變更 |

---

#### TC-CM-008: 成功更新 draft 貼文

- **Arrange**: 資料庫中有一筆 status="draft" 的貼文
- **Act**: 呼叫 `contentService.updateContent(id, { master_caption: "新文案" })`
- **Assert**: 回傳更新後的 Content，master_caption 為 "新文案"，updated_at 已更新

#### TC-CM-009: 更新不存在的貼文

- **Arrange**: 使用不存在的 id
- **Act**: 呼叫 `contentService.updateContent(invalidId, data)`
- **Assert**: 拋出 NotFoundError，code="resource_not_found"

#### TC-CM-010: success 狀態僅允許更新 title

- **Arrange**: 資料庫中有一筆 status="success" 的貼文
- **Act**: 呼叫 `contentService.updateContent(id, { master_caption: "新文案" })`
- **Assert**: 拋出 ForbiddenError，僅 title 欄位可更新

---

### 規格: deleteContent

**描述**: 刪除貼文。僅 draft 狀態可刪除，同時清除關聯的 publish_logs 與 monitor_data。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. `id` 對應的貼文存在 2. 貼文 `status` 為 `"draft"` |
| **後置條件** | 1. content_queue 中該筆記錄已刪除 2. 關聯的 publish_logs 已刪除 3. 關聯的 monitor_data 已刪除 |
| **不變性** | 1. 非 draft 狀態的貼文不被影響 |

---

#### TC-CM-011: 成功刪除 draft 貼文

- **Arrange**: 資料庫中有一筆 status="draft" 的貼文
- **Act**: 呼叫 `contentService.deleteContent(id)`
- **Assert**: 資料庫中該筆記錄不存在

#### TC-CM-012: 不可刪除已發佈貼文

- **Arrange**: 資料庫中有一筆 status="success" 的貼文
- **Act**: 呼叫 `contentService.deleteContent(id)`
- **Assert**: 拋出 ForbiddenError，code="delete_not_allowed"

#### TC-CM-013: 不可刪除排程中的貼文

- **Arrange**: 資料庫中有一筆 status="queued" 的貼文
- **Act**: 呼叫 `contentService.deleteContent(id)`
- **Assert**: 拋出 ForbiddenError，code="delete_not_allowed"

---

### 規格: getContent / listContents

**描述**: 取得單筆或列表貼文資料，支援分頁、狀態篩選、排序。

---

#### TC-CM-014: 取得單筆貼文

- **Arrange**: 資料庫中有一筆貼文
- **Act**: 呼叫 `contentService.getContent(id)`
- **Assert**: 回傳完整 Content 物件

#### TC-CM-015: 取得不存在的貼文

- **Arrange**: 使用不存在的 id
- **Act**: 呼叫 `contentService.getContent(invalidId)`
- **Assert**: 拋出 NotFoundError

#### TC-CM-016: 列表查詢含分頁

- **Arrange**: 資料庫中有 25 筆貼文
- **Act**: 呼叫 `contentService.listContents({ page: 1, limit: 10 })`
- **Assert**: 回傳 10 筆資料，pagination.total=25, has_more=true

#### TC-CM-017: 依狀態篩選

- **Arrange**: 資料庫中有 draft 3 筆、success 5 筆
- **Act**: 呼叫 `contentService.listContents({ status: "draft" })`
- **Assert**: 回傳 3 筆資料，全部 status="draft"

#### TC-CM-018: 依建立時間倒序排列

- **Arrange**: 資料庫中有 3 筆不同建立時間的貼文
- **Act**: 呼叫 `contentService.listContents({ sort_by: "-created_at" })`
- **Assert**: 回傳結果按 created_at 降序排列

---

## 模組: ScheduleService（排程發佈服務）

### 規格: scheduleContent

**描述**: 為貼文設定排程時間，將狀態從 draft 轉為 queued。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 貼文存在且 status="draft" 2. `publish_at` 為未來時間 3. `platforms` 已設定且包含至少一個有效平台 |
| **後置條件** | 1. 貼文 `status` 更新為 `"queued"` 2. `publish_at` 已設定 |
| **不變性** | 1. 其他貼文不受影響 2. 狀態轉換遵循狀態機規則 |

---

#### TC-SC-001: 成功設定排程

- **Arrange**: 資料庫中有 status="draft"、platforms="fb,x" 的貼文
- **Act**: 呼叫 `scheduleService.scheduleContent(id, { publish_at: futureTime })`
- **Assert**: 貼文 status="queued"，publish_at 已設定

#### TC-SC-002: 排程時間為過去

- **Arrange**: 資料庫中有 status="draft" 的貼文
- **Act**: 呼叫 `scheduleService.scheduleContent(id, { publish_at: pastTime })`
- **Assert**: 拋出 ValidationError，code="invalid_schedule_time"

#### TC-SC-003: 未選擇任何平台

- **Arrange**: 資料庫中有 status="draft"、platforms="" 的貼文
- **Act**: 呼叫 `scheduleService.scheduleContent(id, { publish_at: futureTime })`
- **Assert**: 拋出 ValidationError，code="no_platform_selected"

#### TC-SC-004: 非 draft 狀態不可排程

- **Arrange**: 資料庫中有 status="success" 的貼文
- **Act**: 呼叫 `scheduleService.scheduleContent(id, { publish_at: futureTime })`
- **Assert**: 拋出 ConflictError，code="invalid_status_transition"

---

### 規格: cancelSchedule

**描述**: 取消排程，將狀態從 queued 回到 draft。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 貼文存在且 status="queued" |
| **後置條件** | 1. 貼文 `status` 更新為 `"draft"` 2. `publish_at` 清除為 null |
| **不變性** | 1. 貼文內容不變 |

---

#### TC-SC-005: 成功取消排程

- **Arrange**: 資料庫中有 status="queued" 的貼文
- **Act**: 呼叫 `scheduleService.cancelSchedule(id)`
- **Assert**: 貼文 status="draft"，publish_at=null

#### TC-SC-006: 非 queued 狀態不可取消

- **Arrange**: 資料庫中有 status="publishing" 的貼文
- **Act**: 呼叫 `scheduleService.cancelSchedule(id)`
- **Assert**: 拋出 ConflictError，code="invalid_status_transition"

---

## 模組: PublishService（發佈服務）

### 規格: publishNow

**描述**: 立即觸發 n8n 工作流發佈，狀態轉為 publishing。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 貼文存在且 status 為 "draft" 或 "queued" 2. platforms 已設定 3. n8n 服務可達 |
| **後置條件** | 1. 貼文 status="publishing" 2. n8n Webhook 已被觸發 3. publish_at 更新為當前時間 |
| **不變性** | 1. 貼文內容不被修改 |

---

#### TC-PB-001: 成功立即發佈

- **Arrange**: 資料庫中有 status="draft"、platforms="fb,x" 的貼文，n8n 正常運行
- **Act**: 呼叫 `publishService.publishNow(id)`
- **Assert**: 貼文 status="publishing"，n8n Webhook 被呼叫一次

#### TC-PB-002: n8n 服務不可達

- **Arrange**: 資料庫中有 status="draft" 的貼文，n8n 服務關閉
- **Act**: 呼叫 `publishService.publishNow(id)`
- **Assert**: 拋出 ServiceUnavailableError，code="n8n_unreachable"，貼文 status 維持 "draft"

#### TC-PB-003: 冪等性 - 重複發佈請求

- **Arrange**: 使用相同 Idempotency-Key 的兩次請求
- **Act**: 連續呼叫兩次 `publishService.publishNow(id, idempotencyKey)`
- **Assert**: n8n Webhook 僅被觸發一次，兩次回傳結果相同

---

### 規格: handlePublishResult

**描述**: 處理 n8n 回報的發佈結果，寫入 publish_logs，計算並更新整體狀態。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. Webhook 簽名驗證通過 2. content_id 對應的貼文存在 3. results 陣列非空 |
| **後置條件** | 1. 每個 result 寫入一筆 publish_logs 2. content_queue.status 依規則更新 3. 失敗時 retry_count += 1 4. last_error 更新為第一個失敗的 response_summary |
| **不變性** | 1. 已存在的 publish_logs 不被修改 2. 已成功平台的 external_post_id 不被覆蓋 |

---

#### TC-PB-004: 全部平台成功

- **Arrange**: 貼文 status="publishing"，platforms="fb,x,line"
- **Act**: 呼叫 `publishService.handlePublishResult({ content_id, results: [全部 success] })`
- **Assert**: 貼文 status="success"，publish_logs 新增 3 筆，每筆 status="success"

#### TC-PB-005: 部分平台失敗

- **Arrange**: 貼文 status="publishing"，platforms="fb,x,line"
- **Act**: 呼叫 `publishService.handlePublishResult({ content_id, results: [fb:success, x:success, line:failed] })`
- **Assert**: 貼文 status="partial_success"，last_error 為 LINE 的錯誤訊息

#### TC-PB-006: 全部平台失敗

- **Arrange**: 貼文 status="publishing"，platforms="fb,x"
- **Act**: 呼叫 `publishService.handlePublishResult({ content_id, results: [全部 failed] })`
- **Assert**: 貼文 status="failed"，retry_count += 1

#### TC-PB-007: Webhook 簽名驗證失敗

- **Arrange**: 請求帶有無效的 X-N8N-Signature header
- **Act**: 呼叫 `publishService.handlePublishResult(payload, invalidSignature)`
- **Assert**: 拋出 AuthenticationError，code="webhook_verification_failed"

---

### 規格: retryFailedPlatforms

**描述**: 對失敗的平台重新觸發發佈，已成功平台跳過。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 貼文 status 為 "partial_success" 或 "failed" 2. retry_count < 3 3. 指定的平台在最近一次發佈中為 failed |
| **後置條件** | 1. n8n Webhook 被觸發，僅包含失敗平台 2. 貼文 status 更新為 "publishing" |
| **不變性** | 1. 已成功且有 external_post_id 的平台不被重發 |

---

#### TC-PB-008: 成功補發失敗平台

- **Arrange**: 貼文 status="partial_success"，fb:failed, x:success(有 post_id)
- **Act**: 呼叫 `publishService.retryFailedPlatforms(id)`
- **Assert**: n8n Webhook 僅包含 fb 平台，x 被排除

#### TC-PB-009: 指定特定平台補發

- **Arrange**: 貼文 status="partial_success"，fb:failed, line:failed
- **Act**: 呼叫 `publishService.retryFailedPlatforms(id, { platforms: ["fb"] })`
- **Assert**: n8n Webhook 僅包含 fb 平台

#### TC-PB-010: retry_count 達上限

- **Arrange**: 貼文 status="failed"，retry_count=3
- **Act**: 呼叫 `publishService.retryFailedPlatforms(id)`
- **Assert**: 拋出 ValidationError，提示已達重試上限

#### TC-PB-011: 不可對已成功平台補發

- **Arrange**: 貼文 status="partial_success"，fb:success
- **Act**: 呼叫 `publishService.retryFailedPlatforms(id, { platforms: ["fb"] })`
- **Assert**: 拋出 ValidationError，code="parameter_invalid"

---

## 模組: MonitorService（監控服務）

### 規格: getEngagement

**描述**: 取得特定貼文在各平台的最新互動數據。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. content_id 對應的貼文存在 |
| **後置條件** | 1. 回傳各平台最新一筆 monitor_data |
| **不變性** | 1. monitor_data 不被修改 |

---

#### TC-MN-001: 取得有互動數據的貼文

- **Arrange**: 資料庫中有 fb 和 x 的 monitor_data 各 3 筆（不同 fetched_at）
- **Act**: 呼叫 `monitorService.getEngagement(contentId)`
- **Assert**: 回傳 fb 和 x 各取最新一筆，包含 likes/comments/shares

#### TC-MN-002: 尚無互動數據的貼文

- **Arrange**: 貼文剛發佈，monitor_data 為空
- **Act**: 呼叫 `monitorService.getEngagement(contentId)`
- **Assert**: 回傳各平台 likes=0, comments=0, shares=0, fetched_at=null

#### TC-MN-003: 按平台篩選互動數據

- **Arrange**: 有 fb 和 x 的 monitor_data
- **Act**: 呼叫 `monitorService.getEngagement(contentId, { platform: "fb" })`
- **Assert**: 僅回傳 fb 的數據

---

### 規格: getReplies

**描述**: 取得特定貼文在各平台的回覆內容，合併後依時間排序。

---

#### TC-MN-004: 取得多平台回覆

- **Arrange**: fb 有 3 則回覆，x 有 2 則回覆（存於 recent_replies JSON）
- **Act**: 呼叫 `monitorService.getReplies(contentId)`
- **Assert**: 回傳 5 則回覆，按 created_at 降序，每則標示 platform

#### TC-MN-005: 無回覆的貼文

- **Arrange**: monitor_data 存在但 recent_replies 為空陣列
- **Act**: 呼叫 `monitorService.getReplies(contentId)`
- **Assert**: 回傳空陣列

---

### 規格: getDashboardOverview

**描述**: 取得所有貼文的狀態分布統計。

---

#### TC-MN-006: 取得狀態統計

- **Arrange**: 資料庫中 draft:5, queued:2, success:28, partial_success:4, failed:2
- **Act**: 呼叫 `monitorService.getDashboardOverview()`
- **Assert**: 回傳 total=41，by_status 各值正確

#### TC-MN-007: 空資料庫

- **Arrange**: 資料庫中無任何貼文
- **Act**: 呼叫 `monitorService.getDashboardOverview()`
- **Assert**: 回傳 total=0，所有狀態計數為 0

---

## 模組: WebhookSignatureVerifier（Webhook 簽名驗證）

### 規格: verify

**描述**: 驗證 n8n Webhook 回報的 HMAC-SHA256 簽名。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 請求包含 `X-N8N-Signature` header 2. WEBHOOK_SECRET 環境變數已設定 |
| **後置條件** | 1. 驗證通過回傳 true，失敗拋出 AuthenticationError |
| **不變性** | 1. 請求 body 不被修改 |

---

#### TC-WH-001: 有效簽名通過驗證

- **Arrange**: 使用 WEBHOOK_SECRET 對 body 計算 HMAC-SHA256
- **Act**: 呼叫 `verifier.verify(body, validSignature)`
- **Assert**: 回傳 true

#### TC-WH-002: 無效簽名被拒絕

- **Arrange**: 使用錯誤的 secret 計算簽名
- **Act**: 呼叫 `verifier.verify(body, invalidSignature)`
- **Assert**: 拋出 AuthenticationError

#### TC-WH-003: 缺少簽名 header

- **Arrange**: 請求未包含 X-N8N-Signature header
- **Act**: 呼叫 `verifier.verify(body, undefined)`
- **Assert**: 拋出 AuthenticationError

---

## 模組: StatusMachine（狀態機）

### 規格: transition

**描述**: 驗證並執行貼文狀態轉換，確保遵循合法的狀態轉換路徑。

**契約式設計 (DbC)**:

| 類型 | 條件 |
| :--- | :--- |
| **前置條件** | 1. 當前狀態為有效狀態值 2. 目標狀態為有效狀態值 |
| **後置條件** | 1. 合法轉換回傳新狀態 2. 非法轉換拋出 ConflictError |
| **不變性** | 1. 合法轉換路徑不可被運行時修改 |

**合法轉換表：**

| 從 | 到 | 觸發條件 |
| :--- | :--- | :--- |
| draft | queued | 使用者設定排程 |
| queued | draft | 使用者取消排程 |
| queued | publishing | 排程時間到 / 立即發佈 |
| draft | publishing | 立即發佈 |
| publishing | success | 全部平台成功 |
| publishing | partial_success | 部分成功 |
| publishing | failed | 全部失敗 |
| partial_success | publishing | 補發觸發 |
| failed | queued | 重試觸發 |

---

#### TC-SM-001: 合法轉換 draft → queued

- **Act**: 呼叫 `statusMachine.transition("draft", "queued")`
- **Assert**: 回傳 "queued"

#### TC-SM-002: 合法轉換 publishing → partial_success

- **Act**: 呼叫 `statusMachine.transition("publishing", "partial_success")`
- **Assert**: 回傳 "partial_success"

#### TC-SM-003: 非法轉換 success → draft

- **Act**: 呼叫 `statusMachine.transition("success", "draft")`
- **Assert**: 拋出 ConflictError，code="invalid_status_transition"

#### TC-SM-004: 非法轉換 draft → success（跳過中間狀態）

- **Act**: 呼叫 `statusMachine.transition("draft", "success")`
- **Assert**: 拋出 ConflictError，code="invalid_status_transition"

#### TC-SM-005: 合法轉換 failed → queued（重試）

- **Act**: 呼叫 `statusMachine.transition("failed", "queued")`
- **Assert**: 回傳 "queued"

---

## 測試案例總覽

| 模組 | 測試數量 | 覆蓋範圍 |
| :--- | :--- | :--- |
| ContentService | 18 | CRUD、驗證、分頁、篩選、排序 |
| ScheduleService | 6 | 排程設定、取消、狀態驗證 |
| PublishService | 11 | 立即發佈、結果處理、補發、冪等、簽名 |
| MonitorService | 7 | 互動數據、回覆彙整、統計總覽 |
| WebhookSignatureVerifier | 3 | 簽名驗證正常/異常/缺失 |
| StatusMachine | 5 | 合法/非法狀態轉換 |
| **合計** | **50** | |
