# BDD 行為驅動情境 — Synergy AI Closer's Copilot

> **版本:** v1.0 | **更新:** 2026-04-24 | **對應 PRD:** `docs/01_prd.md`

---

## Feature 檔案索引

| # | 檔案 | 對應 Epic | User Stories |
| :---: | :--- | :--- | :--- |
| 1 | `questionnaire.feature` | Epic A：智能健康問卷 | US-A01、A02、A03 |
| 2 | `briefing.feature` | Epic B：商談前摘要 | US-B01、B02、B03 |
| 3 | `crm.feature` | Epic C：陽春版 CRM | US-C01、C02、C03 |
| 4 | `reminder.feature` | Epic D：自動跟進提醒 | US-D01、D02、D03 |

---

## 1. `questionnaire.feature`

```gherkin
Feature: 智能健康問卷
  # 對應 PRD: Epic A (US-A01, A02, A03)
  # 使用者：潛在客戶（填答者）+ 教練（接收名單）

  Background:
    Given 教練「阿明」已將問卷連結「https://app.synergy-ai.tw/q/abc123」傳給朋友「王小姐」
    And 問卷題目版本為「v1.0 健康基礎問卷」（20 題）

  @happy-path @smoke-test
  Scenario: 王小姐在手機完整填完問卷並收到個人摘要
    Given 王小姐在 iPhone 點開問卷連結
    When 她依序填答所有 20 題
    And 她按下「送出」
    Then 她應在 30 秒內看到「你的健康狀態摘要」頁面
    And 摘要應包含：健康等級（A/B/C）、3 點主要發現、隱私保護聲明
    And 摘要應提供「轉寄給朋友」按鈕

  @happy-path
  Scenario: 教練自動收到結構化名單通知
    Given 王小姐完成問卷送出
    When 系統完成 LLM 研判（≤ 30 秒）
    Then 教練「阿明」應收到 Email 或 LINE 通知：「王小姐完成問卷，可查看名單」
    And 教練打開後台應看到：
      | 欄位 | 內容範例 |
      | 姓名 | 王小姐 |
      | 健康等級 | B |
      | 紅旗警訊 | 家族糖尿病史、連續 6 週睡眠 < 6 小時 |
      | 推薦產品組合 | 產品A + 產品C |
      | 切入角度 | 從睡眠問題切入 |
    And CRM 中應自動出現「王小姐」這筆名單，狀態為「新名單」

  @happy-path
  Scenario: 填答者中途離開再接續填
    Given 王小姐填到第 10 題後關閉瀏覽器
    When 她 3 小時後重新點開同一個連結
    Then 她應看到「從第 10 題繼續」的選項
    And 前 10 題答案應保留

  @privacy
  Scenario: 填答者選擇不揭露敏感資訊
    Given 王小姐正在填答「過去一年是否有重大疾病史」
    When 她選擇「不方便透露」
    Then 她應能繼續填下一題
    And 送出後該欄位應標記為「未提供」而非空白
    And 教練端應看到「此項未提供」標示

  @sad-path
  Scenario: 問卷 token 無效或過期
    Given 連結 token「expired-xyz」已失效（> 30 天未使用）
    When 王小姐點開該連結
    Then 她應看到「此連結已失效，請向你的教練索取新連結」
    And 系統不應建立任何資料

  @sad-path
  Scenario: LLM 研判失敗時仍建檔
    Given 王小姐送出問卷
    When LLM API 呼叫失敗 3 次
    Then 名單應仍建立在 CRM 中
    And 該筆名單標記「AI 摘要生成失敗，請手動檢視答案」
    And 教練端可直接查看原始答案
    And 系統應記錄錯誤供 retry

  @edge-case
  Scenario Outline: 問卷計分邊界案例
    Given 王小姐在各風險項的答案為 "<risk_answers>"
    When 系統計算健康等級
    Then 她的健康等級應為 "<level>"

    Examples:
      | risk_answers                        | level |
      | 全部低風險                             | A     |
      | 睡眠差 + 飲食差                        | B     |
      | 家族病史 + 睡眠差 + BMI > 30           | C     |
      | 拒答 ≥ 5 題                          | 未分級  |
```

---

## 2. `briefing.feature`

```gherkin
Feature: 商談前摘要（AI Copilot 核心）
  # 對應 PRD: Epic B (US-B01, B02, B03)
  # 使用者：教練

  Background:
    Given 教練「阿明」已登入後台
    And 「王小姐」已完成問卷，CRM 中有她的資料
    And 狀態為「新名單」或「已商談」

  @happy-path @smoke-test @high-value
  Scenario: 教練在商談前 5 分鐘查看摘要
    Given 阿明與王小姐的商談約在下午 3 點
    When 阿明在下午 2:55 打開手機 App
    And 他點開「王小姐」的名單
    Then 他應在單一頁面看到：
      | 區塊 | 內容 |
      | 客戶痛點（3 句話） | 1. 連 6 週睡眠差<br>2. 家族糖尿病史<br>3. 上次減重失敗過 2 次 |
      | 推薦產品組合 | 產品A + 產品C（月費 ~3,500 NTD） |
      | 推薦理由 | 引用問卷答案第 7/12/18 題 |
      | 預期異議（≥ 2 項） | 「我朋友吃了沒效」、「太貴」 |
      | 異議回覆建議 | 1-2 句範例回覆 |
      | 切入角度 | 從睡眠問題切入 |
    And 頁面應在 3G 網路下 ≤ 2 秒載入完成

  @happy-path
  Scenario: 摘要標註產品推薦理由
    Given 系統推薦「產品A」給王小姐
    When 阿明點開推薦理由
    Then 他應看到引用原文：「王小姐在第 12 題回答『連續 6 週睡眠 < 6 小時』」
    And 他應看到關聯邏輯：「因此推薦含褪黑激素的產品A」

  @happy-path
  Scenario: 商談後教練更新狀態並回到摘要複查
    Given 阿明商談完畢後把王小姐狀態改為「已商談」
    When 他 3 天後重新開啟王小姐的摘要
    Then 他應看到：「上次商談：3 天前」
    And 摘要內容保持不變（不重新生成）

  @sad-path
  Scenario: 摘要生成時 LLM 服務中斷
    Given 阿明點開王小姐的名單
    When LLM API 回應失敗
    Then 系統應降級顯示：「AI 摘要暫時無法生成，以下為原始問卷答案」
    And 阿明應能看到問卷完整答案
    And 系統應於背景 retry 3 次，成功後推播 Email 通知

  @edge-case
  Scenario: 問卷答案不足以生成完整摘要
    Given 王小姐只填了 5 題就送出（部分必填跳過）
    When 系統嘗試生成摘要
    Then 摘要應標記「資料不足」區塊，只顯示能推論的項目
    And 系統應建議：「請引導客戶補填更多資訊」
```

---

## 3. `crm.feature`

```gherkin
Feature: 陽春版客戶管理（CRM）
  # 對應 PRD: Epic C (US-C01, C02, C03)
  # 使用者：教練

  Background:
    Given 教練「阿明」已登入後台
    And 他負責 50 位客戶名單

  @happy-path @smoke-test
  Scenario: 教練查看客戶清單並搜尋
    When 阿明進入 CRM 頁
    Then 他應看到表格含欄位：姓名、問卷日期、健康等級、狀態、最後聯繫、備註
    And 他應能用姓名關鍵字即時搜尋
    And 他應能用「狀態」篩選（新名單/已商談/已成交/未成交）

  @happy-path
  Scenario: 問卷填完自動建檔
    Given CRM 中目前有 50 筆名單
    When 一位新客戶「李先生」完成問卷
    Then CRM 中應自動新增第 51 筆「李先生」
    And 他的狀態應為「新名單」
    And 他的問卷日期應為今天
    And 阿明不需要手動輸入任何資料

  @happy-path
  Scenario: 教練更新客戶狀態並記錄時間
    Given 王小姐狀態為「新名單」
    When 阿明把狀態改為「已商談」
    Then 狀態應更新為「已商談」
    And 「最後聯繫」時間應自動記錄為現在
    And 系統應建立狀態變更歷程

  @happy-path
  Scenario: 教練在備註欄手動加註
    Given 王小姐的名單已存在
    When 阿明在備註欄寫「客戶希望下週再聯絡」
    Then 備註應儲存
    And 備註應標記時間戳

  @sad-path
  Scenario: 教練嘗試看別人的客戶
    Given 阿明的帳號只能看自己的 50 筆名單
    When 他嘗試直接存取其他教練「小美」的客戶 URL
    Then 系統應回傳 403 Forbidden
    And 應記錄未授權存取日誌

  @edge-case
  Scenario Outline: 狀態轉換規則
    Given 王小姐目前狀態為 "<from>"
    When 阿明嘗試把狀態改為 "<to>"
    Then 結果應為 "<result>"

    Examples:
      | from    | to      | result |
      | 新名單   | 已商談   | 允許    |
      | 已商談   | 已成交   | 允許    |
      | 已商談   | 未成交   | 允許    |
      | 已成交   | 已商談   | 拒絕（不可回退） |
      | 未成交   | 已商談   | 允許（可重新商談） |
```

---

## 4. `reminder.feature`

```gherkin
Feature: 自動跟進提醒
  # 對應 PRD: Epic D (US-D01, D02, D03)
  # 使用者：教練（被動接收）

  Background:
    Given 教練「阿明」已完成 LINE Official Account 綁定（line_user_id 已寫入 DB）
    And 教練「阿明」的 Email 也已設定（作為 LINE 失敗時的備援通道）
    And 排程器每小時檢查一次待發送提醒

  @happy-path @smoke-test
  Scenario: 商談後 48 小時透過 LINE 自動提醒
    Given 阿明於 2026-05-01 14:00 把王小姐狀態改為「已商談」
    When 時間到 2026-05-03 14:00（48 小時後）
    And 王小姐狀態仍為「已商談」（未成交也未標記未成交）
    Then 系統應透過 LINE Messaging API 推播給阿明
    And LINE 訊息應包含：
      | 欄位 | 內容 |
      | 開頭 | [Synergy AI] 記得跟進：王小姐 |
      | 正文 | 王小姐在 2 天前商談，狀態未更新，可考慮再聯絡 |
      | 按鈕 | 「打開摘要」深連結到王小姐的商談摘要頁 |
    And reminders.channel 應為 "line"

  @happy-path @fallback
  Scenario: LINE API 失敗時自動降級 Email
    Given 阿明已綁定 LINE 但 LINE Messaging API 回應 500
    When 提醒到期觸發發送
    Then 系統應嘗試 LINE 一次
    And 失敗後應立即改走 Resend Email 發送
    And reminders.channel 應為 "email"
    And reminders.channel_attempts 應記錄兩次嘗試（line failed, email sent）

  @happy-path @fallback
  Scenario: 教練未綁定 LINE 時直接走 Email
    Given 教練「阿美」從未綁定 LINE（line_user_id 為 null）
    When 阿美的客戶提醒到期
    Then 系統應略過 LINE 嘗試
    And 應直接透過 Resend Email 發送
    And reminders.channel 應為 "email"

  @happy-path
  Scenario: 三段提醒時程（48h / 7d / 30d）
    Given 阿明於 2026-05-01 把王小姐狀態改為「已商談」
    When 時間推進到各個時點
    Then 提醒應按以下時程送達：
      | 時點 | 提醒類型 |
      | 2026-05-03（48h） | 短期跟進 |
      | 2026-05-08（7d） | 週關懷 |
      | 2026-05-31（30d） | 月關心 |

  @happy-path
  Scenario: 標記已成交後停止提醒
    Given 阿明已排程了王小姐的 7d 與 30d 提醒
    When 阿明在第 3 天把狀態改為「已成交」
    Then 7d 與 30d 的未發送提醒應自動取消
    And 系統應記錄取消原因：「狀態轉為已成交」

  @happy-path
  Scenario: 標記未成交後仍保留提醒
    Given 阿明把王小姐狀態改為「未成交」
    When 時間到 7d / 30d
    Then 提醒仍應發送（未成交名單需要再啟動）
    And 提醒主旨改為「再嘗試聯絡：王小姐」

  @sad-path
  Scenario: Email 發送失敗
    Given 排程器到達 48h 提醒時點
    When Resend API 回應 5xx 錯誤
    Then 系統應 retry 3 次（間隔 5 / 30 / 180 分鐘）
    And 3 次都失敗則記錄到 error log
    And 不應阻塞其他提醒發送

  @edge-case
  Scenario: 時區處理
    Given 阿明的時區為 Asia/Taipei
    When 排程器在 UTC 時間運行
    Then 48h 計算應用阿明的時區
    And 提醒發送時間點應落在阿明工作時間（9:00-21:00 Asia/Taipei）內
    And 非工作時間應延到下一個工作時段開始

  @edge-case
  Scenario: 重複觸發保護
    Given 48h 提醒已於 2026-05-03 14:00 成功發送
    When 排程器在 2026-05-03 15:00 再次掃描
    Then 不應再發送同一筆 48h 提醒
    And 系統應查檢 reminder_log 避免重複
```

---

## 測試執行指引

### 工具鏈
- **後端**：`pytest` + `pytest-bdd`（Python 3.12）
- **前端**：`Playwright` + `@cucumber/cucumber`（Node.js）
- **Feature 檔位置**：`tests/features/*.feature`
- **Step 定義位置**：`tests/steps/`

### 覆蓋率要求
- Happy path：100%（`@smoke-test` 標籤必跑）
- Sad path：≥ 80%
- Edge case：依風險優先級

### 執行指令
```bash
# 後端 BDD（FastAPI）
cd apps/api && uv run pytest tests/features/ -v --tags=@smoke-test

# 前端 BDD（Next.js）
cd apps/web && npx cucumber-js --tags=@smoke-test
```

### CI 整合
每個 PR 至少跑 `@smoke-test` 與 `@happy-path`。`@sad-path` 與 `@edge-case` 在夜間跑全量。
