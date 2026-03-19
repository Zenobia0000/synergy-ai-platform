# BDD 行為驅動情境指南 - n8n 個人品牌內容分發平台

> **版本:** v1.0 | **更新:** 2026-03-17

---

## Gherkin 語法速查

| 關鍵字 | 用途 |
| :--- | :--- |
| `Feature` | 高層次功能，對應 PRD 中的 Epic |
| `Scenario` | 具體業務場景/測試案例 |
| `Given` | 初始狀態 (Arrange) |
| `When` | 使用者操作 (Act) |
| `Then` | 預期結果 (Assert) |
| `And/But` | 連接多個步驟 |
| `Background` | 所有 Scenario 共用的前置步驟 |
| `Scenario Outline` + `Examples` | 參數化多組資料測試 |

---

## Feature 1: 貼文管理

**檔案名稱**: `content_management.feature`

```gherkin
Feature: 貼文管理
  # 對應 PRD: Epic 1 - 內容管理與發佈 (US-001)
  # 使用者可在 Web 介面建立、編輯、刪除貼文

  Background:
    Given 使用者已登入內容分發平台

  @happy-path @smoke-test
  Scenario: 成功建立一篇新貼文
    Given 我在貼文編輯頁面
    When 我輸入標題 "三月品牌經營心得"
    And 我輸入母文案 "這個月學到的三件事..."
    And 我上傳一張圖片
    And 我選擇目標平台 "fb, x, line"
    Then 我應該看到貼文已儲存為草稿
    And 貼文狀態應為 "draft"

  @happy-path
  Scenario: 編輯既有貼文
    Given 我有一篇狀態為 "draft" 的貼文
    When 我修改母文案內容
    And 我儲存變更
    Then 貼文內容應更新為最新版本
    And 更新時間應被記錄

  @happy-path
  Scenario: 刪除草稿貼文
    Given 我有一篇狀態為 "draft" 的貼文
    When 我刪除這篇貼文
    Then 貼文應從列表中移除
    And 資料庫中該筆記錄應被刪除

  @sad-path
  Scenario: 建立貼文時缺少必填欄位
    Given 我在貼文編輯頁面
    When 我未輸入標題
    And 我嘗試儲存貼文
    Then 我應該看到錯誤訊息 "標題為必填欄位"
    And 貼文不應被儲存

  @sad-path
  Scenario: 不可刪除已發佈的貼文
    Given 我有一篇狀態為 "success" 的貼文
    When 我嘗試刪除這篇貼文
    Then 我應該看到錯誤訊息 "已發佈的貼文無法刪除"

  @edge-case
  Scenario Outline: 母文案字數驗證
    Given 我在貼文編輯頁面
    When 我輸入母文案長度為 <length> 個字元
    Then 我應該看到 "<message>"

    Examples:
      | length | message       |
      | 0      | 文案為必填欄位    |
      | 5000   | 文案已儲存      |
      | 10001  | 文案超過字數上限  |
```

---

## Feature 2: 平台專屬文案

**檔案名稱**: `platform_caption.feature`

```gherkin
Feature: 平台專屬文案
  # 對應 PRD: Epic 1 - 內容管理與發佈 (US-003)
  # 同一份母內容可自動轉成或手動覆寫各平台格式

  Background:
    Given 使用者已登入內容分發平台
    And 我有一篇包含母文案的草稿貼文

  @happy-path
  Scenario: 使用母文案自動填入各平台文案
    Given 我的母文案為 "今天來聊聊品牌經營"
    And 我選擇目標平台 "fb, x, line"
    When 我未手動填寫平台專屬文案
    Then Facebook 文案應自動使用母文案
    And X 文案應自動使用母文案（截斷至 280 字元）
    And LINE 訊息應自動使用母文案

  @happy-path
  Scenario: 手動覆寫特定平台文案
    Given 我的母文案為 "今天來聊聊品牌經營"
    When 我手動填寫 X 專屬文案為 "品牌經營三要點 🔥"
    Then X 發佈時應使用 "品牌經營三要點 🔥"
    And 其他平台仍使用母文案

  @edge-case
  Scenario: X 文案超過 280 字元限制
    Given 我手動填寫 X 專屬文案超過 280 字元
    When 我嘗試儲存
    Then 我應該看到警告 "X 平台文案超過 280 字元限制"
```

---

## Feature 3: 排程發佈

**檔案名稱**: `scheduled_publishing.feature`

```gherkin
Feature: 排程發佈
  # 對應 PRD: Epic 1 - 內容管理與發佈 (US-002)
  # 使用者可設定排程時間，系統自動透過 n8n 發佈

  Background:
    Given 使用者已登入內容分發平台
    And n8n 工作流已正常運行

  @happy-path @smoke-test
  Scenario: 設定排程時間後自動發佈
    Given 我有一篇狀態為 "draft" 的貼文
    And 我選擇目標平台 "x"
    When 我設定排程時間為未來的某個時間點
    And 我確認排程
    Then 貼文狀態應變為 "queued"
    And 當排程時間到達時，n8n 應觸發發佈工作流
    And 發佈成功後貼文狀態應變為 "success"

  @happy-path
  Scenario: 立即發佈貼文
    Given 我有一篇狀態為 "draft" 的貼文
    And 我選擇目標平台 "fb, x"
    When 我選擇 "立即發佈"
    Then 貼文狀態應立即變為 "publishing"
    And n8n 工作流應被即時觸發

  @sad-path
  Scenario: 排程時間設定為過去時間
    Given 我在設定排程時間
    When 我輸入一個已過去的時間
    Then 我應該看到錯誤訊息 "排程時間必須為未來時間"
    And 排程不應被建立

  @sad-path
  Scenario: 排程時未選擇任何平台
    Given 我有一篇草稿貼文
    When 我設定排程時間但未選擇任何目標平台
    And 我嘗試確認排程
    Then 我應該看到錯誤訊息 "請至少選擇一個目標平台"

  @edge-case
  Scenario: 取消已排程的貼文
    Given 我有一篇狀態為 "queued" 的貼文
    When 我取消排程
    Then 貼文狀態應回到 "draft"
    And n8n 不應在原定時間觸發發佈
```

---

## Feature 4: 多平台分發

**檔案名稱**: `multi_platform_distribution.feature`

```gherkin
Feature: 多平台分發
  # 對應 PRD: Epic 1 - 內容管理與發佈 (US-003, US-004, US-005)
  # n8n 工作流負責將內容分發至各平台

  Background:
    Given n8n 工作流已正常運行
    And 各平台 API Token 已設定且有效

  @happy-path @smoke-test
  Scenario: 成功發佈至所有選定平台
    Given 我有一篇選擇 "fb, x, line" 的待發佈貼文
    When n8n 工作流執行發佈
    Then Facebook Page 應成功發文並回傳貼文 ID
    And X 應成功發文並回傳貼文 ID
    And LINE 應成功推送訊息
    And 貼文整體狀態應為 "success"
    And 每個平台的發佈紀錄應寫入 publish_logs

  @sad-path
  Scenario: 部分平台發佈失敗
    Given 我有一篇選擇 "fb, x, line" 的待發佈貼文
    And Facebook API Token 已過期
    When n8n 工作流執行發佈
    Then X 應成功發文
    And LINE 應成功推送
    But Facebook 應記錄失敗原因 "Token 過期"
    And 貼文整體狀態應為 "partial_success"

  @sad-path
  Scenario: 所有平台發佈失敗
    Given 我有一篇待發佈貼文
    And 所有平台 API 均無法連線
    When n8n 工作流執行發佈
    Then 所有平台應記錄失敗原因
    And 貼文整體狀態應為 "failed"
    And retry_count 應增加 1

  @happy-path
  Scenario: 單一平台手動補發
    Given 我有一篇狀態為 "partial_success" 的貼文
    And Facebook 發佈失敗，X 和 LINE 已成功
    When 我對 Facebook 執行手動補發
    Then 僅 Facebook 應重新發佈
    And X 和 LINE 不應重複發送
    And 補發成功後貼文狀態應更新為 "success"

  @edge-case
  Scenario: 防止重複發送至已成功的平台
    Given 我有一篇貼文已成功發佈至 X 並取得外部 post_id
    When n8n 工作流因重試再次執行
    Then X 平台應被跳過
    And 不應產生重複貼文

  @edge-case
  Scenario: 重試次數達上限
    Given 我有一篇貼文 retry_count 已達 3
    And 該貼文仍為 "failed" 狀態
    When n8n 工作流嘗試再次執行
    Then 該貼文應被跳過不再自動重試
    And 管理者應收到需人工處理的通知
```

---

## Feature 5: 發佈狀態追蹤

**檔案名稱**: `publish_status_tracking.feature`

```gherkin
Feature: 發佈狀態追蹤
  # 對應 PRD: Epic 1 - 內容管理與發佈 (US-004)
  # 對應 PRD: Epic 2 - 監控與互動追蹤 (US-006)

  Background:
    Given 使用者已登入內容分發平台

  @happy-path @smoke-test
  Scenario: 在 Web 介面查看發佈結果
    Given 我有一篇已觸發發佈的貼文
    When 發佈完成後我查看該貼文詳情
    Then 我應該看到每個平台的發佈狀態（成功或失敗）
    And 成功的平台應顯示外部貼文 ID
    And 失敗的平台應顯示錯誤原因

  @happy-path
  Scenario: 在監控儀表板查看所有貼文狀態總覽
    Given 我有多篇不同狀態的貼文
    When 我進入監控儀表板
    Then 我應該看到所有貼文的狀態列表
    And 可依狀態篩選（draft / queued / success / failed / partial_success）
    And 可依發佈時間排序

  @happy-path
  Scenario: 查看詳細發佈日誌
    Given 我有一篇已發佈的貼文
    When 我點擊查看發佈日誌
    Then 我應該看到 publish_logs 中的完整記錄
    And 包含每個平台的 API 回傳摘要
    And 包含 n8n workflow execution id

  @sad-path
  Scenario: 發佈過程中即時更新狀態
    Given 我有一篇正在發佈中的貼文
    When n8n 工作流逐一完成各平台發佈
    Then Web 介面應即時更新各平台狀態
    And 不需要手動重新整理頁面
```

---

## Feature 6: 監控儀表板

**檔案名稱**: `monitoring_dashboard.feature`

```gherkin
Feature: 監控儀表板
  # 對應 PRD: Epic 2 - 監控與互動追蹤 (US-006, US-007, US-008)
  # Web 儀表板集中顯示各平台互動數據與回覆

  Background:
    Given 使用者已登入內容分發平台
    And 我有至少一篇已成功發佈至多平台的貼文

  @happy-path @smoke-test
  Scenario: 查看各平台互動數據
    Given n8n 監控工作流已抓取最新互動數據
    When 我進入監控儀表板
    Then 我應該看到每篇貼文在各平台的按讚數
    And 我應該看到每篇貼文在各平台的留言數
    And 我應該看到每篇貼文在各平台的分享數
    And 數據應標示最後更新時間

  @happy-path
  Scenario: 查看各平台回覆內容
    Given 我的貼文在 Facebook 和 X 上有留言回覆
    When 我在儀表板查看該貼文的回覆
    Then 我應該看到來自 Facebook 的留言列表
    And 我應該看到來自 X 的留言列表
    And 每則留言應標示來源平台
    And 留言應依時間排序（最新在前）

  @happy-path
  Scenario: 篩選特定平台的互動數據
    Given 儀表板顯示所有平台的數據
    When 我選擇只查看 Facebook 的數據
    Then 只應顯示 Facebook 平台的互動數據與回覆

  @sad-path
  Scenario: 監控數據抓取失敗
    Given 某平台 API 暫時無法連線
    When n8n 監控工作流執行抓取
    Then 該平台的數據應顯示為 "暫時無法取得"
    And 其他平台的數據應正常顯示
    And 上次成功抓取的數據應保留顯示

  @edge-case
  Scenario: 尚無互動數據的新發佈貼文
    Given 我有一篇剛發佈的貼文
    And n8n 尚未執行第一次監控抓取
    When 我在儀表板查看該貼文
    Then 互動數據應顯示為 0 或 "尚未抓取"
    And 應顯示下次預計抓取時間
```

---

## Feature 7: 互動異常告警

**檔案名稱**: `interaction_alerts.feature`

```gherkin
Feature: 互動異常告警
  # 對應 PRD: Epic 2 - 監控與互動追蹤 (US-009)
  # 當貼文互動異常時通知管理者

  Background:
    Given 使用者已設定告警規則
    And n8n 監控工作流定時運行中

  @happy-path
  Scenario: 發佈失敗時發送告警通知
    Given 我有一篇貼文在某平台發佈失敗
    When n8n 工作流偵測到失敗
    Then 管理者應收到失敗通知（Email 或 LINE）
    And 通知應包含貼文標題、失敗平台與錯誤原因

  @happy-path
  Scenario: 貼文零互動告警
    Given 我有一篇貼文已發佈超過 24 小時
    And 所有平台的互動數據均為 0
    When n8n 監控工作流偵測到此狀況
    Then 管理者應收到零互動告警通知

  @sad-path
  Scenario: 告警通知發送失敗
    Given Email 服務暫時不可用
    When n8n 嘗試發送告警通知
    Then 應記錄通知發送失敗至日誌
    And 下次監控週期應重新嘗試發送

  @edge-case
  Scenario: 避免重複告警
    Given 同一篇貼文的同一個告警已發送過
    When n8n 監控工作流再次偵測到相同狀況
    Then 不應重複發送相同告警
```

---

## Feature 8: 狀態機轉換

**檔案名稱**: `status_transitions.feature`

```gherkin
Feature: 貼文狀態機轉換
  # 對應 PRD: 5.5 狀態機
  # 驗證所有合法的狀態轉換

  @happy-path
  Scenario: 完整正常發佈流程的狀態轉換
    Given 我建立一篇新貼文
    Then 貼文狀態應為 "draft"
    When 我設定排程並確認
    Then 貼文狀態應變為 "queued"
    When 排程時間到達且 n8n 開始處理
    Then 貼文狀態應變為 "publishing"
    When 所有平台發佈成功
    Then 貼文狀態應變為 "success"

  @sad-path
  Scenario: 部分失敗的狀態轉換
    Given 貼文狀態為 "publishing"
    When 部分平台成功、部分失敗
    Then 貼文狀態應變為 "partial_success"
    When 我對失敗平台執行補發且成功
    Then 貼文狀態應更新為 "success"

  @sad-path
  Scenario: 全部失敗後重試的狀態轉換
    Given 貼文狀態為 "publishing"
    When 所有平台均失敗
    Then 貼文狀態應變為 "failed"
    When 我手動觸發重試
    Then 貼文狀態應回到 "queued"

  @edge-case
  Scenario: 不合法的狀態轉換應被拒絕
    Given 貼文狀態為 "success"
    When 嘗試將狀態直接變更為 "draft"
    Then 系統應拒絕此操作
    And 我應看到錯誤訊息 "已成功發佈的貼文無法回到草稿狀態"
```

---

## Feature 9: 錯誤處理與重試

**檔案名稱**: `error_handling.feature`

```gherkin
Feature: 錯誤處理與重試
  # 對應 PRD: 5.6 錯誤處理策略
  # 驗證各類錯誤的處理行為

  Background:
    Given n8n 工作流已正常運行

  @happy-path
  Scenario: 暫時性錯誤自動重試成功
    Given 我有一篇待發佈貼文目標為 X
    And X API 回傳 503 暫時不可用
    When n8n 工作流執行第一次重試
    And X API 恢復正常
    Then X 應成功發文
    And retry_count 應記錄重試次數
    And 貼文狀態應為 "success"

  @sad-path
  Scenario: 設定錯誤不進行自動重試
    Given 我有一篇待發佈貼文目標為 Facebook
    And Facebook API 回傳 400 無效的 Token
    When n8n 工作流接收到此錯誤
    Then 不應自動重試
    And 錯誤原因應記錄至 publish_logs
    And 管理者應收到需檢查設定的通知

  @sad-path
  Scenario: 逾時錯誤處理
    Given 我有一篇待發佈貼文
    And 平台 API 回應逾時
    When n8n 工作流偵測到逾時
    Then 應依 retry_count 自動重試
    And 逾時資訊應記錄至 publish_logs

  @edge-case
  Scenario Outline: 不同 HTTP 狀態碼的處理策略
    Given 平台 API 回傳 HTTP <status_code>
    When n8n 工作流處理此回應
    Then 系統應執行 "<action>"

    Examples:
      | status_code | action           |
      | 200         | 記錄成功並寫回狀態    |
      | 400         | 記錄錯誤，停止重試    |
      | 401         | 記錄 Token 失效，通知管理者 |
      | 403         | 記錄權限不足，停止重試  |
      | 429         | 等待後自動重試       |
      | 500         | 自動重試最多 3 次    |
      | 503         | 自動重試最多 3 次    |
```

---

## 最佳實踐

1. **一個 Scenario 只測一件事**
2. **使用陳述式** -- `Then 我應該看到...` (非 `Then 系統顯示...`)
3. **避免 UI 細節** -- `When 我確認排程` (非 `When 我點擊綠色按鈕`)
4. **從使用者角度編寫** -- 非技術人員也能讀懂
5. **標籤分類** -- `@happy-path` / `@sad-path` / `@edge-case` / `@smoke-test` 便於分群執行
6. **Feature 對應 PRD** -- 每個 Feature 標註對應的 User Story 編號，確保需求可追溯
