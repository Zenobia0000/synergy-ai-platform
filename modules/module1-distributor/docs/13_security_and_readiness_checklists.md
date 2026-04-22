# 安全與生產準備檢查清單 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19 | **審查人員:** kuanwei

---

## A. 核心安全原則

- [ ] **最小權限**: API 端點僅暴露必要資料
- [ ] **縱深防禦**: 前端驗證 + 後端驗證 + 資料庫約束
- [ ] **預設安全**: CORS 限定來源、Webhook 需簽名驗證
- [ ] **攻擊面最小化**: 關閉不必要的端點和除錯資訊

---

## B. 資料安全

### 資料分類

| 分類 | 資料項目 | 保護措施 |
| :--- | :--- | :--- |
| **機密** | 各平台 API Token/Secret、DB 密碼、JWT Secret | `.env` 不進 Git、環境變數注入 |
| **內部** | n8n Webhook Secret、排程配置 | `.env` 管理 |
| **公開** | 貼文內容、發佈狀態 | 正常存取控制 |

### 傳輸安全

- [ ] 生產環境使用 HTTPS (TLS 1.2+)
- [ ] 開發環境 localhost 通訊可接受 HTTP
- [ ] n8n ↔ FastAPI Webhook 通訊使用簽名驗證

### 儲存安全

- [ ] 敏感配置使用環境變數（`.env`），不硬編碼
- [ ] `.env` 已加入 `.gitignore`
- [ ] `.env.example` 只包含鍵名，無實際值
- [ ] 資料庫連線字串使用環境變數

---

## C. 應用程式安全

### 認證 (MVP 預留)

- [ ] FastAPI middleware 架構支援後續插入 JWT 認證
- [ ] `python-jose` 和 `passlib` 已在 requirements.txt
- [ ] `SECRET_KEY` 和 `ACCESS_TOKEN_EXPIRE_MINUTES` 已配置
- [ ] MVP 階段: 本地使用，暫不啟用認證

### 輸入驗證

- [ ] 前端: Zod schema 驗證表單輸入
- [ ] 後端: Pydantic schema 驗證 API 請求
- [ ] `platforms` 欄位使用 regex pattern 驗證 (`^(fb|ig|x|line)(,(fb|ig|x|line))*$`)
- [ ] `title` 限制長度 (`max_length=255`)
- [ ] `publish_at` 驗證為有效時間戳

### 注入防護

- [ ] SQL 注入: 使用 SQLAlchemy ORM（參數化查詢）
- [ ] XSS: React 自動跳脫 + 不使用 `dangerouslySetInnerHTML`
- [ ] 命令注入: 不從使用者輸入組合系統命令

### API 安全

- [ ] Webhook 端點驗證 `N8N_WEBHOOK_SECRET` 簽名
- [ ] CORS 限定允許來源 (`http://localhost:5173`)
- [ ] API 回應不包含內部錯誤堆疊
- [ ] 分頁查詢限制 `limit` 最大值（防止大量資料洩露）

### 依賴安全

- [ ] 前端: 定期 `npm audit`
- [ ] 後端: 定期 `pip-audit` 或 `safety check`
- [ ] 鎖定依賴版本（`package-lock.json` / `requirements.txt` 指定版本）

---

## D. n8n 安全

- [ ] n8n 管理介面設定密碼保護
- [ ] n8n 不暴露於公網
- [ ] Workflow 中的 API Token 使用 n8n Credentials 管理
- [ ] Webhook URL 使用不可猜測的路徑

---

## E. 每次 Commit 前安全檢查

- [ ] 無硬編碼秘密（API key、密碼、token）
- [ ] 所有使用者輸入已驗證
- [ ] SQL 注入防護確認
- [ ] 錯誤訊息不洩露敏感資料
- [ ] `.env` 未被追蹤

---

## F. 審查結論

| # | 行動項 | 優先級 | 預計完成 | 狀態 |
| :--- | :--- | :--- | :--- | :--- |
| 1 | 設定 Webhook 簽名驗證 | P0 | Phase 2 | ⏳ 待處理 |
| 2 | 實作 API 分頁限制 | P0 | Phase 2 | ⏳ 待處理 |
| 3 | 設定 n8n 管理介面密碼 | P0 | Phase 1 | ⏳ 待處理 |
| 4 | 實作 JWT 認證 | P2 | Phase 5 | ⏳ 待處理 |
| 5 | 設定 npm audit CI 檢查 | P1 | Phase 3 | ⏳ 待處理 |

**整體評估:** MVP 階段在本地使用安全風險可控，上線前須完成 P0 項目

---

## G. 生產準備就緒 (MVP 上線前)

### 可觀測性

- [ ] `/health` 端點可用
- [ ] 後端結構化日誌 (uvicorn 預設)
- [ ] 前端錯誤邊界捕獲未處理異常
- [ ] 發佈失敗告警通知 (n8n → Email/LINE)

### 可靠性

- [ ] FastAPI 優雅停機 (uvicorn signal handling)
- [ ] n8n Webhook 呼叫有超時設定
- [ ] 發佈失敗自動重試 (1-3 次，指數退避)
- [ ] 已成功平台不重複發送（冪等性）
- [ ] PostgreSQL 資料定期備份

### 效能

- [ ] API 回應 < 500ms
- [ ] 前端頁面載入 < 2s
- [ ] 資料庫查詢有適當索引
- [ ] React Query 快取減少重複請求

### 可維護性

- [ ] Alembic migration 管理資料庫變更
- [ ] n8n Workflow 匯出至 `n8n/` 目錄 (版本控制)
- [ ] `.env.example` 記錄所有需要的環境變數
- [ ] 文檔與程式碼同步更新
