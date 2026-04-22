# 前端架構規範 - Personal Content Distributor v2

> **版本:** v1.0 | **更新:** 2026-03-19 | **狀態:** 草稿

---

## 第 1 部分: 架構目標

| 維度 | 目標 | 衡量指標 |
| :--- | :--- | :--- |
| **效能** | 頁面載入 < 2s | LCP < 2.5s, FID < 100ms |
| **可用性** | 直覺操作，最少點擊完成發佈 | 任務完成步驟數 |
| **可維護性** | 一人可持續迭代 | 檔案 < 400 行、函式 < 50 行 |
| **可靠性** | 操作不丟失資料 | 表單有自動儲存/確認 |

---

## 第 2 部分: 技術選型

| 層級 | 職責 | 技術 |
| :--- | :--- | :--- |
| 感知層 | 渲染 UI、視覺一致性 | React 18 + shadcn/ui + Tailwind CSS |
| 互動層 | 使用者輸入、路由導航 | React Router v6 + React Hook Form + Zod |
| 狀態層 | Server State 管理 | React Query (TanStack Query) |
| 通訊層 | API 呼叫與快取 | fetch / axios + React Query |
| 基礎設施 | 建置與品質 | Vite + Vitest + Playwright |

### 系統化分層

```
用戶感知層    -- shadcn/ui 元件、Tailwind 樣式
互動邏輯層    -- React Hook Form 表單、React Router 路由
狀態管理層    -- React Query (server state)、useState (local state)
資料通訊層    -- API Client (fetch 封裝)、型別定義
基礎設施層    -- Vite 建置、Vitest 測試、ESLint 檢查
```

---

## 第 3 部分: 設計系統

### shadcn/ui 元件庫

本專案使用 shadcn/ui 作為基礎元件庫，已安裝的元件：

| 類別 | 元件 |
| :--- | :--- |
| 表單 | Button, Input, Label, Select, Checkbox, Switch, Calendar, Form |
| 回饋 | Toast (Sonner), Alert, Dialog, Alert Dialog, Progress |
| 導航 | Navigation Menu, Tabs, Breadcrumb, Pagination |
| 資料展示 | Card, Badge, Avatar, Table, Accordion, Tooltip |
| 佈局 | Separator, Scroll Area, Resizable Panels, Drawer |
| 圖表 | Recharts (Chart 元件) |

### 自定義業務元件

| 元件 | 用途 | 位置 |
| :--- | :--- | :--- |
| `ContentCard` | 貼文卡片顯示 | `components/ContentCard.tsx` |
| `StatusBadge` | 發佈狀態標記 | `components/StatusBadge.tsx` |
| `PlatformTag` | 平台標籤 (FB/IG/X/LINE) | `components/PlatformTag.tsx` |
| `MetricCard` | 監控指標卡片 | `components/MetricCard.tsx` |
| `ReplyItem` | 回覆內容項目 | `components/ReplyItem.tsx` |
| `AppSidebar` | 側邊欄導航 | `components/AppSidebar.tsx` |
| `Layout` | 頁面佈局框架 | `components/Layout.tsx` |

### 設計令牌

使用 Tailwind CSS 配置（`tailwind.config.ts`）管理：

| 類別 | 說明 |
| :--- | :--- |
| 色彩 | shadcn/ui CSS 變數 (--primary, --secondary, --destructive 等) |
| 字體 | 系統字體堆疊 |
| 間距 | Tailwind 預設 (4px 基礎單位) |
| 圓角 | shadcn/ui 預設 (--radius) |

---

## 第 4 部分: 頁面架構

### 路由表

| 路由 | 頁面元件 | 職責 |
| :--- | :--- | :--- |
| `/` | `ContentManagement` | 貼文列表管理（篩選、排序、狀態總覽） |
| `/create` | `CreateContent` | 建立/編輯貼文（表單、平台選擇、排程） |
| `/monitor` | `MonitorDashboard` | 監控儀表板（互動數據、回覆彙整） |
| `/settings` | `SettingsPage` | 系統設定（平台連結、通知偏好） |
| `*` | `NotFound` | 404 頁面 |

### 頁面資料流

```
ContentManagement
  └─ GET /api/v1/contents (React Query, refetchInterval: 10s)
  └─ 顯示 ContentCard 列表
  └─ 點擊 → /create?id=xxx (編輯)

CreateContent
  └─ React Hook Form + Zod 驗證
  └─ POST /api/v1/contents (建立)
  └─ PUT /api/v1/contents/:id (更新)
  └─ 成功 → 導向 /

MonitorDashboard
  └─ GET /api/v1/monitor/dashboard (React Query)
  └─ GET /api/v1/monitor/contents/:id (詳情)
  └─ Recharts 圖表渲染
```

---

## 第 5 部分: 狀態管理策略

### 狀態分類

| 類型 | 管理方式 | 範例 |
| :--- | :--- | :--- |
| Server State | React Query | 貼文列表、監控數據、發佈狀態 |
| Form State | React Hook Form | 貼文編輯表單 |
| UI State | useState | Modal 開關、篩選條件、排序 |
| URL State | React Router | 頁面路由、查詢參數 |
| Theme | next-themes | 深色/淺色模式 |

### React Query 配置

```typescript
// 全域預設
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,        // 30 秒內不重新取得
      refetchOnWindowFocus: true, // 視窗聚焦時重新取得
      retry: 2,                  // 失敗重試 2 次
    },
  },
});

// 貼文列表 (需要即時更新)
useQuery({
  queryKey: ['contents', filters],
  queryFn: () => contentApi.list(filters),
  refetchInterval: 10_000, // 每 10 秒輪詢
});

// 監控數據 (可接受較長快取)
useQuery({
  queryKey: ['monitor', contentId],
  queryFn: () => monitorApi.get(contentId),
  staleTime: 60_000, // 1 分鐘快取
});
```

---

## 第 6 部分: API 通訊層

### API Client 設計

```
src/services/
├── api-client.ts       # 基礎 fetch 封裝 (baseURL, headers, error handling)
├── content-api.ts      # 內容相關 API
├── monitor-api.ts      # 監控相關 API
└── types.ts            # API 回應型別 (自動從 OpenAPI 產生)
```

### 統一回應格式

```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
  meta?: {
    total: number;
    page: number;
    limit: number;
  };
}
```

### 錯誤處理策略

| 錯誤類型 | 處理方式 |
| :--- | :--- |
| 網路錯誤 | Toast 提示 + React Query 自動重試 |
| 4xx 驗證錯誤 | 表單欄位標記錯誤 |
| 401 未認證 | 重導登入頁 (未來) |
| 5xx 伺服器錯誤 | Toast 提示 + 錯誤邊界 |

---

## 第 7 部分: 效能策略

### 載入優化

| 策略 | 實作 |
| :--- | :--- |
| Code Splitting | React.lazy + Suspense (路由級) |
| 圖片優化 | 延遲載入、適當尺寸 |
| Bundle 分析 | `rollup-plugin-visualizer` |
| 快取 | React Query 快取 + HTTP Cache |

### 執行時優化

| 策略 | 適用場景 |
| :--- | :--- |
| `React.memo` | 純展示元件 (ContentCard, StatusBadge) |
| `useMemo` | 計算密集的篩選/排序結果 |
| `useCallback` | 傳遞給子元件的 handler |
| 虛擬列表 | 貼文列表超過 100 筆 |

---

## 第 8 部分: 測試策略

| 類型 | 工具 | 覆蓋率目標 | 測試內容 |
| :--- | :--- | :--- | :--- |
| 單元 | Vitest | 80%+ | 工具函式、Custom Hooks |
| 元件 | Testing Library | 核心元件 | ContentCard、StatusBadge 渲染與互動 |
| E2E | Playwright | 關鍵流程 | 建立貼文 → 發佈 → 查看狀態 |

---

## 第 9 部分: 開發檢查清單

### 新功能上線前

- [ ] TypeScript 無錯誤 (`npm run build`)
- [ ] 單元/元件測試通過 (`npm run test`)
- [ ] ESLint 無警告 (`npm run lint`)
- [ ] 響應式設計驗證 (md / lg 斷點)
- [ ] 錯誤邊界覆蓋
- [ ] Loading / Empty / Error 三態處理
- [ ] Code Review 通過
