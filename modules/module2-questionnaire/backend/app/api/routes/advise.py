"""
POST /advise 路由。

接收問卷答案，呼叫 AdviceService，回傳四段結構化建議。
錯誤映射：
    LLMTimeoutError → 504 Gateway Timeout
    LLMJSONError    → 502 Bad Gateway
    LLMError        → 502 Bad Gateway
    其他例外        → 500 Internal Server Error（FastAPI default）
    Pydantic 驗證  → 422 Unprocessable Entity（FastAPI 自動）
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_advice_service
from app.core.llm_client import LLMError, LLMJSONError, LLMTimeoutError
from app.schemas import AdviceRequest, AdviceResponse
from app.services import AdviceService

router = APIRouter(tags=["advise"])


@router.post("/advise", response_model=AdviceResponse)
async def post_advise(
    request: AdviceRequest,
    service: AdviceService = Depends(get_advice_service),
) -> AdviceResponse:
    """
    產生健康評估建議（summary + products + sales_scripts + next_actions）。

    輸入：AdviceRequest（問卷答案 + locale + coach_level）
    輸出：AdviceResponse（四段結構化建議）
    """
    try:
        return await service.advise(request)
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=f"LLM timeout: {e}") from e
    except LLMJSONError as e:
        raise HTTPException(status_code=502, detail=f"LLM response invalid: {e}") from e
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"LLM upstream error: {e}") from e
