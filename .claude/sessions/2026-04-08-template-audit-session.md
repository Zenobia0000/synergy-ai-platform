# Session: 2026-04-08

**開始時間:** 2026-04-07 約 17:00（跨日）
**最後更新:** 2026-04-08 09:55
**專案:** D:\模板\claude_v2026（Claude Code 工作流模板）
**主題:** 模板優化檢視 — 完成 P1'（取材池索引）與 P2（機制對照表）

---

## 我們在建構什麼

對 `claude_v2026` 模板做全面優化檢視，分 5 個優先級（P1-P5）。本次 session 完成 P1' 與 P2：

1. **P1'** — 為 `.claude/custom-rule&skill/` 備份取材池建立 README 與 INDEX，澄清它不是執行用、而是 94 個 skill + 8 種語言 rules 的備份倉庫
2. **P2** — 建立 `.claude/MECHANISMS.md` 作為 Agent / Skill / Command / Hook 四套擴充機制的權威職責邊界文件
3. **驗證** — 確認 `custom-rule&skill/` 不會被 Claude Code 自動掃描或觸發

---

## 確認有效的部分（含證據）

- **取材池不會被誤觸發** — 三層證據驗證：
  1. Claude Code 只掃描 `.claude/{agents,commands,skills,hooks,rules}` 頂層，不遞迴
  2. `settings.json` 沒有任何 `custom-rule&skill` 引用
  3. 本次 session 啟動時系統列出的可用 skills 只有 8 個精選 + 中文 commands，94 個備份 skill 完全沒出現
- **變更已 commit** — d7f4b15「docs:新增模板機制對照表與取材池索引」，工作樹已清空
- **取材池規模確認** — 94 個 skill（不是 95），分 7 大類：通用工程 13、AI/Agent 23、語言框架 34、API/MCP 6、內容寫作 9、產業垂直 8、範本 1

---

## 未成功的部分（及原因）

- **第一輪 Explore agent 報告誇大 P1 嚴重性** — 把備份池的「64 個重複規則檔」標為 HIGH 優先級需要重構，但其實使用者澄清那是備份倉庫不參與執行，根本不需要去重。教訓：agent 不知道目錄用途時會用最差假設推論
- **Explore agent 把 .mcp.json 標為 CRITICAL 安全漏洞** — 聲稱 BRAVE_API_KEY 已洩漏到版本控制。實際驗證 `.gitignore:2-3` 已正確排除、`git log` 無紀錄，從未進入版本控制。**未來檢查安全聲明時務必先驗 git 歷史**

---

## 尚未嘗試的方法

- **P3 — Hook 平台健壯性**（小，下一步建議從這開始）
  - `.claude/hooks/post-write.sh`、`pre-tool-use.sh` 硬編碼路徑、無 jq 可用性檢查
  - 建議改用 `CLAUDE_PROJECT_DIR` 環境變數、加 `command -v jq >/dev/null || exit 0` 軟降級
- **P4 — README.md 與 CLAUDE_TEMPLATE.md 文件去重**（60% 內容重疊）
- **P5 — `continuous-learning` v1/v2 收斂**（兩者都在備份池，可能可跳過）
- **小型清理：刪除 `test-automation-engineer` agent**（與 `tdd-guide` 95% 重疊，MECHANISMS.md 已標註建議移除）

---

## 檔案當前狀態

| 檔案 | 狀態 | 備註 |
|---|---|---|
| `.claude/MECHANISMS.md` | 完成 | 新檔，四機制權威對照 + 決策樹 + FAQ |
| `.claude/custom-rule&skill/README.md` | 完成 | 新檔，標示為備份池 |
| `.claude/custom-rule&skill/skills/INDEX.md` | 完成 | 新檔，94 skill 分 7 類 |
| `.claude/skills/INDEX.md` | 完成 | 修正失效的 `everything-claude/` 路徑 |
| `.claude/agents/test-automation-engineer.md` | 待刪除 | 與 tdd-guide 重疊，建議下次清理 |
| `.claude/hooks/*.sh` | 待 P3 處理 | 平台健壯性問題未動 |

---

## 已做的決策

- **P1 重新定義為 P1'（取材池索引）** -- 原因: 使用者澄清 `custom-rule&skill/` 是備份倉庫，不該去重。改為補索引文件，讓未來取材好挑
- **保留 `/review-code` 與 `/check-quality` 並存** -- 原因: 兩者在 MECHANISMS.md 中已釐清角色分工（一個分類、一個執行），不算重疊
- **`security-review` skill 與 `security-infrastructure-auditor` agent 不合併** -- 原因: skill 是檢查清單、agent 是執行者，分工健康
- **MECHANISMS.md 放在 `.claude/` 根目錄而非 `.claude/docs/`** -- 原因: 提高可見度，作為唯一權威來源

---

## 阻礙與待解決問題

- 無阻礙
- 待確認：使用者要不要直接刪 `test-automation-engineer.md`？這是 P2 的自然延伸但本 session 沒做
- 待確認：P3 vs P4 哪個先做？兩者都是「小、低風險」

---

## 確切的下一步

**問使用者**：「上次停在準備做 P3（Hook 平台健壯性）或 P4（文件去重）。要從哪一個開始？」

如果使用者選 P3：先讀 `.claude/hooks/post-write.sh` 與 `pre-tool-use.sh`，找出硬編碼路徑與缺失的 jq 檢查。
如果使用者選 P4：先讀 `README.md` 與 `CLAUDE_TEMPLATE.md`，標出 60% 重疊段落，提議精簡方案。

**參考文件**：本次新建的 `.claude/MECHANISMS.md` 是後續所有 agent/skill 邊界討論的權威來源。
