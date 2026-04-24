# 模組規格與測試案例 — Synergy AI Closer's Copilot

> **版本:** v1.0 | **更新:** 2026-04-24 | **狀態:** 草稿
> **對應架構**：`docs/04_architecture.md` | **對應 BDD**：`docs/02_bdd.md` | **對應 API**：`docs/05_api.md`

---

## 模組索引

| # | 模組 | 所屬層級 | 核心 API | BDD Feature |
| :---: | :--- | :--- | :--- | :--- |
| 1 | QuestionnaireService | Application | `/questionnaires/*` | `questionnaire.feature` |
| 2 | ScoringEngine | Domain | (內部) | 內嵌 `questionnaire.feature` |
| 3 | BriefingService | Application | `/leads/{id}/briefing` | `briefing.feature` |
| 4 | LLMAdapter | Infrastructure | (內部) | — |
| 5 | LeadService (CRM) | Application | `/leads/*` | `crm.feature` |
| 6 | LeadStatusMachine | Domain | (內部) | 內嵌 `crm.feature` |
| 7 | ReminderService | Application | `/reminders/*` | `reminder.feature` |
| 8 | ReminderScheduler | Infrastructure | `/internal/reminders/scan` | `reminder.feature` |
| 9 | NotificationChannel 實作群<br>（LineMessagingChannel 主 + ResendEmailChannel 備援）| Infrastructure | (內部) | — |

---

## 1. QuestionnaireService

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Application |
| **核心職責** | 編排問卷填答流程：題目載入、中途儲存、送出、觸發計分與 Lead 建立 |
| **依賴** | `ScoringEngine`、`LeadService`、Supabase Client |
| **被依賴** | FastAPI Router (`/questionnaires/*`) |

### 效能邊界

| 指標 | 目標 | 測量 |
| :--- | :--- | :--- |
| `GET /questionnaires/{token}` p95 | < 300ms | APM |
| `POST /submit` p95（不含 LLM） | < 500ms | APM |
| 同時填答者上限 | 50 人 | 負載測試 |
| Token TTL | 30 天 | DB constraint |

### 關鍵函式

#### `async def start_session(token: UUID) -> QuestionnaireSession`

- **前置**：token 格式正確、DB 有對應 questionnaire record、未過期
- **後置**：回傳題目 + 現有答案進度
- **錯誤**：
  | 情境 | 例外 | HTTP |
  | :--- | :--- | :--- |
  | Token 不存在 | `TokenNotFoundError` | 404 |
  | Token 過期（> 30 天） | `TokenExpiredError` | 410 |

#### `async def save_answers(token: UUID, answers: list[AnswerInput]) -> SaveResult`

- **前置**：token 有效、每題 `question_key` 在 template 中存在
- **後置**：UPSERT answers；若 question_key 重複只保留最新
- **不變性**：`is_redacted=True` 時 `value` 必為 null

#### `async def submit(token: UUID, prospect: ProspectInput, idempotency_key: str | None) -> SubmitResult`

- **前置**：token 有效、必填題已答（或標 `is_redacted`）
- **後置**：
  1. `questionnaires.submitted_at` = now
  2. 呼叫 `ScoringEngine.score(answers)` 取得 health_level + red_flags
  3. `LeadService.create_from_questionnaire(...)` 建立 Lead
  4. 背景任務觸發 `BriefingService.generate(lead_id)`
  5. 回傳 public summary（給填答者看）
- **冪等**：同 idempotency_key 在 24h 內回快取

---

## 2. ScoringEngine（Domain）

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Domain（純函式、無 IO） |
| **核心職責** | 依規則 YAML 計算健康等級與紅旗警訊 |
| **依賴** | 規則定義（`rules/questionnaire-v1.yaml`） |
| **被依賴** | `QuestionnaireService` |

### 規則檔格式（`rules/questionnaire-v1.yaml`）

```yaml
version: "1.0"
rules:
  - id: sleep_risk
    when:
      question_key: sleep_hours
      equals: ["< 4 小時", "4-6 小時"]
    effect:
      add_score: 2
      red_flag: "睡眠品質偏低"

  - id: family_diabetes
    when:
      question_key: family_disease
      contains: "糖尿病"
    effect:
      add_score: 3
      red_flag: "家族糖尿病史"

health_levels:
  A: { max_score: 2 }
  B: { max_score: 5 }
  C: { min_score: 6 }
```

### 關鍵函式

#### `def score(answers: list[Answer], rules: RuleSet) -> ScoringResult`

- **前置**：rules 為有效 YAML 解析結果
- **後置**：回傳 `ScoringResult(level: HealthLevel, total_score: int, red_flags: list[str])`
- **不變性**：
  - 若 `answers` 中 `is_redacted=True` 的題目 ≥ 5 題 → level = "未分級"
  - total_score = Σ(符合規則的 add_score)
- **純函式**：無 side effect，同樣 input 必得同樣 output

---

## 3. BriefingService

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Application |
| **核心職責** | 呼叫 LLM 生成商談摘要、驗證結構、寫入 DB、管理重新生成 |
| **依賴** | `LLMAdapter`、Supabase Client、`LeadService`（讀 lead） |
| **被依賴** | FastAPI Router、`QuestionnaireService`（問卷送出觸發） |

### 效能邊界

| 指標 | 目標 | 測量 |
| :--- | :--- | :--- |
| `generate()` 總延遲 | < 30s | 埋點 |
| LLM token 上限 | 2,500 output tokens | Gemini config |
| 重生成 rate limit | 3/hr/lead | Redis or DB counter |

### 關鍵函式

#### `async def generate(lead_id: UUID, force: bool = False) -> Briefing`

- **前置**：
  - Lead 存在
  - 該 Lead 的 Questionnaire 已 submitted
  - `force=False` 時若已有 `briefings.lead_id` 則直接回傳快取（ADR-009）
- **後置**：
  1. 組裝 prompt（用問卷答案 + health_level + red_flags）
  2. 呼叫 `LLMAdapter.complete()`，輸出 JSON
  3. Pydantic 驗證 `BriefingContent` schema
  4. 失敗重試 2 次（指數退避）
  5. UPSERT `briefings`（`lead_id UNIQUE`）
  6. 回傳 Briefing
- **錯誤**：
  | 情境 | 例外 | HTTP |
  | :--- | :--- | :--- |
  | Lead 不存在 | `LeadNotFoundError` | 404 |
  | Questionnaire 未送出 | `QuestionnaireNotSubmittedError` | 422 |
  | LLM 重試後仍失敗 | `LLMGenerationFailedError` | 503 |
  | 結構化輸出驗證失敗 | 內部 retry；若 2 次都失敗 raise `LLMGenerationFailedError` | 503 |

#### `async def regenerate(lead_id: UUID, coach_id: UUID) -> Briefing`

- **前置**：coach 擁有該 lead；1 小時內 regenerate 次數 < 3
- **後置**：強制 force=True 呼叫 generate

---

## 4. LLMAdapter（Infrastructure）

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Infrastructure |
| **核心職責** | 抽象化 LLM 供應商（ADR-004），提供統一介面 |
| **依賴** | `litellm`、Gemini/Claude API Key |
| **被依賴** | `BriefingService`、未來其他 LLM 呼叫者 |

### 介面

```python
from abc import ABC, abstractmethod

class LLMAdapter(ABC):
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        response_format: Literal["text", "json_object"] = "text",
        max_tokens: int = 2500,
        temperature: float = 0.3,
    ) -> LLMResponse: ...

class LiteLLMAdapter(LLMAdapter):
    """預設實作。model=None 時用 settings.default_llm_model"""
```

### 關鍵函式

#### `async def complete(...) -> LLMResponse`

- **前置**：prompt 非空、`max_tokens ≤ 4000`
- **後置**：
  - `LLMResponse.content`: str
  - `LLMResponse.model`: 實際使用 model（`gemini/gemini-2.5-flash` or `claude-3-5-sonnet`）
  - `LLMResponse.tokens_in` / `tokens_out`
  - `LLMResponse.latency_ms`
- **錯誤**：
  - 5xx → 重試 3 次（1s / 5s / 30s）
  - 4xx → 不重試，raise `LLMClientError`
  - Timeout 60s → raise `LLMTimeoutError`

### Prompt 模板管理

- 位置：`packages/llm/prompts/<use_case>-v<version>.py`
- 版本化：prompt 改動 bump version，生成時記錄 model + prompt_version 到 `briefings`

---

## 5. LeadService (CRM)

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Application |
| **核心職責** | Lead CRUD、狀態機、搜尋篩選 |
| **依賴** | `LeadStatusMachine`、`ReminderService`（狀態變更觸發）、Supabase |
| **被依賴** | FastAPI Router、`QuestionnaireService` |

### 關鍵函式

#### `async def create_from_questionnaire(questionnaire_id, coach_id, prospect, scoring) -> Lead`

- **前置**：問卷存在、coach 有效
- **後置**：建立 Lead 記錄，狀態 = `new`
- **不變性**：每份 Questionnaire 最多一個 Lead

#### `async def list(coach_id, filters, pagination) -> PaginatedLeads`

- **前置**：coach 已登入
- **後置**：僅回傳該 coach 的 leads（RLS 強制）

#### `async def update_status(lead_id, new_status, coach_id) -> Lead`

- **前置**：coach 擁有 lead、狀態轉換合法（`LeadStatusMachine.can_transition`）
- **後置**：
  1. UPDATE leads.status、last_contact_at = now
  2. INSERT status_changes 記錄
  3. 若 new_status = `talked` → `ReminderService.schedule_all(lead_id)`
  4. 若 new_status = `closed_won` → `ReminderService.cancel_pending(lead_id)`
- **錯誤**：
  | 情境 | 例外 | HTTP |
  | :--- | :--- | :--- |
  | 非法轉換 | `InvalidStatusTransitionError` | 422 |
  | 非本人 lead | `PermissionDeniedError` | 403 |

---

## 6. LeadStatusMachine（Domain）

### 狀態圖

```
new ──→ talked ──→ closed_won (終態)
          │   ↖──── closed_lost
          │          │
          └────→ closed_lost ──→ talked （可再商談）
```

### 轉換矩陣

| From \ To | new | talked | closed_won | closed_lost |
| :--- | :---: | :---: | :---: | :---: |
| **new** | — | ✅ | ❌ | ✅ |
| **talked** | ❌ | ✅（多次商談） | ✅ | ✅ |
| **closed_won** | ❌ | ❌ | — | ❌ |
| **closed_lost** | ❌ | ✅ | ✅ | — |

### 關鍵函式

#### `def can_transition(from: LeadStatus, to: LeadStatus) -> bool`

純函式，查轉換矩陣。

---

## 7. ReminderService

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Application |
| **核心職責** | 建立、取消、查詢提醒 |
| **依賴** | Supabase |
| **被依賴** | `LeadService`、`ReminderScheduler` |

### 關鍵函式

#### `async def schedule_all(lead_id: UUID) -> list[Reminder]`

- **前置**：Lead 存在、狀態為 `talked`
- **後置**：建立三筆 reminders
  - `kind=48h`, `due_at = now + 48h`
  - `kind=7d`, `due_at = now + 7d`
  - `kind=30d`, `due_at = now + 30d`
  - 三筆 status = `pending`
- **冪等**：若該 lead 已有同 kind 的 pending reminder，跳過

#### `async def cancel_pending(lead_id: UUID) -> int`

- **後置**：UPDATE reminders SET status='cancelled' WHERE lead_id=? AND status='pending'
- 回傳取消筆數

#### `async def send(reminder_id: UUID) -> ReminderSendResult`

- **前置**：reminder 狀態為 `pending`、到期
- **後置（含 LINE 優先 + Email 降級路由）**：
  1. 組裝通知內容（含 lead 姓名與商談連結）
  2. 查詢 coach 是否有 `line_user_id`
  3. **若已綁定 LINE** → 呼叫 `LineMessagingChannel.send()`
     - 成功：記錄 channel='line'、UPDATE status='sent'
     - 失敗（LINE API 錯誤、被封鎖）→ 記錄 attempt，**降級走 Email**
  4. **LINE 未綁定或降級觸發** → 呼叫 `ResendEmailChannel.send()`
     - 成功：channel='email'、status='sent'
     - 失敗：retry 3 次（5/30/180 min），都失敗則 status='failed'
  5. 每次 channel 嘗試寫入 `reminders.channel_attempts` jsonb 陣列
- **錯誤**：最終兩通道都失敗才 status='failed'；記錄完整 attempts 供追查

---

## 8. ReminderScheduler（Infrastructure）

| 項目 | 內容 |
| :--- | :--- |
| **所屬層級** | Infrastructure |
| **核心職責** | APScheduler 每小時掃描到期提醒，呼叫 `ReminderService.send` |
| **依賴** | APScheduler、`ReminderService` |

### 配置

```python
scheduler.add_job(
    scan_and_send,
    trigger="cron",
    minute=0,  # 每小時整點
    id="reminder_scan",
    max_instances=1,  # 避免重入
    misfire_grace_time=600,
)
```

### 關鍵函式

#### `async def scan_and_send() -> ScanResult`

- SELECT reminders WHERE status='pending' AND due_at <= now() LIMIT 100
- 對每筆呼叫 `ReminderService.send`
- 回傳 `{scanned, sent, failed}`
- **時區處理**：
  - 所有時間戳 UTC 儲存
  - 發送時檢查 coach 時區的 9:00-21:00
  - 落在時區外 → 延到下次工作時段（DB UPDATE due_at）

---

## 9. NotificationChannel 實作群（Infrastructure）

通道抽象 + LINE（主）+ Email（備援）兩個 adapter。MVP 必同時實作，`ReminderService.send` 做 fallback 路由。

```python
from typing import Protocol, Literal

SendStatus = Literal["sent", "failed_retryable", "failed_permanent"]

class NotificationChannel(Protocol):
    channel_name: Literal["line", "email"]

    async def send(
        self,
        *,
        recipient: ChannelRecipient,  # line_user_id 或 email
        subject: str | None,           # email 用；LINE 可忽略
        body: str,
        deep_link: str,
    ) -> SendResult: ...

class LineMessagingChannel(NotificationChannel):
    """MVP 主通道。使用 line-bot-sdk，pushMessage API。
    - 失敗類型：user_not_bound / rate_limited / api_error / blocked
    - rate_limited / api_error → failed_retryable（觸發降級 Email）
    - blocked / user_not_bound → failed_permanent（直接降級）
    """

class ResendEmailChannel(NotificationChannel):
    """MVP 備援通道。LINE 無法送達時使用。
    - 也是未綁定 LINE 的教練唯一通道。
    """
```

### LINE 綁定管理（新增職責）

#### `async def handle_line_webhook(event: LineEvent) -> None`

- **事件 `follow`**：
  1. 回傳 welcome 訊息含綁定引導
  2. 若能從 deep link 識別 coach_id，直接寫入 `coaches.line_user_id`
- **事件 `unfollow`**：UPDATE coaches SET line_user_id=NULL；後續提醒自動走 Email

#### `async def bind_line(coach_id: UUID, line_bind_token: str) -> Coach`

- 驗證 token（短期有效、單次使用）
- UPDATE coaches SET line_user_id

### 測試補充

```python
async def test_reminder_sends_line_when_bound(db, line_mock, email_mock):
    lead = await create_lead_with_reminder(db, coach_line_bound=True)
    await reminder_service.send(reminder_id=...)
    assert line_mock.sent_count == 1
    assert email_mock.sent_count == 0

async def test_reminder_fallbacks_to_email_when_line_fails(db, line_mock, email_mock):
    line_mock.fail_with = "api_error"
    lead = await create_lead_with_reminder(db, coach_line_bound=True)
    await reminder_service.send(reminder_id=...)
    assert line_mock.sent_count == 1  # 嘗試過
    assert email_mock.sent_count == 1  # 降級成功

async def test_reminder_uses_email_directly_when_not_bound(db, line_mock, email_mock):
    lead = await create_lead_with_reminder(db, coach_line_bound=False)
    await reminder_service.send(reminder_id=...)
    assert line_mock.sent_count == 0  # 不嘗試 LINE
    assert email_mock.sent_count == 1
```

---

## 測試策略

### 覆蓋率目標

| 類型 | 目標 | 重點 |
| :--- | :--- | :--- |
| 單元測試 | 80%+ | Domain 層 100%（純函式易測） |
| 整合測試 | 關鍵路徑 100% | DB + LLM mock |
| BDD (`@smoke-test`) | 必跑 | CI 門檻 |

### 測試範例

#### TC-Q001: `ScoringEngine` — 家族病史觸發紅旗

```python
def test_scoring_family_disease_triggers_red_flag():
    answers = [
        Answer(key="sleep_hours", value="6-8 小時"),
        Answer(key="family_disease", value="糖尿病"),
    ]
    rules = load_rules("questionnaire-v1.yaml")
    result = score(answers, rules)
    assert result.level == HealthLevel.B
    assert "家族糖尿病史" in result.red_flags
```

#### TC-Q002: `ScoringEngine` — 5 題以上拒答 → 未分級

```python
def test_scoring_too_many_redacted_returns_ungraded():
    answers = [Answer(key=f"q{i}", value=None, is_redacted=True) for i in range(5)]
    result = score(answers, rules)
    assert result.level == HealthLevel.UNGRADED
```

#### TC-B001: `BriefingService` — LLM 失敗後 retry 成功

```python
async def test_briefing_llm_retry(monkeypatch):
    mock_llm = AsyncMock()
    mock_llm.complete.side_effect = [LLMTimeoutError(), LLMTimeoutError(), VALID_RESPONSE]
    monkeypatch.setattr("packages.llm.adapter", mock_llm)

    briefing = await briefing_service.generate(lead_id="lead_1")
    assert briefing.content is not None
    assert mock_llm.complete.call_count == 3
```

#### TC-L001: `LeadStatusMachine` — 拒絕成交後回退

```python
def test_cannot_transition_from_closed_won():
    assert not can_transition(LeadStatus.CLOSED_WON, LeadStatus.TALKED)
    assert not can_transition(LeadStatus.CLOSED_WON, LeadStatus.NEW)
```

#### TC-R001: `ReminderService` — 成交後取消所有 pending

```python
async def test_closed_won_cancels_reminders(db_session):
    lead = await create_lead_with_reminders(db_session)
    assert count_pending(lead.id) == 3

    await lead_service.update_status(lead.id, LeadStatus.CLOSED_WON, coach_id=...)

    assert count_pending(lead.id) == 0
    assert count_cancelled(lead.id) == 3
```

#### TC-S001: `ReminderScheduler` — 冪等性

```python
async def test_scheduler_idempotent(db_session):
    await create_due_reminder(db_session)

    result1 = await scheduler.scan_and_send()
    result2 = await scheduler.scan_and_send()

    assert result1.sent == 1
    assert result2.sent == 0  # 第二次不應重送
```

### 測試結構

```
apps/api/tests/
├── unit/
│   ├── domain/
│   │   ├── test_scoring_engine.py
│   │   └── test_lead_status_machine.py
│   └── application/
│       ├── test_briefing_service.py
│       └── test_reminder_service.py
├── integration/
│   ├── test_questionnaire_flow.py
│   └── test_reminder_scheduler.py
└── features/  # BDD
    ├── questionnaire.feature
    ├── briefing.feature
    ├── crm.feature
    └── reminder.feature
```

### CI 門檻

```bash
uv run pytest apps/api/tests/ \
    --cov=apps/api/src \
    --cov-report=term-missing \
    --cov-fail-under=80
```

未達 80% 阻擋 merge。
