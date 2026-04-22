# Synergy AI POC — 甘特圖

> **週期：** 2026-04-28 ~ 2026-07-27（13 週）
> **格式：** Mermaid Gantt（GitHub / VS Code Mermaid preview 皆可渲染）

---

## 總覽甘特圖（Phase 層級）

```mermaid
gantt
    title Synergy AI POC 開發時程（大節點）
    dateFormat  YYYY-MM-DD
    axisFormat  %m-%d
    excludes    weekends

    section Phase 0 啟動
    POC 啟動與共通基礎         :milestone, m1, 2026-05-04, 0d
    Kick-off / 技術決策 / 共通 schema :p0, 2026-04-28, 5d

    section Phase 1 模組 2 問卷
    健康問卷 Web 化            :p1a, after p0, 2d
    問卷結果寄送              :p1b, after p1a, 2d
    名單標籤分級              :p1c, after p1b, 3d
    分流規則引擎              :p1d, after p1c, 4d
    模組 2 整合驗收            :p1e, after p1d, 2d
    M2 模組 2 POC 完成         :milestone, m2, after p1e, 0d

    section Phase 2 模組 1 獲客
    貼文文案 AI 生成           :p2a, after p1e, 3d
    貼文圖片 AI 生成           :p2b, after p2a, 3d
    自動排程與發布             :p2c, after p2b, 3d
    SEO 內容頁                :p2d, after p2a, 3d
    模組 1 整合驗收            :p2e, after p2c, 2d
    M3 模組 1 POC 完成         :milestone, m3, after p2e, 0d

    section Phase 3 模組 6 團隊
    模組 6 骨架與資料模型       :p3a, after p2e, 3d
    MEGA 資料串接              :p3b, after p3a, 3d
    月目標設定                :p3c, after p3b, 3d
    績效看板                  :p3d, after p3c, 4d
    團隊儀表板                :p3e, after p3d, 3d
    培訓追蹤                  :p3f, after p3b, 2d
    落後提醒告警引擎           :p3g, after p3c, 2d
    模組 6 整合驗收            :p3h, after p3e, 2d
    M4 模組 6 POC 完成         :milestone, m4, after p3h, 0d

    section Phase 4 整合交付
    三模組資料流串接           :p4a, after p3h, 3d
    全局 E2E 測試              :p4b, after p4a, 2d
    UAT 與 Bug Fix            :p4c, after p4b, 3d
    POC 環境部署              :p4d, after p4c, 2d
    Demo 準備與交付            :p4e, after p4d, 1d
    M5 POC Demo 交付          :milestone, m5, after p4e, 0d
```

---

## 週次時程表（對照用）

| 週次 | 日期範圍 | Phase | 主要工作 |
| :--- | :--- | :--- | :--- |
| W1 | 04-28 ~ 05-04 | Phase 0 | Kick-off、認證、UI 風格、DB schema |
| W2 | 05-05 ~ 05-11 | Phase 1 | 問卷 Web 化、結果寄送 |
| W3 | 05-12 ~ 05-18 | Phase 1 | 名單分級、分流規則（上） |
| W4 | 05-19 ~ 05-25 | Phase 1 | 分流規則（下）、整合驗收 **M2** |
| W5 | 05-26 ~ 06-01 | Phase 2 | AI 文案生成、AI 圖片生成（上） |
| W6 | 06-02 ~ 06-08 | Phase 2 | AI 圖片生成（下）、自動排程 |
| W7 | 06-09 ~ 06-15 | Phase 2 | SEO 內容頁、整合驗收 **M3** |
| W8 | 06-16 ~ 06-22 | Phase 3 | 模組 6 骨架、MEGA 串接 |
| W9 | 06-23 ~ 06-29 | Phase 3 | 月目標、績效看板（上） |
| W10 | 06-30 ~ 07-06 | Phase 3 | 績效看板（下）、團隊儀表板、培訓追蹤 |
| W11 | 07-07 ~ 07-13 | Phase 3 | 落後提醒、整合驗收 **M4** |
| W12 | 07-14 ~ 07-20 | Phase 4 | 三模組串接、E2E、UAT |
| W13 | 07-21 ~ 07-27 | Phase 4 | Bug Fix、部署、Demo 交付 **M5** |

---

## 關鍵里程碑

| 編號 | 日期 | 里程碑 | 交付產物 |
| :--- | :--- | :--- | :--- |
| **M1** | 2026-05-04 | POC 啟動完成 | 共通基礎、ADR、CI/CD |
| **M2** | 2026-05-25 | 模組 2（問卷）POC 完成 | 問卷→分級→分流可走通 |
| **M3** | 2026-06-15 | 模組 1（獲客）POC 完成 | AI 生文→排程→發佈可走通 |
| **M4** | 2026-07-13 | 模組 6（團隊）POC 完成 | 目標→看板→告警可走通 |
| **M5** | 2026-07-27 | POC Demo 交付 | 整合 Demo、部署、交付文件 |

---

## 資源配置視圖（人月）

```mermaid
gantt
    title 人力配置（假設 2 全端 + 0.5 AI + 0.3 PM）
    dateFormat YYYY-MM-DD
    axisFormat %m-%d

    section 全端 A
    模組 2 補強               :a1, 2026-05-05, 15d
    模組 1 補強               :a2, after a1, 15d
    整合/UAT                 :a3, 2026-07-14, 10d

    section 全端 B
    共通基礎                 :b1, 2026-04-28, 5d
    模組 6 骨架＋目標         :b2, 2026-06-16, 15d
    模組 6 看板＋告警         :b3, after b2, 10d
    整合/UAT                 :b4, 2026-07-14, 10d

    section AI 工程師 (50%)
    模組 2 LLM 調校          :c1, 2026-05-05, 10d
    模組 1 生成引擎          :c2, 2026-05-26, 15d
    模組 6 告警規則          :c3, 2026-07-01, 5d

    section PM/QA (30%)
    需求釐清                 :d1, 2026-04-28, 5d
    UAT 驗收 (M2)            :d2, 2026-05-22, 3d
    UAT 驗收 (M3)            :d3, 2026-06-12, 3d
    UAT 驗收 (M4)            :d4, 2026-07-10, 3d
    POC 交付                 :d5, 2026-07-21, 5d
```

---

## 使用方式

- **GitHub / GitLab：** 直接瀏覽本檔即可看到 Mermaid 圖
- **VS Code：** 安裝 *Markdown Preview Mermaid Support* 擴充
- **匯出 PNG：** 用 [Mermaid Live Editor](https://mermaid.live/) 貼上程式碼匯出
- **變更時程：** 僅需改 `dateFormat` 與各 task 的起訖；週次表隨之手動同步
