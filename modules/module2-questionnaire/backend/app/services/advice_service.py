"""
Advice Service — 單一進入點，串接四個 prompt 子模組。

設計原則：
    - 兩階段平行化：Stage 2（health_summary + product_recommendation），
      Stage 3（sales_scripts + next_actions）
    - warm_up 載入靜態資料（labels、products、rules）一次，後續 advise 沿用
    - 失敗不包裝：任何子任務 raise 例外直接冒泡給呼叫端
    - 不使用全域 lru_cache；由 AdviceService 實例持有狀態

匯出：
    AdviceServiceConfig  — frozen dataclass，設定封裝
    AdviceService        — 主要服務類別
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core import LLMClient
from app.schemas import AdviceRequest, AdviceResponse
from app.services.prompts.base import PromptContext, build_field_label_map
from app.services.prompts.health_summary import generate_health_summary
from app.services.prompts.next_actions import generate_next_actions
from app.services.prompts.product_recommendation import generate_product_recommendation
from app.services.prompts.rule_engine import collect_candidates, evaluate_rules, load_catalog
from app.services.prompts.sales_scripts import generate_sales_scripts


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AdviceServiceConfig:
    """
    AdviceService 設定封裝（不可變）。

    Attributes
    ----------
    questionnaire_path:
        questionnaire.json 的絕對路徑，用於建立 field → label 映射。
    products_path:
        products.json 的絕對路徑，供規則引擎與 fallback 使用。
    rules_path:
        product_rules.json 的絕對路徑，供規則引擎使用。
    max_candidates:
        規則引擎最多回傳的候選產品數，預設 15。
    max_products:
        LLM 最多推薦的產品數，預設 3。
    max_next_actions:
        LLM 最多產出的下一步行動數，預設 3。
    """

    questionnaire_path: Path
    products_path: Path
    rules_path: Path
    max_candidates: int = 15
    max_products: int = 3
    max_next_actions: int = 3


# ---------------------------------------------------------------------------
# AdviceService
# ---------------------------------------------------------------------------


class AdviceService:
    """
    串接四個 prompt 子模組，產出完整 AdviceResponse 的 Orchestrator。

    生命週期：
        1. 建立實例（注入 config + LLMClient）
        2. （可選）顯式呼叫 warm_up()，或於第一次 advise() 時自動觸發
        3. 重複呼叫 advise(request) 取得建議
    """

    def __init__(self, config: AdviceServiceConfig, client: LLMClient) -> None:
        self._config = config
        self._client = client
        self._context: PromptContext | None = None
        self._products: dict[str, Any] | None = None
        self._rules: list | None = None

    async def warm_up(self) -> None:
        """
        載入靜態資料（questionnaire labels、products、rules）。

        可顯式呼叫以預熱；advise() 若尚未 warm_up 會自動觸發。
        多次呼叫時，只有第一次有效（幂等）。
        """
        if self._context is not None:
            return

        labels = build_field_label_map(self._config.questionnaire_path)
        self._context = PromptContext(
            questionnaire_labels=labels,
            coach_level="new",
            locale="zh-TW",
        )
        self._products, self._rules = load_catalog(
            self._config.products_path,
            self._config.rules_path,
        )

    async def advise(self, request: AdviceRequest) -> AdviceResponse:
        """
        完整 pipeline：規則引擎 → LLM（兩階段平行）→ 組裝 AdviceResponse。

        Stage 1（同步）：
            evaluate_rules + collect_candidates — 純函式，無 I/O

        Stage 2（平行 async）：
            generate_health_summary + generate_product_recommendation

        Stage 3（平行 async，依賴 Stage 2 輸出）：
            generate_sales_scripts + generate_next_actions

        Stage 4：組裝並回傳 AdviceResponse

        Parameters
        ----------
        request:
            包含問卷答案的 AdviceRequest。

        Returns
        -------
        AdviceResponse
            四段結構化建議（summary、products、scripts、actions）。

        Raises
        ------
        任何子模組 raise 的例外均直接冒泡，不包裝。
        """
        if self._context is None:
            await self.warm_up()

        # Stage 1: Rule engine（純函式，不呼叫 LLM）
        triggered = evaluate_rules(request.answers, self._rules)
        candidates = collect_candidates(
            triggered,
            self._rules,
            self._products,
            max_candidates=self._config.max_candidates,
        )

        # Stage 2: 平行 — health_summary + product_recommendation
        summary, products = await asyncio.gather(
            generate_health_summary(
                answers=request.answers,
                context=self._context,
                client=self._client,
            ),
            generate_product_recommendation(
                answers=request.answers,
                candidates=candidates,
                context=self._context,
                client=self._client,
                max_products=self._config.max_products,
            ),
        )

        # Stage 3: 平行 — sales_scripts + next_actions（依賴 Stage 2 結果）
        scripts, actions = await asyncio.gather(
            generate_sales_scripts(
                answers=request.answers,
                health_summary=summary,
                recommended_products=products,
                context=self._context,
                client=self._client,
            ),
            generate_next_actions(
                answers=request.answers,
                health_summary=summary,
                recommended_products=products,
                context=self._context,
                client=self._client,
                max_actions=self._config.max_next_actions,
            ),
        )

        # Stage 4: 組裝
        return AdviceResponse(
            summary=summary,
            recommended_products=products,
            sales_scripts=scripts,
            next_actions=actions,
        )
