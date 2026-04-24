# Synergy AI POC — 文件總覽

> **POC 範圍：** 3 模組、12 功能 | **工期：** 13 週（2026-04-28 ~ 2026-07-27）
> **合作模式：** 合夥共創（客戶方 + 開發方共同定義與驗收）
> **最後更新：** 2026-04-22

---

## 文件架構

```
Layer 1: WHY（為什麼做）
  └─ D1. POC Charter

Layer 2: WHAT（做什麼）
  ├─ D2. POC-Scoped PRD
  └─ D3. Success Metrics & Exit Criteria

Layer 3: HOW（怎麼做）
  ├─ D4. Technical Feasibility Assessment
  ├─ D5. WBS & Timeline + Gantt
  └─ D6. Risk Register

Layer 4: WHO（誰負責）
  └─ D7. RACI & Stakeholder Agreement
```

---

## 文件索引

| # | 文件 | 說明 | 狀態 |
|---|------|------|------|
| D1 | [00_poc_charter.md](./00_poc_charter.md) | POC 章程 — 商業假設、範疇邊界、Go/No-Go 決策閘門 | v1.0 |
| D2 | [01_poc_prd.md](./01_poc_prd.md) | POC 範圍 PRD — 12 功能的 User Story + 驗收標準 | v1.0 |
| D3 | [02_success_metrics.md](./02_success_metrics.md) | 成功指標與退出標準 — 功能/技術/商業驗證 + Go/No-Go 決策樹 | v1.0 |
| D4 | [03_technical_feasibility.md](./03_technical_feasibility.md) | 技術可行性評估 — 技術棧、Spike 項目、第三方依賴、整合複雜度 | v1.0 |
| D5 | [04_wbs.md](./04_wbs.md) | 工作分解結構 — 28 個工作包含驗收標準、5 個里程碑 | v1.1 |
| D5 | [05_gantt.md](./05_gantt.md) | 甘特圖 — Mermaid 視覺化時程與資源分配 | v1.0 |
| D6 | [06_risk_register.md](./06_risk_register.md) | 風險登記簿 — 15 項風險、熱力圖、升級流程 | v1.0 |
| D7 | [07_raci_agreement.md](./07_raci_agreement.md) | RACI 職責矩陣 — 合夥共創協議、溝通節奏、變更管理 | v1.0 |

---

## 閱讀順序建議

1. **先讀 D1（Charter）** — 理解 POC 的「為什麼」和「邊界」
2. **再讀 D3（Success Metrics）** — 知道怎樣算成功
3. **然後 D7（RACI）** — 明確雙方職責
4. **需要細節時讀 D2（PRD）** — 每個功能的具體規格
5. **技術關注讀 D4（Feasibility）** — 風險和依賴
6. **執行階段參考 D5 + D6** — WBS 排程和風險追蹤

---

## 上層文件（完整產品）

| 文件 | 說明 |
|------|------|
| [01_synergy_ai_prd.md](../01_synergy_ai_prd.md) | 完整 PRD（6 模組） |
| [02_synergy_ai_sow.md](../02_synergy_ai_sow.md) | 軟體需求分析暨工作說明書 |
| [03_user_journey_map.md](../03_user_journey_map.md) | 使用者旅程地圖 |
| [04_module_breakdown.md](../04_module_breakdown.md) | 模組拆解與技術架構 |
| [05_wbs_pre_development.md](../05_wbs_pre_development.md) | 開發前交付物 WBS |

---

## 原始需求來源

- [六大功能模組進度.docx](../六大功能模組進度.docx) — 客戶勾選 POC 範圍（藍底項目）
