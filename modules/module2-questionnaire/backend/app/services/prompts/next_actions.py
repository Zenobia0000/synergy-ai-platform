"""
下一步行動建議 Prompt 工程模組。

核心函式：
    generate_next_actions — 依問卷答案、健康摘要、推薦產品呼叫 LLM，
                            產出 list[NextAction]，建議教練下一步該做什麼。
"""

from __future__ import annotations

import logging
from typing import Any

from app.core import LLMClient
from app.schemas import HealthAssessmentSummary, NextAction, RecommendedProduct
from app.services.prompts.base import PromptContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常數：PII 欄位（在 prompt 中移除）
# ---------------------------------------------------------------------------

_PII_FIELD_IDS: frozenset[str] = frozenset(
    {
        "name",
        "email",
        "phone",
        "referrer",
        "form_id",
    }
)

# ---------------------------------------------------------------------------
# 常數：合法 action 集合
# ---------------------------------------------------------------------------

_VALID_ACTIONS: frozenset[str] = frozenset(
    {
        "schedule_consultation",
        "offer_trial",
        "escalate_to_senior",
        "send_educational_content",
        "hold_for_warming",
    }
)

# ---------------------------------------------------------------------------
# 常數：Few-shot 範例（嵌入 system prompt）
# ---------------------------------------------------------------------------

_FEW_SHOT_EXAMPLES = """
【範例一：高意願客戶】
客戶情境：45 歲男性，有明確體重管理目標，預算充足，無特殊疾病史，問卷填答完整。
健康風險：中等（輕微體重過重）
建議輸出：
{
  "actions": [
    {
      "action": "schedule_consultation",
      "why": "您填答中顯示有明確的體重管理目標且預算合理，資訊齊全，適合立即安排 2:1 深度商談推進決策",
      "priority": "high"
    },
    {
      "action": "send_educational_content",
      "why": "商談前先發送體重管理相關衛教資料，讓客戶對產品有初步了解，提升商談效率",
      "priority": "low"
    }
  ]
}

【範例二：懷疑型客戶】
客戶情境：32 歲女性，有睡眠問題但對保健品效果存疑，預算有限，目前還在蒐集資訊。
健康風險：低（偶爾疲勞）
建議輸出：
{
  "actions": [
    {
      "action": "send_educational_content",
      "why": "客戶填答顯示仍在資訊蒐集階段，尚未建立信任感，先推送睡眠相關衛教內容與成功案例見證",
      "priority": "medium"
    },
    {
      "action": "offer_trial",
      "why": "針對客戶對效果的疑慮，提供免費試用品讓其親身體驗，降低購買門檻",
      "priority": "medium"
    }
  ]
}
"""

# ---------------------------------------------------------------------------
# 常數：System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """你是 Synergy 資深營運教練，幫新手教練判斷下一步該做什麼。

【五種行動的語意定義】

1. schedule_consultation（安排 2:1 商談）
   適用時機：客戶意願明顯、資訊填答齊全、信任度已建立。
   條件參考：有明確健康痛點 + 合理預算 + 無重大疑慮 → 優先推薦（high）

2. offer_trial（提供試用品）
   適用時機：客戶猶豫不決、想先體驗效果、對產品尚不信任。
   條件參考：有健康需求但懷疑效果，透過試用降低購買門檻 → medium

3. escalate_to_senior（轉請上線/資深教練接手）
   適用時機：新手能力不足、客戶情況複雜、有醫療疑慮（慢性病、正在服藥、高齡、懷孕）。
   條件參考：健康風險高、key_risks 含慢性病/正在服藥/高齡/懷孕等字眼 → high
   重要：若客戶有慢性病史或正在服藥，強烈建議包含此行動。

4. send_educational_content（推送衛教/見證內容）
   適用時機：客戶還在認知階段、需要培養信任、對產品缺乏了解。
   條件參考：還在蒐集資訊、尚未建立信任感 → medium

5. hold_for_warming（先持續溫存不主動推進）
   適用時機：時機未到、預算明顯不足、短期內無購買意願。
   條件參考：填答避重就輕、預算敏感、時機不成熟 → low

【硬性規則】
- 每個行動的 why 必須具體引用客戶問卷或健康摘要的事實（例：因您提到 XX 狀況 + 尚未決定）
- 最多輸出 3 個行動，由 LLM 自行依客戶狀況排序
- 禁止建議列舉外的行動（例：加好友、發限時優惠、送折扣碼）
- 若健康風險等級為 high 或 key_risks 含「慢性病」「高齡」「懷孕」「正在服藥」→ 強烈建議包含 escalate_to_senior

【字數控制（硬性限制，避免輸出被截斷）】
- **最多 3 個 action**（不要貪多）
- 每個 why **20~50 字**（一句話說清楚關鍵判斷依據，不要長篇大論）
- 總輸出長度控制在 300 字以內

【輸出格式（嚴格 JSON）】
{
  "actions": [
    {
      "action": "schedule_consultation | offer_trial | escalate_to_senior | send_educational_content | hold_for_warming",
      "why": "具體說明原因，引用客戶資訊，至少 10 字",
      "priority": "high | medium | low"
    }
  ]
}

【Few-shot 範例】
""" + _FEW_SHOT_EXAMPLES

# ---------------------------------------------------------------------------
# 內部輔助函式
# ---------------------------------------------------------------------------


def _build_user_prompt(
    answers: dict[str, Any],
    health_summary: HealthAssessmentSummary,
    recommended_products: list[RecommendedProduct],
    context: PromptContext,
    max_actions: int,
) -> str:
    """
    建立 user prompt。

    包含：
    - 客戶問卷關鍵填答（移除 PII）
    - 健康摘要（key_risks + overall_level + narrative 前半段）
    - 推薦產品名稱列表
    - 輸出要求
    """
    lines: list[str] = ["【客戶問卷關鍵填答】"]

    for field_id, value in answers.items():
        # 過濾 PII
        if field_id in _PII_FIELD_IDS:
            continue

        label = context.questionnaire_labels.get(field_id, field_id)

        if isinstance(value, list):
            formatted_value = "、".join(str(v) for v in value)
        elif value is None:
            formatted_value = "（未填）"
        else:
            formatted_value = str(value)

        lines.append(f"- {label}：{formatted_value}")

    # 健康摘要
    lines.append("\n【健康評估摘要】")
    lines.append(f"- 整體風險等級：{health_summary.overall_level}")
    lines.append("- 主要健康風險：")
    for risk in health_summary.key_risks:
        lines.append(f"  • {risk}")

    # narrative 前半段（前 100 字）
    narrative_excerpt = health_summary.narrative[:100]
    lines.append(f"- 摘要說明（節錄）：{narrative_excerpt}…")

    # 推薦產品
    lines.append("\n【已推薦產品】")
    if recommended_products:
        for product in recommended_products:
            lines.append(f"- {product.name}（SKU: {product.sku}）")
    else:
        lines.append("- （無推薦產品）")

    # 輸出要求
    lines.append(f"\n請根據以上資訊，輸出 1 至 {max_actions} 個最適合的下一步行動建議（JSON 格式）。")

    return "\n".join(lines)


def _parse_actions_from_raw(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """從 LLM 回傳的 raw dict 中提取 actions 列表。"""
    actions = raw.get("actions", [])
    if not isinstance(actions, list):
        return []
    return actions


def _filter_valid_actions(
    raw_actions: list[dict[str, Any]],
) -> tuple[list[NextAction], list[str]]:
    """
    過濾並解析合法的 action。

    Returns
    -------
    tuple[list[NextAction], list[str]]
        (合法的 NextAction 列表, 被過濾掉的非法 action 名稱列表)
    """
    valid: list[NextAction] = []
    invalid_names: list[str] = []

    for item in raw_actions:
        action_name = item.get("action", "")
        if action_name not in _VALID_ACTIONS:
            invalid_names.append(action_name)
            continue

        # 設定 priority 預設值
        if "priority" not in item or item["priority"] not in {"high", "medium", "low"}:
            item = {**item, "priority": "medium"}

        try:
            valid.append(NextAction(**item))
        except Exception as exc:
            logger.warning("NextAction 解析失敗，跳過：%s，錯誤：%s", item, exc)
            invalid_names.append(action_name)

    return valid, invalid_names


def _build_fallback_action(overall_level: str) -> NextAction:
    """
    依 overall_level 回傳通用 fallback action。

    high   → escalate_to_senior (high)
    medium → schedule_consultation (medium)
    low    → send_educational_content (medium)
    """
    if overall_level == "high":
        return NextAction(
            action="escalate_to_senior",
            why="客戶健康風險等級偏高，建議轉介資深教練或上線協助評估，確保客戶獲得適當的專業支援",
            priority="high",
        )
    elif overall_level == "medium":
        return NextAction(
            action="schedule_consultation",
            why="客戶健康風險等級中等，建議安排 2:1 商談進一步了解需求，提供個人化建議",
            priority="medium",
        )
    else:
        return NextAction(
            action="send_educational_content",
            why="客戶健康風險等級較低，建議先推送衛教資料建立認識與信任，為後續諮詢做準備",
            priority="medium",
        )


# ---------------------------------------------------------------------------
# 主要公開函式
# ---------------------------------------------------------------------------


async def generate_next_actions(
    *,
    answers: dict[str, Any],
    health_summary: HealthAssessmentSummary,
    recommended_products: list[RecommendedProduct],
    context: PromptContext,
    client: LLMClient,
    model: str | None = None,
    max_actions: int = 3,
) -> list[NextAction]:
    """
    依問卷答案、健康摘要、推薦產品呼叫 LLM，產出 1-3 個下一步行動建議。

    流程：
    1. 建立 system prompt（含 5 種 action 定義、判斷邏輯、few-shot）
    2. 建立 user prompt（客戶填答 + 健康摘要 + 推薦產品，移除 PII）
    3. 呼叫 client.complete_json（temperature=0.35）
    4. 過濾非法 action，記錄 warning
    5. 若過濾後為空 → fallback 依 overall_level 給通用 action
    6. 截斷至 max_actions

    Parameters
    ----------
    answers:
        問卷填答 dict，key 為 field_id。
    health_summary:
        健康研判摘要。
    recommended_products:
        推薦產品列表。
    context:
        包含 label 映射、教練等級、語系的上下文。
    client:
        LLMClient 實例。
    model:
        可選模型覆蓋，如 "gemini/gemini-2.5-pro"。
    max_actions:
        最多回傳幾個行動，預設 3。

    Returns
    -------
    list[NextAction]
        解析成功的下一步行動建議，1 ~ max_actions 個。
    """
    system_prompt = _SYSTEM_PROMPT
    user_prompt = _build_user_prompt(
        answers=answers,
        health_summary=health_summary,
        recommended_products=recommended_products,
        context=context,
        max_actions=max_actions,
    )

    raw: dict[str, Any] = await client.complete_json(
        system=system_prompt,
        user=user_prompt,
        response_schema={"type": "object", "properties": {"actions": {"type": "array"}}},
        model=model,
        temperature=0.35,
    )

    raw_actions = _parse_actions_from_raw(raw)
    valid_actions, invalid_names = _filter_valid_actions(raw_actions)

    if invalid_names:
        logger.warning(
            "LLM 回傳含非法 action，已過濾：%s",
            invalid_names,
        )

    # 若過濾後為空，使用 fallback
    if not valid_actions:
        logger.warning(
            "所有 action 均非法（%s），使用 fallback（overall_level=%s）",
            invalid_names,
            health_summary.overall_level,
        )
        valid_actions = [_build_fallback_action(health_summary.overall_level)]

    # 截斷至 max_actions
    return valid_actions[:max_actions]
