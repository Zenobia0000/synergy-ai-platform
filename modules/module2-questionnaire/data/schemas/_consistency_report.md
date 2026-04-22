# 問卷一致性報告

產生時間：2026-04-21T15:35:08.994504+08:00

## 概要

| 指標 | 數值 |
|------|------|
| 主版本欄位總數（xlsx） | 56 |
| Apps Script 題目總數 | 60 |
| 交集數（含正規化比對） | 34 |
| 主版本被 AS 涵蓋率 | 60.7% |

## 差異詳情

### 主版本獨有（xlsx 有、Apps Script 無）

- 主要壓力來源－其他說明
- 其他想補充的內容
- 壓力相關身體感受－其他說明
- 您目前願意為健康改善投入的程度
- 您覺得自己最難調整的是
- 日常飲食型態－其他說明
- 是否曾接受手術，或有重要家族病史？
- 是否曾被醫師告知有以下情況
- 最近一次健康檢查是否有異常指標？
- 最難調整項目－其他說明
- 本次最想優先改善的問題
- 本次最想優先改善的問題－其他說明
- 消化狀況－其他說明
- 目前是否有長期使用的藥物或保健食品
- 目前最困擾您的3個問題
- 若健康狀態改善，您最希望生活中先有哪一個改變？
- 若有喝咖啡，每天約幾杯？
- 請填寫藥物或保健食品內容
- 請簡要說明異常項目
- 過去2週內常有以下情況
- 醫療狀況－其他說明
- 體態感受－其他說明

### Apps Script 獨有（Apps Script 有、xlsx 無）

- 1. 本次最想優先改善的問題（可複選）
- 10. 水分與其他習慣
- 11. 日常活動量
- 12. 是否曾被醫師告知有以下情況？（可複選）
- 13-補充. 若有藥物或保健食品，請說明內容
- 13. 目前是否有長期使用的藥物或保健食品？
- 14. 是否曾接受手術，或有重要家族病史？（請說明）
- 15-補充. 若有異常指標，請說明
- 15. 最近一次健康檢查是否有異常指標？
- 16. 目前最困擾您的 3 個問題
- 17. 您目前願意為健康改善投入的程度
- 18. 您覺得自己最難調整的是
- 2. 若健康狀態改善，您最希望生活中先有哪一個改變？
- 3. 壓力與身心感受
- 4. 睡眠狀況
- 5. 消化與進食後感受
- 6. 循環相關感受
- 7. 水分代謝與體態感受
- 8. 排便習慣
- 9. 飲食習慣
- 一、基本資料
- 三、近期身體感受
- 二、健康目標
- 五、健康與醫療紀錄
- 六、補充資訊
- 四、生活習慣與營養攝取

---

## 手動抽檢

產生時間：2026-04-21T15:35:08.996504+08:00

### 代表性欄位抽檢（3 個）

**欄位：`gender`（性別）**

```json
{
  "field_id": "gender",
  "label": "性別",
  "type": "single_choice",
  "required": true,
  "options": [
    {
      "value": "男",
      "label": "男"
    },
    {
      "value": "女",
      "label": "女"
    },
    {
      "value": "其他",
      "label": "其他"
    },
    {
      "value": "不願透露",
      "label": "不願透露"
    }
  ],
  "default": null,
  "help_text": "Google 表單可設為單選",
  "condition": null,
  "pii": false,
  "order": 7,
  "min": null,
  "max": null,
  "unit": null
}
```

**欄位：`current_weight_kg`（目前體重（kg））**

```json
{
  "field_id": "current_weight_kg",
  "label": "目前體重（kg）",
  "type": "number",
  "required": true,
  "options": null,
  "default": null,
  "help_text": "建議限制數字格式",
  "condition": null,
  "pii": false,
  "order": 9,
  "min": null,
  "max": null,
  "unit": "kg"
}
```

**欄位：`medical_history`（是否曾被醫師告知有以下情況）**

```json
{
  "field_id": "medical_history",
  "label": "是否曾被醫師告知有以下情況",
  "type": "multi_choice",
  "required": false,
  "options": [
    {
      "value": "胃食道逆流",
      "label": "胃食道逆流"
    },
    {
      "value": "消化性潰瘍",
      "label": "消化性潰瘍"
    },
    {
      "value": "痔瘡",
      "label": "痔瘡"
    },
    {
      "value": "過敏體質",
      "label": "過敏體質"
    },
    {
      "value": "蕁麻疹",
      "label": "蕁麻疹"
    },
    {
      "value": "氣喘",
      "label": "氣喘"
    },
    {
      "value": "過敏性鼻炎",
      "label": "過敏性鼻炎"
    },
    {
      "value": "高血壓",
      "label": "高血壓"
    },
    {
      "value": "血糖異常",
      "label": "血糖異常"
    },
    {
      "value": "肝功能異常",
      "label": "肝功能異常"
    },
    {
      "value": "腎功能異常",
      "label": "腎功能異常"
    },
    {
      "value": "婦科相關問題",
      "label": "婦科相關問題"
    },
    {
      "value": "乳房相關問題",
      "label": "乳房相關問題"
    },
    {
      "value": "其他",
      "label": "其他"
    },
    {
      "value": "無",
      "label": "無"
    }
  ],
  "default": null,
  "help_text": "可複選",
  "condition": null,
  "pii": false,
  "order": 1,
  "min": null,
  "max": null,
  "unit": null
}
```

### 產品圖片 URL 抽檢（5 個）

| SKU | 名稱 | image_match_confidence | URL 前綴驗證 |
|-----|------|------------------------|------------|
| 96371 | 普精耐粉末食品 (PROARGI-9+) | null (未匹配) | null |
| 23424 | 紅色能量隨身包 (SYNERBEET) | 0.900 | ✓ |
| 23151 | 威特立能量補給飲品 (VITALIFT) | 0.900 | ✓ |
| 23711 | 倍然膠囊 (DOUBLE BURN) | 0.867 | ✓ |
| 23431 | 普益康隨身包 (PROGUARD) | 0.900 | ✓ |

> URL 驗證基準：`https://twprod.synergyworldwide.com/` 開頭視為合規。

### 小結

- PII 欄位標註：`name`、`email`、`referrer` 已標 `pii: true`
- 其他 PII 候選（phone、mobile、birthday 等）在本版問卷中不存在，預設集合已備妥
- 圖片 URL 均以 `https://twprod.synergyworldwide.com/` 開頭（或 null）
