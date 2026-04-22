# Session: 2026-04-08

**開始時間:** 2026-04-08（延續 template-optimization session 後）
**最後更新:** 2026-04-08
**專案:** D:\模板\claude_v2026（Claude Code 工作流模板）
**主題:** 修正 pre-tool-use / post-write hook 的 stdout 污染 + 診斷 UserPromptSubmit 間歇性 hook error

---

## 我們在建構什麼

恢復上次 `2026-04-08-template-optimization-complete-session.md` 後，使用者回報在別的專案用此模板時遇到 hook error。使用者已自行完成根因分析，需要驗證並修正：

1. **hook stdout 污染修正** — `pre-tool-use.sh` 與 `post-write.sh` 的註解明寫「stdout 必須保持安靜」，但實作中仍用 `echo` 印 TaskMaster 狀態、用 `cat << EOF` 印文檔審查 box 和 WBS 同步 box，違反自己的規則，導致 Claude Code 把輸出標記為 hook error。
2. **UserPromptSubmit 間歇性 hook error 診斷** — 使用者回報時不時出現，需要找出根因。

---

## 確認有效的部分（含證據）

- **hook 污染已修正並 commit** — `e046c86` `fix(hooks): 消除 pre-tool-use 與 post-write 的 stdout 污染`，2 檔 +7/-39，使用者已 push 到 origin/main
- **pre-tool-use.sh 清理完成**：
  - L43-44 `echo "📋 TaskMaster 當前狀態..."` → `log()`
  - L50 待審查文檔 echo → `log()`
  - L63 `echo "💡 提示..."` → 併入 log 訊息
  - L87-88 `echo "🤖 TaskMaster Hub..."` → `log()`
- **post-write.sh 清理完成**：
  - L52-69 `cat << EOF` 文檔審查 box（13 行）→ 單行 `log()`
  - L93-105 `cat << EOF` WBS 同步 box（13 行）→ 單行 `log()`
- **驗證乾淨**：`grep '^\s*(echo|cat <<)(?!.*(>>|>&2|LOG_FILE))'` 兩檔都 no match；`bash -n` 語法檢查通過
- **其他 hook 確認無問題**：
  - `session-start.sh` — SessionStart hook，stdout 允許（歡迎 box 正是 Claude Code CLI 顯示的那塊）
  - `agent-monitor.sh` — echo 全部包在 `{ ... } >> "$LOG_FILE"` 或 `>&2`，正確
  - `user-prompt-submit.sh` — 主要流程無 stdout 污染（只走 `log()` 寫檔）
  - `post-agent-report.sh` — 只有 log 寫檔

---

## 未成功的部分（及原因）

- **UserPromptSubmit 間歇性 error 未完成修正** — 已診斷出 3 個可疑點但尚未動手改：
  1. **最可能**：`user-prompt-submit.sh:48-52` 與 `:79-82` 的 `node "$CLAUDE_DIR/taskmaster.js"` legacy 呼叫。如果使用者的其他專案有舊版 taskmaster.js 殘留，每次 prompt 含 `/task-init` 或 `.md` 就會 fork node 子行程。hook timeout 是 15 秒，node 卡住或慢就會超時 → Claude Code 回報 hook error。符合「時不時」特徵。
  2. **次可能（死程式碼）**：`:26` `jq -r '.content // .message // ""'` — UserPromptSubmit hook 實際欄位是 `.prompt`，所以 `USER_INPUT` 永遠是空字串，下面分支永遠不觸發。反而意外保護了 node 不被呼叫，但也代表 `/task-*` 偵測完全沒在工作。
  3. **第三**：`:50, :80` `cd "$PROJECT_ROOT"` 不在 subshell 裡，會改整個 hook 行程的 cwd。副作用小但不乾淨。

---

## 尚未嘗試的方法

- **刪除 `user-prompt-submit.sh` 的兩段 legacy node 區塊**（L48-52、L79-82）——模板本身沒有 `taskmaster.js`，留著是定時炸彈
- **把 jq 欄位從 `.content // .message` 改成 `.prompt`**——讓 `/task-*` 偵測真的能 log
- **改 `echo "$INPUT" | jq` 為 `printf '%s' "$INPUT" | jq`**——避免特殊字元（反斜線、控制字元）被 echo 解析
- **把 `cd "$PROJECT_ROOT"` 包進 subshell `( cd ...; ... )`** 或直接刪掉（node 區塊移除後就不需要了）
- **跨平台 hook 在 Linux 真機測試**（延續前 session）
- **`/task-init` 端到端測試**（延續前 session）

---

## 檔案當前狀態

| 檔案 | 狀態 | 備註 |
|---|---|---|
| `.claude/hooks/pre-tool-use.sh` | 完成 | 所有 stdout echo 改 log()，已 commit e046c86 |
| `.claude/hooks/post-write.sh` | 完成 | 兩個 `cat << EOF` box 改 log() 單行，已 commit e046c86 |
| `.claude/hooks/user-prompt-submit.sh` | 待修 | 已診斷 3 問題點，尚未動手 |
| `.claude/hooks/session-start.sh` | 無需改 | SessionStart 允許 stdout |
| `.claude/hooks/agent-monitor.sh` | 無需改 | `{ } >> $LOG_FILE` 正確導向 |
| `.claude/hooks/post-agent-report.sh` | 無需改 | 只寫檔 |
| `.claude/sessions/2026-04-08-template-optimization-complete-session.md` | 前次 session 已保存 | 本次 session 從這裡恢復 |
| `.claude/sessions/2026-04-08-hook-stdout-fix-session.md` | 本檔案 | 本次 session 紀錄 |

---

## 已做的決策

- **不用 echo 到 stdout、一律走 log() 寫檔** — 原因：註解明寫的規則就要貫徹，兩個 hook 之所以觸發 error 就是自打嘴巴。log() 寫 `.claude/logs/hooks.log` 不影響 Claude Code stdout 監測。
- **保留 `post-write.sh` 的功能性 log 訊息（檔名、WBS 同步事件）** — 原因：刪除會失去運維可見性；改成單行 log() 同時保留資訊和合規。
- **`session-start.sh` 的 ANSI box 不動** — 原因：SessionStart hook 的 stdout 是設計用來顯示歡迎訊息的（本次 session 開頭看到的 TaskMaster Ready box 就是它印的）。
- **UserPromptSubmit 錯誤**初判定位為「legacy node 呼叫 + 15s timeout」而非 stdout 污染 — 原因：UserPromptSubmit hook 的 stdout 會被 Claude Code 當作額外 prompt context（不是 error），所以 stdout 不是嫌疑犯；non-zero exit 或 timeout 才是。
- **本次不繼續 user-prompt-submit.sh 的修正** — 原因：使用者要求先存 session，下次再決定是否動手（也許需要他在另一個專案驗證 taskmaster.js 是否真的存在）。

---

## 阻礙與待解決問題

- **未實際驗證使用者其他專案是否有 `taskmaster.js` 殘留** — 需要使用者自己確認，或下次 session 可請他跑 `ls .claude/taskmaster.js` 在那邊的專案
- **UserPromptSubmit hook error 實際觸發條件未能觀察** — 沒有拿到 hooks.log 片段看到錯誤時點
- **使用者的 hook 檔可能還是舊版** — 剛剛的 fix commit 是在這個模板 repo，使用者其他專案需要把新版 pre-tool-use.sh / post-write.sh 同步過去才會生效

---

## 確切的下一步

**如果要修 UserPromptSubmit hook**：
1. 先請使用者在出問題的專案跑 `ls .claude/taskmaster.js` 確認 legacy 檔案是否存在
2. 修 `user-prompt-submit.sh`：
   - 刪 L48-52、L79-82 的 node 區塊（含 `cd "$PROJECT_ROOT"`）
   - L26 `.content // .message` → `.prompt`
   - L22 `INPUT=$(cat)` → `INPUT=$(cat)`（OK）；L26 `echo "$INPUT"` → `printf '%s' "$INPUT"`
3. `bash -n` 驗證語法
4. commit：`fix(hooks): 移除 user-prompt-submit legacy node 呼叫並修正 jq 欄位`
5. 請使用者把新版同步到另一個出問題的專案

**如果不急著修**：
- 等使用者觀察另一個專案的實際錯誤頻率和觸發條件再決定
- 或跳回其他優化任務（前 session 遺留：Linux 實測、/task-init 端到端測試）

**參考文件**：
- 本次 session：`.claude/sessions/2026-04-08-hook-stdout-fix-session.md`
- 前次 session：`.claude/sessions/2026-04-08-template-optimization-complete-session.md`
- Hook 規則：`.claude/PAUSE_RESUME_GUIDE.md`、`.claude/MECHANISMS.md`
