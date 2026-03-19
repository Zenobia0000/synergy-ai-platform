# n8n Workflows

## 設定步驟

### 1. 匯入 Workflow

1. 開啟 n8n: `http://localhost:5678`
2. 點擊 "Import from file"
3. 匯入 `workflows/publish_main.json`

### 2. 設定 n8n 環境變數

在 n8n Settings → Variables 新增：

| 變數名 | 說明 | 取得方式 |
|--------|------|---------|
| `IG_USER_ID` | Instagram Business 帳號 ID | Graph API Explorer 查詢 |
| `IG_ACCESS_TOKEN` | Page Access Token (長期) | Facebook Developer 產生 |

### 3. Instagram API 前置需求

1. **Facebook Developer App** — 到 [developers.facebook.com](https://developers.facebook.com) 建立 App
2. **連結 Instagram Professional 帳號** — Instagram 帳號需為 Business 或 Creator 類型
3. **連結 Facebook Page** — IG 帳號需綁定一個 Facebook Page
4. **取得權限** — App 需要以下權限：
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_read_engagement`
5. **取得 IG User ID** — 用 Graph API Explorer 呼叫：
   ```
   GET /me/accounts?fields=instagram_business_account
   ```
6. **取得長期 Token** — 短期 token 需換成 60 天長期 token：
   ```
   GET /oauth/access_token?grant_type=fb_exchange_token&client_id={app-id}&client_secret={app-secret}&fb_exchange_token={short-token}
   ```

### 4. Instagram 發佈流程 (兩步驟)

```
Step 1: POST /{ig-user-id}/media
        body: { image_url, caption, access_token }
        → 取得 creation_id

Step 2: POST /{ig-user-id}/media_publish
        body: { creation_id, access_token }
        → 取得 post id
```

> 注意: Instagram API 要求 `image_url` 必須是公開可存取的 URL

### 5. 測試

啟動後端後，在前端建立一篇貼文（需有圖片 URL），勾選 Instagram，點「立即發佈」：
1. 後端 scheduler 觸發 n8n webhook
2. n8n 執行 IG 兩步驟發佈
3. n8n 回報結果至後端 webhook
4. 前端自動更新狀態

### 6. 注意事項

- 後端在 Docker 外運行時，n8n 用 `host.docker.internal:8000` 連回後端
- Webhook Secret 需與後端 `.env` 中的 `N8N_WEBHOOK_SECRET` 一致
- Instagram 發佈**必須有圖片**（純文字不支援）
- 圖片 URL 必須是公開可存取的（不能是 localhost）

## Workflows

| 檔案 | 用途 | 觸發方式 |
|------|------|---------|
| `publish_main.json` | Instagram 發佈 | POST webhook `/webhook/publish` |
