"""
產品推薦 Prompt 工程模組。

兩階段策略：
    1. 規則引擎（rule_engine.py）已預先篩出候選清單（最多 15 個）
    2. 本模組用 LLM 從候選中挑選 1~max_products 個、排優先級、寫中文推薦理由

核心函式：
    generate_product_recommendation — 依候選清單與問卷答案呼叫 LLM，產出推薦列表

Fallback 機制：
    - 候選清單為空 → 跳過 LLM，直接取 products.json 第一個產品作通用建議
    - LLM 回傳空陣列 / 所有 SKU 均為幻覺 → fallback 取 candidates 前 1 個 + 通用理由
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import HttpUrl, ValidationError

from app.core import LLMClient
from app.schemas.advice import RecommendedProduct
from app.services.prompts.base import PromptContext
from app.services.prompts.rule_engine import CandidateProduct

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 常數
# ---------------------------------------------------------------------------

# PII 欄位 ID（不進入 prompt）
_PII_FIELD_IDS: frozenset[str] = frozenset(
    {"name", "email", "phone", "referrer", "form_id"}
)

# products.json 路徑（供 empty-candidates fallback 使用）
_PRODUCTS_JSON_PATH = (
    Path(__file__).resolve().parents[4] / "data" / "schemas" / "products.json"
)

# LLM 呼叫溫度（較低以減少幻覺）
_TEMPERATURE = 0.4

# ---------------------------------------------------------------------------
# 系統 Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
你是 Synergy 資深健康顧問，協助新手教練根據客戶狀況精準推薦產品。

## 規則

1. 你**只能從「候選清單」中挑選產品**，嚴禁自創任何不在候選清單中的產品名稱或 SKU。
2. 推薦理由需具體呼應客戶問卷狀況（例：「因您的體重 95kg 且有運動目標…」），禁止空泛描述。
3. 禁止誇大效果、禁止承諾療效，不可使用「治療」、「根治」、「保證」等詞語。
4. 若候選清單為空，請回傳 {"products": []}。
5. confidence 為你對此推薦的把握程度，範圍 0.0~1.0（浮點數）。

## 字數控制（硬性限制，避免輸出被截斷）

- 推薦產品**最多 3 個**（即使候選更多也精選 3 個最相關）
- 每個 reason **20~50 字**（太長記不住，太短沒說服力）
- 總輸出長度盡量在 300 字以內

## 輸出格式（嚴格 JSON，不可包含額外說明文字）

{"products": [{"sku": "<string>", "reason": "<string 20-50字>", "confidence": <float 0-1>}]}
"""

# ---------------------------------------------------------------------------
# 內部工具函式
# ---------------------------------------------------------------------------


def _strip_pii(answers: dict[str, Any]) -> dict[str, Any]:
    """移除 PII 欄位，回傳新 dict（不可變策略）。"""
    return {k: v for k, v in answers.items() if k not in _PII_FIELD_IDS}


def _format_answers_section(
    answers: dict[str, Any],
    context: PromptContext,
) -> str:
    """
    將問卷答案格式化為人類可讀的 Q/A 文字區塊。

    只列出有值的欄位，使用 questionnaire_labels 將 field_id 轉為中文。
    """
    clean_answers = _strip_pii(answers)
    lines: list[str] = []

    for field_id, value in clean_answers.items():
        if value is None or value == "" or value == []:
            continue
        label = context.questionnaire_labels.get(field_id, field_id)
        if isinstance(value, list):
            display = "、".join(str(v) for v in value)
        else:
            display = str(value)
        lines.append(f"- {label}：{display}")

    return "\n".join(lines) if lines else "（無有效問卷資料）"


def _format_candidates_section(candidates: list[CandidateProduct]) -> str:
    """
    將候選產品清單格式化為 prompt 用的條目清單。

    每個產品列 sku / name / category / scenario。
    """
    if not candidates:
        return "（無候選產品）"

    lines: list[str] = []
    for i, c in enumerate(candidates, start=1):
        scenario_str = "、".join(c.scenario[:3]) if c.scenario else "無"
        lines.append(
            f"{i}. SKU={c.sku}｜{c.name}｜分類：{c.category}｜情境：{scenario_str}"
        )

    return "\n".join(lines)


def _build_user_prompt(
    answers: dict[str, Any],
    candidates: list[CandidateProduct],
    context: PromptContext,
    max_products: int,
) -> str:
    """組裝 user prompt（三段式）。"""
    answers_text = _format_answers_section(answers, context)
    candidates_text = _format_candidates_section(candidates)

    return (
        "## Section 1：客戶問卷重點\n"
        f"{answers_text}\n\n"
        "## Section 2：候選產品清單\n"
        f"{candidates_text}\n\n"
        "## Section 3：任務\n"
        f"從上述候選清單中，挑選 1~{max_products} 個最適合該客戶的產品，"
        "為每個產品寫 20~60 字的繁體中文推薦理由，並給出信心分數（0.0~1.0）。\n"
        "輸出嚴格 JSON，不可包含額外文字。"
    )


def _clamp_confidence(value: float) -> float:
    """將 confidence 強制限制在 [0.0, 1.0] 範圍。"""
    return max(0.0, min(1.0, value))


def _load_fallback_product() -> dict[str, Any] | None:
    """從 products.json 讀取第一個產品作 fallback 用。"""
    try:
        data: dict[str, Any] = json.loads(
            _PRODUCTS_JSON_PATH.read_text(encoding="utf-8")
        )
        products = data.get("products", [])
        return products[0] if products else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("無法載入 products.json 作 fallback：%s", exc)
        return None


def _candidates_to_map(candidates: list[CandidateProduct]) -> dict[str, CandidateProduct]:
    """建立 sku → CandidateProduct 映射，供驗證 LLM 輸出用。"""
    return {c.sku: c for c in candidates}


def _parse_llm_products(
    raw_items: list[dict[str, Any]],
    candidates_map: dict[str, CandidateProduct],
    max_products: int,
) -> list[RecommendedProduct]:
    """
    解析 LLM 回傳的 products 陣列。

    - 過濾不在 candidates 中的 SKU（幻覺保險絲）
    - clamp confidence 到 [0,1]
    - 最多取 max_products 個
    - 回傳 RecommendedProduct 列表
    """
    results: list[RecommendedProduct] = []

    for item in raw_items:
        sku = item.get("sku", "")
        if sku not in candidates_map:
            logger.warning("LLM 回傳不在候選清單的 SKU '%s'，已過濾（幻覺）", sku)
            continue

        reason = item.get("reason", "")
        raw_confidence = item.get("confidence", 0.5)

        try:
            clamped_confidence = _clamp_confidence(float(raw_confidence))
        except (TypeError, ValueError):
            clamped_confidence = 0.5

        candidate = candidates_map[sku]

        # 嘗試建立 RecommendedProduct，confidence 超出範圍時已被 clamp
        try:
            product = RecommendedProduct(
                sku=sku,
                name=candidate.name,
                reason=reason,
                image_url=candidate.image_url,  # type: ignore[arg-type]
                confidence=clamped_confidence,
            )
            results.append(product)
        except ValidationError as exc:
            logger.warning("RecommendedProduct 驗證失敗（SKU=%s）：%s，略過", sku, exc)
            continue

        if len(results) >= max_products:
            break

    return results


def _build_fallback_from_candidates(
    candidates: list[CandidateProduct],
) -> list[RecommendedProduct]:
    """
    LLM 結果為空時，從 candidates 取前 1 個作 fallback。

    Returns empty list if candidates is also empty.
    """
    if not candidates:
        return []

    c = candidates[0]
    try:
        return [
            RecommendedProduct(
                sku=c.sku,
                name=c.name,
                reason="此產品符合您的健康需求，建議諮詢教練了解詳情。",
                image_url=c.image_url,  # type: ignore[arg-type]
                confidence=0.3,
            )
        ]
    except ValidationError:
        return []


def _build_fallback_from_products_json() -> list[RecommendedProduct]:
    """
    candidates 為空時，從 products.json 取第一個產品作通用 fallback。
    """
    product = _load_fallback_product()
    if product is None:
        return []

    image_url_raw = product.get("image_url")

    try:
        return [
            RecommendedProduct(
                sku=product["sku"],
                name=product.get("name", ""),
                reason="候選清單空，這是通用建議，請依客戶狀況與教練諮詢後決定。",
                image_url=image_url_raw,  # type: ignore[arg-type]
                confidence=0.2,
            )
        ]
    except (ValidationError, KeyError) as exc:
        logger.warning("建立 fallback RecommendedProduct 失敗：%s", exc)
        return []


# ---------------------------------------------------------------------------
# 主函式
# ---------------------------------------------------------------------------


async def generate_product_recommendation(
    *,
    answers: dict[str, Any],
    candidates: list[CandidateProduct],
    context: PromptContext,
    client: LLMClient,
    model: str | None = None,
    max_products: int = 3,
) -> list[RecommendedProduct]:
    """
    從候選產品清單中，透過 LLM 挑選並排序推薦產品。

    Parameters
    ----------
    answers:
        問卷填答 dict，key 為 field_id。
    candidates:
        規則引擎已篩選出的候選產品清單（最多 15 個）。
    context:
        PromptContext（含 questionnaire_labels, coach_level, locale）。
    client:
        LLMClient 實例。
    model:
        可選，覆蓋預設模型。
    max_products:
        最多推薦幾個產品（預設 3）。

    Returns
    -------
    list[RecommendedProduct]
        1~max_products 個推薦產品，依 LLM 排序優先級排列。
        若 LLM 結果為空，回傳 fallback（至少 1 個）。

    Fallback 規則：
        1. candidates 為空 → 不呼叫 LLM，直接取 products.json 第一個 + 通用理由
        2. LLM 回傳空 / 全幻覺 → fallback 取 candidates 前 1 個 + 通用理由
    """
    # ── Fallback 路徑：無候選清單 ──────────────────────────────────────────
    if not candidates:
        logger.info("候選清單為空，跳過 LLM，回傳通用 fallback 產品")
        return _build_fallback_from_products_json()

    # ── 建立 candidates map（供驗證用）──────────────────────────────────────
    candidates_map = _candidates_to_map(candidates)

    # ── 組裝 prompt ──────────────────────────────────────────────────────────
    user_prompt = _build_user_prompt(answers, candidates, context, max_products)

    # ── 呼叫 LLM ─────────────────────────────────────────────────────────────
    logger.debug(
        "呼叫 LLM 進行產品推薦，候選數=%d，max_products=%d",
        len(candidates),
        max_products,
    )

    llm_response = await client.complete_json(
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        temperature=_TEMPERATURE,
        model=model,
    )

    # ── 解析 LLM 回應 ─────────────────────────────────────────────────────────
    raw_items: list[dict[str, Any]] = llm_response.get("products", [])

    if not isinstance(raw_items, list):
        logger.warning("LLM 回傳的 products 不是 list：%s，走 fallback", type(raw_items))
        raw_items = []

    results = _parse_llm_products(raw_items, candidates_map, max_products)

    # ── Fallback：LLM 結果為空 ───────────────────────────────────────────────
    if not results:
        logger.info("LLM 回傳結果解析後為空，fallback 取 candidates 前 1 個")
        results = _build_fallback_from_candidates(candidates)

    return results
