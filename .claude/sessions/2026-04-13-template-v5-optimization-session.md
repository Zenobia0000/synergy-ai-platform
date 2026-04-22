# Session: 2026-04-13

**開始時間:** 約 09:00
**最後更新:** ~16:00
**專案:** claude_v2026（Claude Code 開發模板）
**主題:** v5.0 全面效能優化 + 企業級範本強化 + Skills/MCP 擴充

---

## 我們在建構什麼

對 Claude Code 開發模板進行全面效能優化和功能擴充。從 v4.4 升級到 v5.0，主要目標是：
1. 精簡不必要的 context 佔用（Skills/Rules/Hooks/文檔）
2. 新增針對使用者開發場景（Python 全端 + AI 工具）的 Skills
3. 強化 VibeCoding 文件範本至企業級標準
4. 整理模板目錄結構，統一歸檔

---

## 確認有效的部分（含證據）

- **刪除 6 個通用 Skills** — coding-standards、api-design、security-review、tdd-workflow、deployment-patterns、docker-patterns 全部是模型內建知識，刪除後功能零損失
- **Skills on-demand 載入從 3,267 行降到 ~1,500 行** — 減少 context window 浪費
- **Rules 每次對話注入從 294 行降到 ~230 行** — interactive-qa 從 101→18 行效果最顯著
- **3 個 Hooks 精簡 81%** — pre-tool-use、user-prompt-submit、post-write 大部分只做 log，精簡後功能相同
- **文檔歸檔到 guides/** — MECHANISMS、WORKFLOW、PAUSE_RESUME_GUIDE、STATUSLINE_GUIDE、MCP_CONFIGS 統一管理
- **VibeCoding 範本強化** — 02_PRD 擴展（+OKRs/Personas/競爭分析）、07_module_spec 擴展（+效能邊界/實際測試）、09+10 合併、11 審查強化
- **完整性檢查通過** — 所有陳舊引用（09/10 舊模板、CONTEXT_USAGE.md）全部修正

---

## 未成功的部分（及原因）

- **無重大失敗**
- **小問題：繁體中文翻譯時出現亂碼** — Write 工具寫入某些中文字（如「預算」「深度」「模式」）時產生亂碼 `���`，需要事後用 Edit 修正。原因不明，可能是編碼問題。

---

## 尚未嘗試的方法

- MongoDB patterns skill（使用者常用 MongoDB 但目前無專屬 skill，評估後認為模型知識 + context7 足夠）
- Plugin marketplace 發布（dev-project-kit plugin 已建立但尚未 push 到 GitHub）
- output-styles 的 09_file_dependencies / 10_class_relationships 引用可能還有遺漏（只修了 03-architecture-design-doc，其他 output-styles 未全面掃描）

---

## 檔案當前狀態

| 檔案/目錄 | 狀態 | 備註 |
|:---|:---|:---|
| `.claude/skills/` (7 個) | 完成 | project-docs, deep-research, e2e-testing, cost-aware-llm-pipeline, mcp-builder, database-migrations, postgres-patterns |
| `.claude/rules/` (9 個) | 完成 | 新增 ui-design（Apple 風格毛玻璃） |
| `.claude/guides/` (5 個) | 完成 | WORKFLOW, MECHANISMS, MCP_CONFIGS, PAUSE_RESUME, STATUSLINE |
| `.claude/plugins/dev-project-kit/` | 完成 | 包含 4 個 skill 的可攜帶 plugin（內容未同步最新 7 個） |
| `.claude/hooks/` (7 個) | 完成 | 3 個精簡，4 個保持原樣 |
| `VibeCoding_Workflow_Templates/` (16 個) | 完成 | 02 擴展、07 擴展、09+10 合併、11 強化、output_style.md 刪除 |
| `.mcp.json` | 完成 | 新增 firecrawl MCP |
| `README.md` (根目錄) | 完成 | v5.0，所有計數正確 |
| `.claude/README.md` | 完成 | 所有計數正確 |

---

## 已做的決策

- **Skills 篩選原則** — 只保留「模型不知道的專案特定知識」，通用知識（PEP 8、React hooks、OWASP）不需要 skill
- **前端/後端不設 skill** — 靠模型內建知識 + context7 MCP 即時查文檔 + rules/patterns.md
- **Python/TS 不設語言 skill** — 模型知識足夠，python-patterns (750行) 和 python-testing (816行) 90% 是通用知識
- **ui-design 用 rule 不用 skill** — 設計風格需要每次對話都生效，rule 自動注入更合適
- **VibeCoding 編號不重排** — 合併 09+10 後缺 10 號，但重排會影響 30+ 處引用，風險大於收益
- **Agent 模型維持 opus/sonnet/haiku 三級** — planner+architect+security=opus，核心開發=sonnet，輕量任務=haiku
- **firecrawl 優於 exa** — deep-research skill 需要「搜尋+深讀完整網頁」，firecrawl 一個工具覆蓋兩個能力

---

## 阻礙與待解決問題

- **dev-project-kit plugin 只有 4 個 skill** — 新增的 mcp-builder、database-migrations、postgres-patterns 還沒同步到 plugin
- **output-styles 可能還有陳舊引用** — 只掃了 03-architecture-design-doc，其餘 14 個 output-style 未全面檢查 09/10 引用
- **Write 工具的中文亂碼問題** — 偶發，原因不明，暫時用 Edit 事後修正

---

## 確切的下一步

1. 同步 dev-project-kit plugin（把 7 個 skill 都複製進去）
2. 全面掃描 output-styles/ 裡是否還有 09/10 舊模板引用
3. 可以開始在實際專案中測試此模板：`cp -r claude_v2026 新專案路徑`
