"""
健康研判摘要 Prompt 工程模組。

核心函式：
    generate_health_summary — 依問卷答案呼叫 LLM，產出 HealthAssessmentSummary
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.core import LLMClient
from app.schemas import HealthAssessmentSummary
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
# 常數：預設免責聲明
# ---------------------------------------------------------------------------

_DEFAULT_DISCLAIMER = (
    "本評估僅供健康諮詢參考，非醫療診斷。"
    "若有明顯不適或正在治療中，請優先遵循醫師建議。"
)

_MEDICAL_DISCLAIMER_KEYWORD = "非醫療診斷"

# ---------------------------------------------------------------------------
# 常數：Few-shot 範例（嵌入 system prompt）
# ---------------------------------------------------------------------------

_FEW_SHOT_EXAMPLE = """
【範例輸入】
- 性別：男
- 年齡：45
- 目前體重（kg）：95
- 身高（cm）：175
- 本次最想優先改善的問題：體重管理、睡眠品質
- 家族病史：高血壓、糖尿病、高血脂

【範例輸出】
{
  "key_risks": [
    "體重過重（BMI 31.0，屬肥胖範圍）",
    "三高家族史（高血壓、糖尿病、高血脂）",
    "睡眠品質差，代謝壓力增加"
  ],
  "overall_level": "high",
  "narrative": "客戶為 45 歲男性，BMI 約 31，屬肥胖範圍，加上三高家族史，整體健康風險偏高。睡眠不佳進一步加重代謝負擔，建議優先進行體重管理並改善睡眠。整體評估為高風險，需積極介入與追蹤。",
  "disclaimers": [
    "本評估僅供健康諮詢參考，非醫療診斷。若有明顯不適或正在治療中，請優先遵循醫師建議。"
  ]
}
"""

# ---------------------------------------------------------------------------
# 常數：System prompt 模板
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_TEMPLATE = """你是 Synergy 資深健康顧問，專門為新手教練快速解讀客戶問卷，提供健康評估摘要。

【核心規則】
1. 本評估僅供健康諮詢參考，非醫療診斷。若客戶有明顯不適或正在接受治療，必須提醒優先遵循醫師建議。
2. 禁止誇大效果、禁止承諾療效、禁止貶低醫療專業人員或醫療行為。
3. 輸出必須是合法 JSON，嚴格符合以下指定 schema，不得包含額外欄位。

【字數控制（硬性限制，避免輸出被截斷）】
- key_risks：**最多 3 項**，每項 **15~40 字**，聚焦最關鍵風險
- narrative：**80~180 字**，3~5 句即可，不要條列化
- disclaimers：最多 1 項，直接使用預設文字即可
- 總輸出長度盡量控制在 400 字以內

【輸出 JSON Schema】
{schema_json}

【Few-shot 範例】
{few_shot}

請依據客戶填答資料，產出符合上述 schema 的 JSON 格式健康評估摘要。"""

# ---------------------------------------------------------------------------
# 常數：User prompt 模板
# ---------------------------------------------------------------------------

_USER_PROMPT_SUFFIX = "\n\n請依上述資訊產出 JSON 格式的健康評估摘要。"


# ---------------------------------------------------------------------------
# 內部輔助函式
# ---------------------------------------------------------------------------


def _build_system_prompt() -> str:
    """建立 system prompt，嵌入 JSON schema 與 few-shot 範例。"""
    schema_dict = HealthAssessmentSummary.model_json_schema()
    schema_json = json.dumps(schema_dict, ensure_ascii=False, indent=2)
    return _SYSTEM_PROMPT_TEMPLATE.format(
        schema_json=schema_json,
        few_shot=_FEW_SHOT_EXAMPLE,
    )


def _build_user_prompt(
    answers: dict[str, Any],
    context: PromptContext,
) -> str:
    """
    將 answers 轉為人類可讀的 Q/A 條列式 prompt。

    - 移除 PII 欄位
    - 用 context.questionnaire_labels 將 field_id 換成中文 label
    """
    lines: list[str] = ["【客戶問卷填答】"]

    for field_id, value in answers.items():
        # 過濾 PII
        if field_id in _PII_FIELD_IDS:
            continue

        # 轉換 label；若無映射則保留 field_id
        label = context.questionnaire_labels.get(field_id, field_id)

        # 格式化 value
        if isinstance(value, list):
            formatted_value = "、".join(str(v) for v in value)
        elif value is None:
            formatted_value = "（未填）"
        else:
            formatted_value = str(value)

        lines.append(f"- {label}：{formatted_value}")

    lines.append(_USER_PROMPT_SUFFIX)
    return "\n".join(lines)


def _ensure_disclaimer(summary: HealthAssessmentSummary) -> HealthAssessmentSummary:
    """
    確保 disclaimers 含「非醫療診斷」關鍵字。

    若缺少或為空，補上預設免責聲明。
    回傳新的 HealthAssessmentSummary（不可變）。
    """
    combined = " ".join(summary.disclaimers)
    if not summary.disclaimers or _MEDICAL_DISCLAIMER_KEYWORD not in combined:
        new_disclaimers = [*summary.disclaimers, _DEFAULT_DISCLAIMER]
        return summary.model_copy(update={"disclaimers": new_disclaimers})
    return summary


# ---------------------------------------------------------------------------
# 主要公開函式
# ---------------------------------------------------------------------------


async def generate_health_summary(
    *,
    answers: dict[str, Any],
    context: PromptContext,
    client: LLMClient,
    model: str | None = None,
) -> HealthAssessmentSummary:
    """
    依問卷填答呼叫 LLM，產出 HealthAssessmentSummary。

    流程：
    1. 建立 system prompt（含 JSON schema + few-shot）
    2. 建立 user prompt（Q/A 條列，移除 PII，label 中文化）
    3. 呼叫 client.complete_json（temperature=0.3）
    4. 解析為 HealthAssessmentSummary；若 ValidationError → 重試一次（temperature +0.1）
    5. 確保 disclaimers 含「非醫療診斷」

    Parameters
    ----------
    answers:
        問卷填答 dict，key 為 field_id。
    context:
        包含 label 映射、教練等級、語系的上下文。
    client:
        LLMClient 實例。
    model:
        可選模型覆蓋，如 "gemini/gemini-2.5-pro"。

    Returns
    -------
    HealthAssessmentSummary
        解析成功的健康研判摘要。

    Raises
    ------
    ValidationError
        若兩次 LLM 呼叫均無法解析為合法 HealthAssessmentSummary。
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(answers, context)
    schema = HealthAssessmentSummary.model_json_schema()

    base_temperature = 0.3
    last_error: ValidationError | None = None

    for attempt in range(2):
        temperature = base_temperature + attempt * 0.1

        raw: dict[str, Any] = await client.complete_json(
            system=system_prompt,
            user=user_prompt,
            response_schema=schema,
            model=model,
            temperature=temperature,
        )

        try:
            summary = HealthAssessmentSummary(**raw)
            return _ensure_disclaimer(summary)
        except ValidationError as exc:
            last_error = exc
            logger.warning(
                "HealthAssessmentSummary validation failed (attempt %d/2): %s",
                attempt + 1,
                exc,
            )

    assert last_error is not None
    raise last_error
