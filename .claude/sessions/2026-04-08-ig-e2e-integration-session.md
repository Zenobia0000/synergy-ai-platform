# Session: 2026-04-08

**開始時間:** 約 10:00 (UTC+8)
**最後更新:** 18:30 (UTC+8)
**專案:** Personal Content Distributor v2 (n8n_rpa_post)
**主題:** Phase 2.5 Code Review 修復 + Phase 2.6 Instagram 端到端整合（含本機圖片上傳）

---

## 我們在建構什麼

完成 Personal Content Distributor v2 從「Phase 2 最小閉環（n8n workflow 模板存在但未驗證）」→ 「Phase 2.6 Instagram 全流程貫通並可從前端 UI 上傳本機圖片發佈」。

主要工作分兩階段：

1. **Phase 2.5（前置修復）**：對 backend 執行 code review，修補 3 個 CRITICAL（webhook HMAC、scheduler race、零測試覆蓋）與 5 個 HIGH 問題；建立後端最小測試套件（15 tests, 66% coverage）；修復 dev 啟動腳本的 port 衝突與 hooks stdout 污染問題。

2. **Phase 2.6（IG 整合）**：把 backend → n8n → Instagram → callback 整條鏈路打通，並加入 MinIO 物件儲存讓使用者可以從前端 UI 上傳本機圖片，透過 ngrok static domain 讓 Meta API 能抓到本機 backend 提供的圖片 proxy。

最後完成 README + WBS 更新，並切成 3 個邏輯 commit。

---

## 確認有效的部分（含證據）

### Phase 2.5 修復
- **C1 webhook HMAC + fail-fast** — `webhooks.py` 改用 `hmac.compare_digest`；`config.py` 加 `validate_runtime()` 在 `main.py` lifespan 啟動時呼叫。確認方式：tests/test_webhooks.py 的 4 個簽名測試 (missing/wrong/correct/idempotent) 全綠。
- **C2 scheduler atomic claim** — 改成 `UPDATE...RETURNING SKIP LOCKED`，無法被多 worker 重複觸發。確認方式：tests/test_scheduler.py 的 retry/cap 測試通過。
- **C3 backend test suite (15 tests)** — pytest + httpx ASGITransport + aiosqlite，conftest.py 用 SQLAlchemy 跨方言 UUID monkey-patch (`pg.UUID = sa.Uuid`) 讓 PG 模型能跑 sqlite。確認方式：`pytest tests/ -q` → 15 passed。
- **H1 /schedule Pydantic schema** — 新增 `ScheduleRequest`，移除手寫 `data: dict` 解析。
- **H2 delete_content 204** — 改用 `Response(status_code=204)` 只在成功路徑回，錯誤改 JSONResponse。
- **H4 PublishLog UNIQUE** — 加 alembic migration `a1f2c3d4e5b6`；webhook handler 加 idempotent 檢查。
- **H5 api-client robust JSON** — 包 try/catch ApiError，5xx HTML 不再炸 SyntaxError。
- **dev 腳本修復** — port 8888→8000 對齊；start-dev 加 .env + secret 檢查；stop-dev 用 PID-by-port 精準停止取代 `taskkill /IM node.exe`。
- **Hooks stdout 靜默** — `pre-tool-use.sh` / `post-write.sh` 全部 echo→log，消除 hook error 雜訊。
- **vite proxy 8888→8000** — 修 frontend 連 backend 的 ECONNREFUSED。
- **lovable-tagger 移除** — 解 vite 8 peer dep 衝突，npm install 不再需要 `--legacy-peer-deps`。

### Phase 2.6 IG 整合
- **n8n workflow 修正** — `graph.facebook.com` → `graph.instagram.com`（對齊 IGAA token），兩個 IG node 之間插 Wait 5s，加 `onError: continueErrorOutput` → Report IG Failure；webhook secret 從硬編碼改讀 `$env.N8N_WEBHOOK_SECRET`。確認方式：n8n execution 從 error 變 success，IG App 看到貼文。
- **N8N_BLOCK_ENV_ACCESS_IN_NODE=false** — n8n 預設禁止 workflow 存取 `$env.*`，加這個才能讀 IG 憑證與 webhook secret。
- **Backend /publish bug fix** — 原本只設 `status=publishing` 不觸發 n8n（scheduler 只看 `queued`），修為 BackgroundTasks 呼叫 `publish_content_now`。確認方式：完整 E2E curl 序列 status 從 publishing → success 大約 15 秒。
- **MinIO + minio-init** — docker-compose 加兩個 service，bucket auto-create 的一次性容器。確認方式：`docker compose ps` 三 container 都 healthy；`docker exec ... mc ls` 看到 bucket。
- **Backend uploads endpoint** — `POST /uploads/image` 用 minio SDK + `asyncio.to_thread`；`GET /uploads/{key}` 用 StreamingResponse 從 MinIO 串流。bucket 全程私有。
- **Frontend file picker** — `CreateContent.tsx` 圖片欄位旁的 ⬆ 按鈕觸發 hidden file input；`upload-api.ts` 包 multipart fetch；上傳成功自動填入 image_url + 顯示預覽。
- **ngrok static domain** — 用 `nonignitible-appraisingly-adelynn.ngrok-free.dev` 永久 URL，寫進 `backend/.env` 的 `PUBLIC_BASE_URL`。
- **圖片 URL 雙形態策略** — `storage_service.build_relative_url()` 回相對路徑存進 DB，前端 vite proxy 直接載圖；`to_absolute_url()` 只在 trigger n8n 時補 ngrok 前綴給 IG 抓。避開 ngrok 免費版警告 HTML 頁讓 `<img>` 載入失敗的問題。
- **允許刪除 failed 貼文** — backend `DELETABLE_STATUSES = {"draft", "failed"}`；frontend `ContentCard` dropdown 對 failed 加「刪除」項。
- **完整 E2E 通過** — 從 UI 點上傳本機 jpg → 看到預覽 → 立即發佈 → 約 15 秒後狀態 success → IG App 出現新貼文 → 列表頁圖片預覽正常。

### 其他
- **15/15 tests still passing** 在每次重大修改後都確認。
- **3 個乾淨 commit** — `c74a263` (feat IG E2E), `7e296cb` (chore .gitignore), `fa358e9` (chore .claude line endings + sync)。working tree 100% 乾淨。

---

## 未成功的部分（及原因）

- **第一次 smoke test curl 用了錯誤的 body 包裹** — 我給的 payload 多包了一層 `{"body": {...}}`，n8n webhook 自動把 HTTP body 包在 `$json.body`，導致 IF 節點讀的是 `$json.body.platforms` 但實際資料在 `$json.body.body.platforms` → 永遠 false → workflow 停在 IF 節點。修正：去掉外層 `body`。
- **第一次 IG 發佈撞 OAuth 190 "Cannot parse access token"** — 因為 user 走的是 Instagram Login 流程（IGAA token），但 workflow 用 `graph.facebook.com`（給 EAA token 用的）。修正：改 endpoint 為 `graph.instagram.com`。
- **第二次撞 9004 "影音素材 URI 不符規定"** — 用 `picsum.photos/1080/1080.jpg` 做測試圖，但 picsum 會 302 redirect，IG 抓圖器不吃 redirect。修正：改用 Unsplash 直連 200 OK 的 URL。
- **第三次撞 9007 "Media ID is not available"** — IG container 建立後需要時間下載+處理圖片，n8n workflow 立刻打 publish 太快。修正：兩個 node 間插 Wait 5s。
- **第四次發佈 status 卡 publishing** — 因為 backend `/publish` 端點其實沒呼叫 n8n（只設 status=publishing 就 return），被 scheduler 也忽略（scheduler 只看 queued）。修正：加 BackgroundTasks。
- **本機 ngrok 升級失敗** — 一開始 user 裝的是 Microsoft Store ngrok（卡在 3.3.1），ngrok server 拒絕 < 3.20.0 的 agent；`ngrok update` 走 `bin.equinox.io` 也被網路擋；最後用 `winget uninstall + winget install -s winget` 解決。
- **uploaded 圖片預覽不顯示** — 因為 backend 一開始把 `image_url` 存成絕對 ngrok URL，瀏覽器 `<img>` 載 ngrok 時被免費版警告 HTML 頁攔截。修正：DB 改存相對路徑，僅 trigger n8n 時補絕對前綴。
- **第一次跑 backend pytest 直接 pip install 25 個套件到全域 Python** — 違反 user 的「一律用 uv」規範，被立刻要求 uninstall 並改用 uv。已存記憶 `feedback_python_env.md`。
- **stop-dev.sh 用 `taskkill //F //IM node.exe`** — 會殺掉所有 node 程序，太粗暴。修正：用 `netstat -ano` 找 port 對應 PID 精準殺。
- **`.claude/.taskmaster-data/.session-snapshot` 等 runtime artifacts 一開始沒 ignore** — 後來補進 `.gitignore`。

---

## 尚未嘗試的方法

- **替換 Wait node 為 polling container status** — `GET /{container_id}?fields=status_code` 直到 `FINISHED`，比固定 5 秒更穩健，特別是 video 或大圖。MVP 階段先用 Wait 5s。
- **scheduler 失敗的指數退避（exponential backoff）** — 目前只有 retry_count + cap，沒有間隔倍增。MVP 階段夠用。
- **圖片上傳 presigned URL 模式** — 讓前端直接 PUT 到 MinIO，不經過 backend，省 backend 頻寬。改寫不複雜但 MVP 不需要。
- **Cloudflare R2 / B2 / S3 真正 CDN** — 正式上線時換掉 MinIO 自架，以避免 ngrok tunnel 流量限制。
- **後端覆蓋率從 66% 補到 80%** — service 層 (content_service, scheduler) 的 list/sort/cancel/get 還沒測。Phase 3 後補。
- **前端測試** — frontend 只有一個 example.test.ts，沒有實質單元測試或 E2E。Phase 5 任務 5.6 處理。
- **n8n workflow 加 backend→n8n 方向的 secret 驗證** — 目前只有 n8n→backend 用 HMAC，反向沒驗。低風險，但理論上可加 webhook header 驗證。

---

## 檔案當前狀態

| 檔案 | 狀態 | 備註 |
|------|------|------|
| `backend/app/api/v1/webhooks.py` | 完成 | HMAC compare_digest, idempotent log |
| `backend/app/api/v1/contents.py` | 完成 | Pydantic schedule, BackgroundTasks publish, 允許刪 failed |
| `backend/app/api/v1/uploads.py` | 完成 | NEW — multipart upload + streaming proxy |
| `backend/app/services/scheduler_service.py` | 完成 | Atomic claim, retry cap, publish_content_now, image url rewrite |
| `backend/app/services/storage_service.py` | 完成 | NEW — minio SDK wrapper, build_relative_url, to_absolute_url |
| `backend/app/core/config.py` | 完成 | validate_runtime, MinIO + PUBLIC_BASE_URL settings |
| `backend/app/core/database.py` | 完成 | Cross-dialect connect_args (sqlite/asyncpg) |
| `backend/app/main.py` | 完成 | lifespan: validate_runtime + ensure_bucket |
| `backend/app/models/content.py` | 完成 | PublishLog UNIQUE constraint |
| `backend/app/schemas/content.py` | 完成 | ScheduleRequest |
| `backend/alembic/versions/a1f2c3d4e5b6_*.py` | 完成 | NEW migration |
| `backend/tests/conftest.py` | 完成 | NEW — file-based sqlite, UUID patch |
| `backend/tests/test_contents_api.py` | 完成 | NEW — 7 tests |
| `backend/tests/test_webhooks.py` | 完成 | NEW — 5 tests |
| `backend/tests/test_scheduler.py` | 完成 | NEW — 3 tests |
| `frontend/src/services/upload-api.ts` | 完成 | NEW |
| `frontend/src/services/api-client.ts` | 完成 | Robust JSON parse |
| `frontend/src/pages/CreateContent.tsx` | 完成 | File picker integration |
| `frontend/src/components/ContentCard.tsx` | 完成 | 加 failed 刪除選項 |
| `frontend/vite.config.ts` | 完成 | proxy 8888→8000, lovable-tagger 移除 |
| `n8n/workflows/publish_main.json` | 完成 | graph.instagram.com, Wait 5s, error routing, env secret |
| `docker-compose.yml` | 完成 | minio + minio-init, n8n env vars (IG_*, webhook secret, BLOCK_ENV) |
| `.env.example` (root) | 完成 | NEW — for docker-compose |
| `backend/.env.example` | 完成 | + MinIO + PUBLIC_BASE_URL |
| `scripts/start-dev.{sh,bat}` | 完成 | port 8000, .env check, n8n in infra |
| `scripts/stop-dev.{sh,bat}` | 完成 | PID-by-port surgical stop |
| `.claude/hooks/pre-tool-use.sh` | 完成 | stdout silenced |
| `.claude/hooks/post-write.sh` | 完成 | stdout silenced |
| `.claude/taskmaster-data/wbs.md` | 完成 | + Phase 2.5 (12 tasks) + Phase 2.6 (10 tasks) + M2.5/M2.6 |
| `README.md` | 完成 | tech stack, IG setup, ngrok setup, API table, 進度, 架構圖 |
| `.gitignore` | 完成 | + .coverage, exec*.txt, scripts/_parse_exec.py, .session-* |

---

## 已做的決策

- **MinIO + ngrok static domain** — 而非 Cloudflare R2 / S3。原因：MinIO 本機 self-host 完全免費、S3 相容 API 未來可無痛遷移；ngrok 免費送 1 個 static domain (since 2023)，URL 永久不變、不用每次改 .env。
- **MinIO bucket 私有 + backend proxy** — 而非 bucket 公開直連。原因：只需開一個對外 port (backend 8000)，更安全；可加 access log / 限流 / 認證；正式上線可無痛換成 CDN。
- **Image URL 在 DB 存相對路徑** — 而非絕對 ngrok URL。原因：避開 ngrok 免費版警告 HTML 頁攔截瀏覽器 `<img>` 載入；只在 backend 觸發 n8n 時用 `to_absolute_url()` 補前綴給 IG 抓。
- **走 graph.instagram.com 而非 graph.facebook.com** — 因為 user 拿到的是 Instagram Login 流程的 IGAA token。原因：兩種 token 對應不同 host，不能混用；user 已走 Instagram Business Login 流程拿到 token，重做 FB Page 流程不划算。
- **Wait 5 秒而非 polling status** — IG container 處理時間。原因：MVP 階段 5 秒對小圖夠用，polling 邏輯複雜度高；之後支援 video 時再改 polling。
- **/publish 用 BackgroundTasks 而非 queue** — 把 trigger n8n 移到背景任務。原因：HTTP 請求立即 202 回應、user 立即看到 publishing 狀態；不需要引入 Celery/RQ；單機 MVP 級夠用。
- **後端測試用 sqlite + aiosqlite** — 而非 testcontainer postgres。原因：測試啟動快、無 Docker 依賴；用 monkey-patch `pg.UUID = sa.Uuid` 與 file-backed sqlite 解決跨方言與多 session 共享問題。
- **3 個 commit 切分而非單一巨型** — c74a263 (功能) → 7e296cb (.gitignore) → fa358e9 (.claude line endings + 同步)。原因：commit message 每筆專注一件事，方便未來 cherry-pick / revert。
- **失敗貼文允許刪除但成功的不行** — DELETABLE_STATUSES = {draft, failed}。原因：成功貼文是已發佈到 IG 的紀錄，刪 DB 不會撤回 IG 上的內容，誤導性高；草稿與失敗無外部副作用。
- **Hooks 全部移除 stdout 輸出** — 而非保留部分 status box。原因：Claude Code CLI 對非預期 stdout 內容歸類為 hook error，造成大量誤報；hook 自己的註解就寫了「stdout 必須保持安靜」。
- **Python 環境一律 uv** — 已存 memory，禁止 pip install 全域。原因：使用者明確要求，避免污染系統 Python。

---

## 阻礙與待解決問題

- **無重大阻礙**。所有 Phase 2.5 + 2.6 任務都完成、commit、驗證 E2E 通過。
- **次要待辦**：
  - ngrok 每次 dev session 要手動跑 `ngrok http --domain=... 8000`，未整合進 start-dev 腳本。
  - 後端覆蓋率 66%，距 CLAUDE.md 規定的 80% 還有缺口。
  - 前端零實質測試（只有 example.test.ts）。
  - n8n workflow 改動是 in-place edit + reimport，DB 副本已是新版但檔案版本與 DB 副本同步機制脆弱。
- **長期優化方向**：
  - 替 Wait 5s 為 polling container status（穩健性提升）。
  - 替 MinIO 為 Cloudflare R2 / S3（正式上線時）。
  - 替 ngrok 為自有網域 + Cloudflare Tunnel named tunnel（正式上線時）。

---

## 確切的下一步

1. **立刻可做**：`/task-next` 取得 Phase 3 任務（推薦從 3.1 X Adapter 開始，因為 3.1 與 3.2 可並行）；或 3.2 Facebook Page Adapter。預估各 3h，M3 里程碑 2026-04-12。
2. **次優先**：把 ngrok 啟動步驟加進 `start-dev.sh` / `start-dev.bat`，用 background 方式啟動，並從 backend/.env 讀 PUBLIC_BASE_URL 推導 domain。
3. **如果要 push**：`git push origin main` 把 3 筆 commit 推到 remote。
4. **也可以直接收工**：今天 IG E2E 全程通了、所有 commit 乾淨、tests 全綠，working tree empty。下次 session 可直接 `/task-next` 從 Phase 3 開始。

### 環境狀態（給下次 session 參考）
- Backend `.env`：已設 N8N_WEBHOOK_SECRET / SECRET_KEY / IG_ACCESS_TOKEN / IG_USER_ID / PUBLIC_BASE_URL
- Root `.env`：已設 N8N_WEBHOOK_SECRET / IG_ACCESS_TOKEN / IG_USER_ID
- Docker：postgres + n8n + minio 三個 healthy
- DB migration：head = `a1f2c3d4e5b6` (publish_logs UNIQUE)
- n8n workflow：`Content Distributor - Publish Main` 已 import + Active
- ngrok domain：`nonignitible-appraisingly-adelynn.ngrok-free.dev` (claim 完成，static)
- IG workflow：`graph.instagram.com` 走 IGAA token，已驗證可發佈
