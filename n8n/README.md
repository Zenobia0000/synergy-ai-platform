# n8n Workflows

## 設定步驟

### 1. 匯入 Workflow

1. 開啟 n8n: `http://localhost:5678`
2. 點擊 "Import from file"
3. 匯入 `workflows/publish_main.json`

### 2. 配置 Credentials

#### X (Twitter) API
1. 在 n8n Settings → Credentials 新增 "OAuth2 API"
2. 填入 X Developer Portal 的:
   - Client ID
   - Client Secret
   - Authorization URL: `https://twitter.com/i/oauth2/authorize`
   - Token URL: `https://api.twitter.com/2/oauth2/token`
   - Scope: `tweet.read tweet.write users.read`

### 3. 測試

啟動後端後，在前端建立一篇貼文並點擊「立即發佈」，觀察:
1. 後端 scheduler 觸發 n8n webhook
2. n8n 執行 workflow
3. n8n 回報結果至後端 webhook
4. 前端自動更新狀態

### 4. 注意事項

- 後端在 Docker 外運行時，n8n 用 `host.docker.internal:8000` 連回後端
- 後端在 Docker 內運行時，改用 `backend:8000`
- Webhook Secret 需與後端 `.env` 中的 `N8N_WEBHOOK_SECRET` 一致

## Workflows

| 檔案 | 用途 | 觸發方式 |
|------|------|---------|
| `publish_main.json` | 多平台發佈 | POST webhook `/webhook/publish` |
