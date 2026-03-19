from fastapi import APIRouter

from app.api.v1.contents import router as contents_router
from app.api.v1.webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(contents_router, prefix="/contents", tags=["contents"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
