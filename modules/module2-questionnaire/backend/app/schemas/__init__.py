"""
schemas 套件入口，統一匯出所有 Pydantic 契約模型。
"""

from app.schemas.advice import (
    AdviceRequest,
    AdviceResponse,
    HealthAssessmentSummary,
    NextAction,
    RecommendedProduct,
    SalesScript,
    get_advice_response_schema_json,
)

__all__ = [
    "AdviceRequest",
    "AdviceResponse",
    "HealthAssessmentSummary",
    "NextAction",
    "RecommendedProduct",
    "SalesScript",
    "get_advice_response_schema_json",
]
