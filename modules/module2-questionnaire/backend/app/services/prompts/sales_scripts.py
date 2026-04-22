"""
行銷話術 Prompt 工程模組。

核心函式：
    generate_sales_scripts — 依問卷答案、健康摘要、推薦產品，呼叫 LLM 產出四情境話術
"""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from app.core import LLMClient
from app.schemas.advice import HealthAssessmentSummary, RecommendedProduct, SalesScript
from app.services.prompts.base import PromptContext

logger = logging.getLogger(__name__)

# PII 欄位（在 prompt 中移除）
_PII_FIELD_IDS: frozenset[str] = frozenset({"name", "email", "phone", "referrer", "form_id"})

# 話術 LLM 溫度（比健康研判高，需要一點創意）
_BASE_TEMPERATURE = 0.6

# System prompt（角色定位、情境定義、硬性規則、few-shot 全合一）
_SYSTEM_PROMPT = """\
你是 Synergy 資深教練教練（coach-of-coach），擅長把健康顧問知識轉化為新手教練能照著唸的話術。

【四個話術情境定義】
- opening（開場）：聊天/私訊開頭如何切入健康議題，不壓迫、不直接推銷，自然帶出關心
- objection（異議處理）：針對客戶可能的典型拒絕理由（如「太貴」「沒時間」「不信任」），提供 3 個 Q&A 式回覆要點
- closing（收尾/成交）：引導約商談或下單，不硬推，讓對方感覺是自己做決定
- follow_up（後續跟進）：成交或未成交後的 follow-up 訊息模板，維持關係、保持溫度

【硬性規則】
1. 話術口吻：自然、親切、像朋友；新手教練直接複製貼上就能用
2. 禁止誇大療效、禁止任何醫療承諾、禁止恐嚇式話術（如「不管就會生病」）
3. 禁止一開口就講產品功效或價格
4. 必須緊扣：客戶性別、年齡、具體健康風險、已推薦產品名稱

【字數控制（硬性限制，避免輸出被截斷）】
- 每個 script **嚴格 40~90 字**（太長新手記不住也不實用，系統也會被截）
- taboo **最多 40 字**，1 句即可
- 四個情境總輸出長度控制在 600 字以內

【輸出 JSON 格式】
{"scripts": [{"scenario": "opening|objection|closing|follow_up", "script": "話術文本（20-120 字）", "taboo": "1-2 句提醒或 null"}]}

【Few-shot 範例：45 歲男性 + 體重問題 + PROARGI-9+】（示範字數控制）
{"scripts": [
  {"scenario": "opening", "script": "嗨！前陣子看你分享最近比較累，45 歲前後很多人都感覺體力大不如前。我最近在幫朋友做健康評估，有空輕鬆聊一下？", "taboo": "不要一開口就講產品功效或推薦購買。"},
  {"scenario": "objection", "script": "我懂這個顧慮！你有三高家族史，提早預防比等有狀況再處理輕鬆很多。我有朋友用了 PROARGI-9+ 反應不錯，要不要聽聽？", "taboo": "避免說「保證有效」等承諾式語言。"},
  {"scenario": "closing", "script": "依你目前狀況，建議先從 PROARGI-9+ 調理一個月，許多人第三週就感覺精神變好。這週哪天方便詳細聊？", "taboo": "不要說「現在買最划算」逼單。"},
  {"scenario": "follow_up", "script": "嗨！上次聊到睡眠和體力問題我一直放在心上，整理了一份心血管保養資料，有空傳給你參考，純分享喔！", "taboo": "不要一直催問「你考慮得怎麼樣」。"}
]}

請依據客戶資料與推薦產品，產出符合上述格式的話術 JSON。"""

# Fallback 話術（當 LLM 回傳不足 2 個時補用）
_FALLBACK_SCRIPTS: list[dict[str, Any]] = [
    {
        "scenario": "opening",
        "script": (
            "嗨！最近身體狀況怎麼樣？其實現在很多人都有健康上的一些小問題，"
            "我最近有在幫朋友做一些健康評估，有空的話可以輕鬆聊一下。"
        ),
        "taboo": "不要一開口就提產品，先關心對方狀況才能建立信任。",
    },
    {
        "scenario": "follow_up",
        "script": (
            "嗨！之前我們有聊過健康的話題，我最近整理了一些對你可能有幫助的資料，"
            "純粹分享，沒有任何壓力，你有空的話我傳給你參考看看？"
        ),
        "taboo": "跟進時保持輕鬆語氣，不要催促對方做決定。",
    },
]


# ---------------------------------------------------------------------------
# 內部輔助函式
# ---------------------------------------------------------------------------


def _strip_pii(answers: dict[str, Any]) -> dict[str, Any]:
    """移除 answers 中的 PII 欄位，回傳新 dict（不可變）。"""
    return {k: v for k, v in answers.items() if k not in _PII_FIELD_IDS}


def _format_answers(answers: dict[str, Any], context: PromptContext) -> str:
    """將 answers 轉為可讀 Q/A 條列格式，移除 PII，label 中文化。"""
    clean = _strip_pii(answers)
    lines: list[str] = []
    for field_id, value in clean.items():
        label = context.questionnaire_labels.get(field_id, field_id)
        if isinstance(value, list):
            formatted = "、".join(str(v) for v in value)
        elif value is None:
            formatted = "（未填）"
        else:
            formatted = str(value)
        lines.append(f"- {label}：{formatted}")
    return "\n".join(lines)


def _build_user_prompt(
    answers: dict[str, Any],
    health_summary: HealthAssessmentSummary,
    recommended_products: list[RecommendedProduct],
    context: PromptContext,
    scenarios: tuple[str, ...],
) -> str:
    """建立 user prompt，涵蓋客戶重點、推薦產品、情境請求。"""
    parts: list[str] = [
        "【Section 1：客戶重點】",
        _format_answers(answers, context),
        f"- 整體健康風險等級：{health_summary.overall_level}",
        f"- 主要健康風險：{'、'.join(health_summary.key_risks)}",
        "\n【Section 2：推薦產品清單】",
        *[f"- {p.name}：{p.reason}" for p in recommended_products],
        f"\n【Section 3：請產出以下情境的話術】",
        f"需要的情境：{'、'.join(scenarios)}",
        "請為每個情境各產出一段話術與 taboo 提醒，以 JSON 格式輸出。",
    ]
    return "\n".join(parts)


def _parse_scripts(
    raw: dict[str, Any],
    scenarios: tuple[str, ...],
) -> list[SalesScript]:
    """
    從 LLM 回傳的 dict 解析合法的 SalesScript 列表。

    只保留 scenarios 內的情境；缺少的情境 log warning，不補。
    """
    results: list[SalesScript] = []
    for item in raw.get("scripts", []):
        scenario = item.get("scenario")
        if scenario not in scenarios:
            logger.warning("LLM 回傳未請求的情境: %s，已忽略", scenario)
            continue
        results.append(SalesScript(**item))

    returned = {s.scenario for s in results}
    for scenario in scenarios:
        if scenario not in returned:
            logger.warning("LLM 未回傳請求的情境: %s", scenario)
    return results


def _apply_fallback(scripts: list[SalesScript]) -> list[SalesScript]:
    """若 scripts 不足 2 個，從 _FALLBACK_SCRIPTS 補齊至至少 2 個（不重複情境）。"""
    existing = {s.scenario for s in scripts}
    result = list(scripts)
    for fallback_data in _FALLBACK_SCRIPTS:
        if len(result) >= 2:
            break
        if fallback_data["scenario"] not in existing:
            result.append(SalesScript(**fallback_data))
            existing.add(fallback_data["scenario"])
    return result


# ---------------------------------------------------------------------------
# 主要公開函式
# ---------------------------------------------------------------------------


async def generate_sales_scripts(
    *,
    answers: dict[str, Any],
    health_summary: HealthAssessmentSummary,
    recommended_products: list[RecommendedProduct],
    context: PromptContext,
    client: LLMClient,
    model: str | None = None,
    scenarios: tuple[str, ...] = ("opening", "objection", "closing", "follow_up"),
) -> list[SalesScript]:
    """
    依問卷答案、健康摘要、推薦產品，呼叫 LLM 產出行銷話術。

    流程：
    1. 建立 system prompt（角色、情境定義、規則、few-shot）
    2. 建立 user prompt（客戶重點、推薦產品、情境請求）
    3. 呼叫 client.complete_json（temperature=0.6）
    4. 解析為 list[SalesScript]；script < 20 字觸發重試
    5. 兩次後仍不足 min_required → fallback 補齊

    Parameters
    ----------
    answers:
        問卷填答 dict，key 為 field_id。PII 欄位自動過濾。
    health_summary:
        由 3.1 產出的 HealthAssessmentSummary，提供風險等級與關鍵風險。
    recommended_products:
        由 3.2 產出的推薦產品列表，話術會緊扣產品名稱。
    context:
        包含 label 映射、教練等級、語系的上下文。
    client:
        LLMClient 實例。
    model:
        可選模型覆蓋，如 "gemini/gemini-2.5-pro"。
    scenarios:
        要求產出的情境 tuple，預設全四個。

    Returns
    -------
    list[SalesScript]
        解析成功的話術列表。請求 >= 2 個情境時至少回傳 2 個（不足由 fallback 補齊）。
    """
    user_prompt = _build_user_prompt(
        answers=answers,
        health_summary=health_summary,
        recommended_products=recommended_products,
        context=context,
        scenarios=scenarios,
    )
    response_schema = {
        "type": "object",
        "properties": {"scripts": {"type": "array", "items": SalesScript.model_json_schema()}},
        "required": ["scripts"],
    }
    min_required = min(2, len(scenarios))
    last_valid: list[SalesScript] = []

    for attempt in range(2):
        temperature = _BASE_TEMPERATURE + attempt * 0.1
        raw: dict[str, Any] = await client.complete_json(
            system=_SYSTEM_PROMPT,
            user=user_prompt,
            response_schema=response_schema,
            model=model,
            temperature=temperature,
        )
        try:
            scripts = _parse_scripts(raw, scenarios)
            if scripts:
                last_valid = scripts
            if len(scripts) >= min_required:
                return scripts
            logger.warning(
                "第 %d 次嘗試：只取得 %d 個合法話術，預期至少 %d 個",
                attempt + 1,
                len(scripts),
                min_required,
            )
        except ValidationError as exc:
            logger.warning("SalesScript validation failed (attempt %d/2): %s", attempt + 1, exc)

    if min_required >= 2:
        return _apply_fallback(last_valid)
    return last_valid
