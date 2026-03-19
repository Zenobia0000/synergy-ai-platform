# 程式碼審查與重構指南 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19

---

## 審查前檢查

- [ ] 程式碼可編譯無錯誤 (前端 `npm run build`、後端無 import error)
- [ ] 所有測試通過 (`vitest run` / `pytest`)
- [ ] 符合專案風格規範 (`eslint` / `ruff`)
- [ ] 文檔已更新（如 API 變更需更新 06_api_design）
- [ ] 已完成自我審查

---

## 審查重點

### 1. 程式碼品質

| 檢查項 | 標準 |
| :--- | :--- |
| 可讀性 | 命名清晰、邏輯容易理解 |
| 函式長度 | < 50 行 |
| 檔案長度 | < 800 行（典型 200-400 行） |
| 巢狀深度 | ≤ 4 層 |
| 不可變性 | 使用 spread operator / 不可變方法 |
| 無硬編碼值 | 可配置的值使用環境變數 |
| 錯誤處理 | 每層明確處理，不靜默吞噬 |

### 2. 前端專項

| 檢查項 | 標準 |
| :--- | :--- |
| TypeScript | 無 `any` 型別、無 `@ts-ignore` |
| React Hooks | 依賴陣列正確、無不必要的 re-render |
| shadcn/ui | 優先使用現有元件，避免重複造輪子 |
| API 呼叫 | 透過 React Query，不直接使用 fetch |
| 狀態管理 | 最小化全域狀態，優先使用 server state |

### 3. 後端專項

| 檢查項 | 標準 |
| :--- | :--- |
| Pydantic | 所有 API 輸入使用 Schema 驗證 |
| SQLAlchemy | 使用 async session，避免 N+1 查詢 |
| 錯誤回應 | 統一錯誤格式，不洩露內部細節 |
| 依賴注入 | 使用 FastAPI Depends |
| Alembic | 資料庫變更必須有 migration |

### 4. 安全檢查

- [ ] 無硬編碼秘密（API key、密碼、token）
- [ ] 所有使用者輸入已驗證（Pydantic / Zod）
- [ ] SQL 注入防護（SQLAlchemy ORM / 參數化查詢）
- [ ] Webhook 有簽名驗證
- [ ] 錯誤訊息不洩露敏感資料

---

## 重構時機

| 訊號 | 行動 |
| :--- | :--- |
| 函式超過 50 行 | Extract Method |
| 參數超過 4 個 | Introduce Parameter Object (Pydantic model) |
| 重複程式碼 > 3 處 | 提取共用函式 |
| 多重 if/switch | Replace Conditional with Strategy Pattern |
| 檔案超過 400 行 | 按功能拆分 |
| 元件 props > 5 個 | 拆分元件或使用 composition |

---

## 重構策略

| 策略 | 適用場景 | 範例 |
| :--- | :--- | :--- |
| Extract Method | 函式過長，有可複用邏輯 | 將發佈邏輯從 controller 提取到 service |
| Extract Variable | 條件表達式過複雜 | 命名布林條件 `is_publishable` |
| Replace Magic Number | 硬編碼數值 | `MAX_RETRY = 3` |
| Move to Service | Controller 含業務邏輯 | Router → Service → Repository |
| Extract Component | React 元件過大 | 拆分 ContentForm 的各個區塊 |
| Custom Hook | 多個元件共用邏輯 | `useContentMutation()` |

---

## PR 模板

```markdown
## 摘要
[變更簡述，關聯的 WBS 任務編號]

## 變更類型
- [ ] Bug 修復 (fix)
- [ ] 新功能 (feat)
- [ ] 重構 (refactor)
- [ ] 文檔更新 (docs)
- [ ] 測試 (test)

## 測試
- [ ] 單元測試通過
- [ ] 整合測試通過 (如涉及 API)
- [ ] 手動測試完成

## 檢查清單
- [ ] TypeScript / Python 無型別錯誤
- [ ] 無硬編碼秘密
- [ ] 無新增 console.log / print
- [ ] 自我審查完成
- [ ] 相關文檔已更新
```

---

## 品質關卡

### 合併前
- [ ] 自動化檢查全通過 (lint + test)
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 安全審查通過（無秘密洩露、輸入已驗證）

### 合併後
- [ ] 建置成功
- [ ] `/health` 端點正常回應
- [ ] 核心功能手動驗證
