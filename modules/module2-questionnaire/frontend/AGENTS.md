# Frontend — Vite + React

本目錄採用 **Vite 6 + React 19 + TypeScript + Tailwind v4 + React Router 7**。已**不再**使用 Next.js。

寫程式碼前請注意：
- 所有頁面都是 client-side SPA，不需要 `"use client"` 指示詞
- 路由用 `react-router-dom`（`Link` 用 `to=`、導頁用 `useNavigate()`）
- 圖片用原生 `<img loading="lazy">`，不要引入 `next/image`
- 環境變數走 `import.meta.env.VITE_*`（不是 `process.env.NEXT_PUBLIC_*`）
- `@/*` alias 指向 `src/*`（設定在 `vite.config.ts` resolve.alias + `tsconfig.app.json` paths）
- 後端 API 透過 `/api/*` → `BACKEND_URL` (預設 `http://localhost:8000`) 的 Vite proxy，呼叫端用相對路徑即可

UI 風格遵循 `.claude/ui/apple/DESIGN.md`（`.claude/taskmaster-data/ui-style.json` 指定）。
