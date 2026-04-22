# 文檔與維護指南 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19

---

## 1. 文檔類型

| 類型 | 內容 | 格式 | 位置 |
| :--- | :--- | :--- | :--- |
| **專案文檔** | PRD、架構設計、ADR、BDD 場景 | Markdown | `docs/` |
| **API 文檔** | OpenAPI 規範、端點說明 | 自動產生 (FastAPI) | `/api/v1/docs` |
| **WBS 追蹤** | 任務分解、進度追蹤 | Markdown + JSON | `.claude/taskmaster-data/` |
| **開發者文檔** | 環境設置、專案規則 | Markdown | `CLAUDE.md`, `README.md` |
| **Workflow 文檔** | n8n 工作流說明 | Markdown + JSON | `n8n/` |

---

## 2. 文檔結構

```
docs/
├── 01_workflow_manual.md                  # 開發流程使用手冊
├── 02_project_brief_and_prd.md            # PRD 需求文件
├── 03_behavior_driven_development_guide.md # BDD 驗收場景
├── 04_architecture_decision_record.md     # 架構決策記錄
├── 05_architecture_and_design_document.md # 架構設計文件
├── 06_api_design_specification.md         # API 設計規範
├── 07_module_specification_and_tests.md   # 模組規格與測試
├── 08_project_structure_guide.md          # 專案結構指南
├── 09_file_dependencies.md               # 檔案依賴關係
├── 10_class_relationships.md              # 類別關係設計
├── 11_code_review_and_refactoring_guide.md # Code Review 指南
├── 12_frontend_architecture_specification.md # 前端架構規範
├── 13_security_and_readiness_checklists.md   # 安全與上線準備
├── 14_deployment_and_operations_guide.md     # 部署與運維
├── 15_documentation_and_maintenance_guide.md # 文檔維護 (本文)
├── 16_wbs_development_plan.md                # WBS 開發計畫
└── 17_frontend_information_architecture.md   # 前端資訊架構
```

---

## 3. 撰寫規範

- **簡潔明瞭**: 直接切入重點，避免冗長描述
- **主動語態**: 「建立資料庫」而非「資料庫應被建立」
- **包含範例**: 程式碼範例使用實際專案的程式碼
- **保持一致**: 文檔編號與 VibeCoding 模板對應
- **版本標記**: 每份文檔標注版本、更新日期、狀態

### 命名規範

| 類型 | 格式 | 範例 |
| :--- | :--- | :--- |
| 文檔檔名 | `{編號}_{描述}.md` | `04_architecture_decision_record.md` |
| ADR 標題 | `ADR-{序號}: {決策標題}` | `ADR-001: 前端框架選型` |
| 圖表 | Mermaid 語法嵌入 Markdown | `graph TB`, `sequenceDiagram` |

---

## 4. 文檔與程式碼同步

### 何時更新文檔

| 變更類型 | 需更新的文檔 |
| :--- | :--- |
| 新增 API 端點 | `06_api_design_specification.md` |
| 資料模型變更 | `05_architecture`, `09_file_dependencies`, `10_class_relationships` |
| 新的技術決策 | `04_architecture_decision_record.md` (新增 ADR) |
| 目錄結構調整 | `08_project_structure_guide.md` |
| 前端頁面新增 | `12_frontend_architecture`, `17_frontend_information_architecture` |
| 安全相關變更 | `13_security_and_readiness_checklists.md` |
| 部署方式變更 | `14_deployment_and_operations_guide.md` |
| WBS 任務完成 | `.claude/taskmaster-data/wbs.md`, `16_wbs_development_plan.md` |

### 自動產生的文檔

| 文檔 | 工具 | 說明 |
| :--- | :--- | :--- |
| API 文檔 | FastAPI 自動產生 | `/api/v1/docs` (Swagger UI) |
| API Schema | FastAPI 自動產生 | `/api/v1/openapi.json` |

---

## 5. 維護排程

### 每個 Phase 結束時

- [ ] 審查相關文檔是否與實際程式碼一致
- [ ] 更新 WBS 任務狀態
- [ ] 確認 ADR 是否有新的技術決策需記錄
- [ ] 更新 `CLAUDE.md` 如有新的規則或約束

### MVP 上線前

- [ ] 全面文檔稽核：所有 17 份文檔與實際狀態一致
- [ ] API 文檔與實際端點一致 (OpenAPI spec)
- [ ] 部署指南可復現 (14_deployment)
- [ ] 安全檢查清單全部勾選 (13_security)

---

## 6. CHANGELOG 模板

```markdown
# 變更記錄

## [Unreleased]
### 新增
### 變更
### 修復

## [0.1.0] - 2026-03-19
### 新增
- 專案初始化
- FastAPI 後端骨架
- 前端 Vite + React 模板
- 完整文檔集 (17 份)
- WBS 任務清單
```

---

## 7. 最佳實踐

1. **隨開發同步撰寫**: 不要事後補文檔
2. **文檔也要 Review**: 大幅修改文檔時使用 `/review-code`
3. **優先更新 CLAUDE.md**: 它是 Claude Code 的 SSOT
4. **ADR 只增不刪**: 過時的 ADR 標記「已取代」而非刪除
5. **WBS 即時更新**: 每完成任務立即更新狀態
