"""
輸出契約 Pydantic v2 schemas。

定義 /advise API 的請求與回應結構，供 LLM 輸出解析與前端顯示使用。
所有 model 採用 extra='forbid' 嚴格拒絕多餘欄位，確保資料契約穩定。

匯出項目：
    AdviceRequest        — 請求體（問卷答案 + 語系 + 教練等級）
    AdviceResponse       — 回應體（四段結構化建議）
    HealthAssessmentSummary — 健康研判摘要
    RecommendedProduct   — 推薦產品單項
    SalesScript          — 行銷話術單項
    NextAction           — 下一步行動單項
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# ---------------------------------------------------------------------------
# 子模型
# ---------------------------------------------------------------------------


class RecommendedProduct(BaseModel):
    """推薦產品資訊，對應 products.json 中的 SKU。"""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(
        ...,
        min_length=1,
        description="產品 SKU，需與 products.json 中的 sku 欄位一致",
    )
    name: str = Field(
        ...,
        description="產品名稱（繁中）",
    )
    reason: str = Field(
        ...,
        min_length=10,
        description="為何推薦此產品的說明（繁中，至少 10 字，供教練向客戶解釋用）",
    )
    image_url: HttpUrl | None = Field(
        default=None,
        description="產品圖片 URL，若無對應圖片則為 null",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="LLM 對此推薦的信心分數，0.0 ~ 1.0",
    )


class SalesScript(BaseModel):
    """行銷話術，依場景分類供新手教練使用。"""

    model_config = ConfigDict(extra="forbid")

    scenario: Literal["opening", "objection", "closing", "follow_up"] = Field(
        ...,
        description=(
            "話術使用場景："
            "opening=開場破冰、"
            "objection=處理異議、"
            "closing=收尾成交、"
            "follow_up=後續追蹤"
        ),
    )
    script: str = Field(
        ...,
        min_length=20,
        description="話術文本（繁中，至少 20 字），可直接對客戶說的語句",
    )
    taboo: str | None = Field(
        default=None,
        description="話術禁忌與提醒，提醒教練避免的說法或行為",
    )


class NextAction(BaseModel):
    """下一步行動建議，指引教練在諮詢後該採取什麼行動。"""

    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "schedule_consultation",
        "offer_trial",
        "escalate_to_senior",
        "send_educational_content",
        "hold_for_warming",
    ] = Field(
        ...,
        description=(
            "建議行動類型："
            "schedule_consultation=安排 2:1 商談、"
            "offer_trial=提供產品試用、"
            "escalate_to_senior=轉介資深上線、"
            "send_educational_content=發送衛教資料、"
            "hold_for_warming=暫緩，持續暖身"
        ),
    )
    why: str = Field(
        ...,
        min_length=10,
        description="建議此行動的原因（繁中，至少 10 字）",
    )
    priority: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="執行優先級：high=本週內、medium=本月內、low=視情況",
    )


class HealthAssessmentSummary(BaseModel):
    """健康研判摘要，供教練快速掌握客戶風險輪廓。"""

    model_config = ConfigDict(extra="forbid")

    key_risks: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="關鍵健康風險列表（繁中），1 ~ 5 項",
    )
    overall_level: Literal["low", "medium", "high"] = Field(
        ...,
        description="整體健康風險等級：low=低風險、medium=中風險、high=高風險",
    )
    narrative: str = Field(
        ...,
        min_length=30,
        description="3-5 句自然語言摘要（繁中），供教練向客戶說明健康狀況用",
    )
    disclaimers: list[str] = Field(
        default_factory=lambda: [
            "本評估僅供健康諮詢參考，非醫療診斷。"
            "若有明顯不適或正在治療中，請優先遵循醫師建議。"
        ],
        description="免責聲明列表，預設含一則標準醫療免責聲明",
    )


# ---------------------------------------------------------------------------
# 根模型
# ---------------------------------------------------------------------------


class AdviceResponse(BaseModel):
    """
    /advise API 回應根節點。

    包含四段結構化建議，由 LLM 依問卷填答產出，
    供新手教練在健康諮詢後使用。
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "summary": {
                    "key_risks": ["睡眠品質差", "免疫力低下"],
                    "overall_level": "medium",
                    "narrative": (
                        "根據您的問卷填答，您目前有睡眠品質不佳與免疫力下降等健康隱患。"
                        "建議優先改善睡眠習慣並補充必要營養素。"
                        "整體健康風險為中等，需持續關注後續變化。"
                    ),
                    "disclaimers": [
                        "本評估僅供健康諮詢參考，非醫療診斷。"
                        "若有明顯不適或正在治療中，請優先遵循醫師建議。"
                    ],
                },
                "recommended_products": [
                    {
                        "sku": "PRD-001",
                        "name": "超級維他命 C",
                        "reason": "此客戶有明顯的免疫力不足症狀，維他命 C 可強化防禦力",
                        "image_url": None,
                        "confidence": 0.85,
                    }
                ],
                "sales_scripts": [
                    {
                        "scenario": "opening",
                        "script": "您好，根據您填寫的健康問卷，我發現您最近睡眠品質不佳，這讓我很擔心。",
                        "taboo": None,
                    },
                    {
                        "scenario": "closing",
                        "script": "感謝您今天的時間，我建議您先試用一個月看看效果如何。",
                        "taboo": None,
                    },
                ],
                "next_actions": [
                    {
                        "action": "schedule_consultation",
                        "why": "客戶有多項中高風險指標，需安排專業諮詢",
                        "priority": "high",
                    }
                ],
            }
        },
    )

    summary: HealthAssessmentSummary = Field(
        ...,
        description="健康研判摘要，含風險列表、等級與自然語言描述",
    )
    recommended_products: list[RecommendedProduct] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="推薦產品組合，1 ~ 5 個，依信心分數排序",
    )
    sales_scripts: list[SalesScript] = Field(
        ...,
        min_length=2,
        description="行銷話術建議，至少涵蓋開場與一個其他場景",
    )
    next_actions: list[NextAction] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="下一步行動建議，1 ~ 3 個，依優先級排序",
    )


class AdviceRequest(BaseModel):
    """
    /advise API 請求根節點。

    接收問卷填答結果，由前端或 API 呼叫端提交。
    answers 的 key 為 questionnaire.json 定義的 field_id，
    value 支援多型別以對應不同題型。
    """

    model_config = ConfigDict(extra="forbid")

    answers: dict[str, str | int | float | bool | list[str] | None] = Field(
        ...,
        description=(
            "問卷填答結果，key 為 field_id（對應 questionnaire.json），"
            "value 依題型可為字串、整數、浮點數、布林值、字串列表或 null"
        ),
    )
    locale: Literal["zh-TW", "en"] = Field(
        default="zh-TW",
        description="回應語系：zh-TW=繁體中文（預設）、en=英文",
    )
    coach_level: Literal["new", "experienced"] = Field(
        default="new",
        description="教練等級：new=新手（話術較詳細）、experienced=資深（簡潔版）",
    )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def get_advice_response_schema_json(indent: int = 2) -> str:
    """
    回傳 AdviceResponse 的 JSON schema 字串。

    供 LLM prompt 使用，讓模型知道需要產出的 JSON 結構。

    Args:
        indent: JSON 縮排空格數，預設 2。

    Returns:
        格式化後的 JSON schema 字串。
    """
    return json.dumps(AdviceResponse.model_json_schema(), ensure_ascii=False, indent=indent)
