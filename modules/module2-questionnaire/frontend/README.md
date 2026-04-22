# Frontend — Synergy Questionnaire AI

Vite + React 19 + TypeScript + Tailwind v4 SPA。

## 啟動

```bash
npm install
npm run dev
```

開 http://localhost:3000 即可。

預設會把 `/api/*` 反向代理到 `BACKEND_URL`（預設 `http://localhost:8000`）。若後端跑在別的位置：

```bash
BACKEND_URL=http://localhost:9000 npm run dev
```

若需要直連外部 API（跳過 proxy），設定 `VITE_API_BASE`：

```bash
echo 'VITE_API_BASE=http://localhost:8000' > .env.local
```

## 專案結構

```
frontend/
├── index.html            # Vite entry
├── vite.config.ts        # Vite + Tailwind 設定、/api proxy
├── src/
│   ├── main.tsx          # React 掛載點 + BrowserRouter
│   ├── App.tsx           # 路由定義
│   ├── index.css         # Tailwind + Apple Design tokens
│   ├── routes/           # Home、Questionnaire、Advice 三條路由
│   ├── components/
│   │   ├── ui/           # Button、Card、Input、Section
│   │   ├── questionnaire/
│   │   └── advice/
│   └── lib/              # api、types、clipboard、markdown、conditions、download
```

## Scripts

| Script | 用途 |
| :--- | :--- |
| `npm run dev` | 開發伺服器（含熱重載、API proxy） |
| `npm run build` | 型別檢查 + 生產 build 到 `dist/` |
| `npm run preview` | 本機 preview `dist/` |
| `npm run typecheck` | 只跑 `tsc -b` 驗型別 |
