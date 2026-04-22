# 前端架構規格（Frontend Architecture）— Synergy Questionnaire AI

> **專案:** synergy-questionnaire-ai POC
> **最後更新:** 2026-04-22
> **參照模板:** `VibeCoding_Workflow_Templates/12_frontend_architecture_specification.md`
> **IA 對照:** `docs/17_frontend_information_architecture.md`

---

## 1. 技術選型

| 層 | 技術 | 選用原因 |
|---|---|---|
| Build tool | Vite 6 | 啟動快、HMR 即時，純 SPA POC 無 SSR 需求 |
| UI library | React 19 | Concurrent features、新 hooks API |
| 語言 | TypeScript 5 | 型別安全、與 Pydantic schema 對齊 |
| 樣式方案 | Tailwind CSS v4 + CSS 變數 | v4 的 `@theme` 直接在 CSS 內定義 tokens，無需 `tailwind.config.ts` |
| 路由 | React Router 7 | 社群標準 SPA 路由，支援 nested routes 與 loader（未來擴充） |
| 狀態管理 | React useState + Context | POC 無複雜跨頁狀態；角色用 Context + sessionStorage |
| 資料 fetch | 原生 `fetch` + 薄封裝（`src/lib/api.ts`） | POC 無需 react-query / SWR |
| 表單 | 自製（`QuestionnaireForm`） | 問卷 schema driven，不需 react-hook-form |
| 測試 | 先空白 | POC 優先 E2E checklist，單元測試後補 |

---

## 2. 目錄結構

```
frontend/
├── index.html
├── vite.config.ts              # Vite 設定、/api proxy、@/* alias
├── tsconfig.{json,app.json,node.json}
├── package.json
└── src/
    ├── main.tsx                # Entry：BrowserRouter + RoleProvider
    ├── App.tsx                 # 路由總表
    ├── index.css               # Tailwind + @theme tokens + 全域樣式
    ├── routes/                 # 每檔 = 一個路由頁面
    │   ├── Home.tsx            # /
    │   ├── Login.tsx           # /login
    │   ├── Questionnaire.tsx   # /u/questionnaire
    │   ├── UserResult.tsx      # /u/result
    │   └── CoachAdvice.tsx     # /coach, /coach/advice
    ├── components/
    │   ├── layout/             # 共用 layout
    │   │   ├── AppLayout.tsx   # Header + Outlet + Footer
    │   │   ├── Header.tsx
    │   │   └── Footer.tsx
    │   ├── ui/                 # 原子元件（token 對齊）
    │   │   ├── Button.tsx
    │   │   ├── Card.tsx
    │   │   ├── Input.tsx
    │   │   └── Section.tsx
    │   ├── questionnaire/      # 問卷領域元件
    │   └── advice/             # 建議結果領域元件
    ├── contexts/
    │   └── RoleContext.tsx     # 角色 Context + 角色 guard hook
    └── lib/
        ├── api.ts              # fetch 封裝 + ApiError
        ├── types.ts            # 與後端 Pydantic 對齊的 TS 型別
        ├── role.ts             # sessionStorage 讀寫 + 型別
        ├── conditions.ts       # 問卷條件式顯示
        ├── clipboard.ts        # 複製到剪貼簿
        ├── download.ts         # 下載 Markdown
        └── markdown.ts         # 建議結果 → Markdown
```

---

## 3. 路由策略

### 路由總表（React Router 7 `Routes`）

```tsx
<Routes>
  <Route element={<AppLayout />}>
    <Route path="/" element={<Home />} />
    <Route path="/login" element={<Login />} />
    <Route element={<RoleGuard require="user" />}>
      <Route path="/u/questionnaire" element={<Questionnaire />} />
      <Route path="/u/result" element={<UserResult />} />
    </Route>
    <Route element={<RoleGuard require="coach" />}>
      <Route path="/coach" element={<CoachAdvice />} />
      <Route path="/coach/advice" element={<CoachAdvice />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Route>
</Routes>
```

### RoleGuard

- 讀 `useRole()`；無 role → `Navigate to="/login"`
- role 不符合 → 導向角色對應首頁（user → `/u/questionnaire`，coach → `/coach`）
- 教練可填問卷：`Questionnaire` 另允許 `role === "coach"`（在元件內自檢，或獨立 `RoleGuard require={["user","coach"]}`）

---

## 4. 角色與 Session 管理

### RoleContext（`src/contexts/RoleContext.tsx`）

```ts
type Role = "user" | "coach";
interface RoleContextValue {
  role: Role | null;
  setRole: (role: Role) => void;
  clearRole: () => void;
}
```

- 初始化時讀 `sessionStorage.role`
- `setRole` 同步寫入 sessionStorage
- `clearRole` 清除 role + `last_advice_result` + `pending_advice_request`（避免角色混用）

### Session 資料 key

| Key | 型別 | 用途 |
|---|---|---|
| `role` | `"user" \| "coach"` | 目前角色 |
| `pending_advice_request` | `Answers` JSON | 問卷答案（送 API 前暫存） |
| `last_advice_result` | `AdviceResponse` JSON | 後端回傳的完整建議 |

---

## 5. 樣式方案（Tailwind v4 + Design Tokens）

### Tokens 注入

所有 Apple tokens 在 `src/index.css` 的 `@theme` block 中定義，Tailwind v4 自動生成對應 utility class：

```css
@import "tailwindcss";

@theme {
  /* Colors */
  --color-bg: #f5f5f7;
  --color-bg-elevated: #ffffff;
  --color-fg: #1d1d1f;
  --color-fg-muted: rgba(0, 0, 0, 0.8);
  --color-fg-subtle: rgba(0, 0, 0, 0.48);
  --color-accent: #0071e3;
  --color-accent-hover: #0077ed;
  --color-success: #34c759;
  --color-warning: #ff9f0a;
  --color-error: #ff3b30;
  --color-border: rgba(0, 0, 0, 0.12);

  /* Typography */
  --font-display: "SF Pro Display", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --font-sans: "SF Pro Text", "SF Pro Icons", "Helvetica Neue", Helvetica, Arial, sans-serif;

  /* Typography scale (selected) */
  --text-hero: 56px;
  --text-heading-lg: 40px;
  --text-heading-md: 28px;
  --text-heading-sm: 21px;
  --text-body: 17px;
  --text-caption: 14px;
  --text-micro: 12px;

  /* Spacing scale */
  --spacing-1: 4px;
  --spacing-2: 8px;
  --spacing-3: 12px;
  --spacing-4: 16px;
  --spacing-6: 24px;
  --spacing-8: 32px;
  --spacing-12: 48px;
  --spacing-16: 64px;

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 11px;
  --radius-lg: 12px;
  --radius-pill: 980px;

  /* Shadow */
  --shadow-card: 3px 5px 30px 0px rgba(0, 0, 0, 0.22);
}
```

### 使用規則

| 場景 | 做法 |
|---|---|
| 背景/文字顏色 | Tailwind utility：`bg-bg`、`text-fg`、`text-fg-muted`、`bg-accent` |
| 字體大小 | Tailwind utility：`text-body`、`text-heading-md` |
| 間距 | Tailwind 既有 scale（`p-4`、`gap-8`）對應 4/8/12/16/24/32/48/64px |
| 圓角 | `rounded-sm`（8px）、`rounded-md`（11px）、`rounded-lg`（12px）、`rounded-full`（980px） |
| 陰影 | `shadow-card` |
| 深色模式 | POC 不支援，`color-scheme: light` 強制鎖定 |

### 禁止

- 元件內硬編碼 hex（`#1d1d1f`、`#0071e3`）— 必須用 token
- 隨意 `px` 值（`padding: 13px`、`margin: 22px`）— 必須對齊 spacing scale
- 同類元件並存兩種實作（例：已有 `Button`，不能在 page 裡直接寫 `<button>`）

---

## 6. 資料流

### API 呼叫

```
Page/Component
  └─► useRole() 讀 role
  └─► apiFetch("/endpoint") → /api/* proxy → FastAPI (localhost:8000)
      ├─► 成功 → setState → 寫入 sessionStorage.last_advice_result
      └─► 錯誤 → ApiError → 畫面錯誤狀態
```

### 問卷提交流程

```
/u/questionnaire
  └─► GET /api/questionnaire/schema
  └─► 使用者填寫
  └─► onSubmit: sessionStorage.pending_advice_request = answers
  └─► POST /api/advise → AdviceResponse
  └─► sessionStorage.last_advice_result = response
  └─► navigate(role === "user" ? "/u/result" : "/coach")
```

---

## 7. 認證流程

POC 不做真實認證：
- `/login` 顯示兩個角色卡片 → 點擊 `setRole("user" | "coach")` → 導向對應首頁
- 「切換角色」= `clearRole()` + navigate `/login`

---

## 8. 部署策略

POC 階段純本機：
- 前端：`npm run dev` → `http://localhost:3000`
- 後端：`uv run uvicorn app.main:app` → `http://localhost:8000`
- Vite `server.proxy` 把 `/api/*` 導向後端

未來 production：
- 前端 `npm run build` → `dist/` → Nginx / Vercel static
- 後端 Docker + Gunicorn
- 前後端同源或 CORS 設定

---

## 9. 效能考量（POC）

- 路由 code split：React Router 7 自動支援 lazy，當前 POC 量小先全打包（bundle < 300KB gzip 可接受）
- 產品圖片：原生 `<img loading="lazy">`；未來量大再考慮 CDN / srcset
- API 回應：LLM 呼叫 10-30 秒，使用 loading spinner + 文案告知

---

## 10. 擴充路線

1. 接 Module 1（貼文生成）：共用 `lib/api.ts` 與 Apple tokens，新增 `/u/posts` 與 `/coach/posts`
2. 加 DB：新增 `/coach/history` 列表頁（使用者歷史結果）
3. 真實認證：OAuth 或 email + password，`RoleContext` 改為 `AuthContext`
4. 深色模式：`@theme` 內新增 dark 變體 + `@media (prefers-color-scheme: dark)`
