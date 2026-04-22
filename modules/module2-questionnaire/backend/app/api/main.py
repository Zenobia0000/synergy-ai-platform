"""FastAPI application bootstrap."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import advise as advise_routes
from app.api.routes import schema as schema_routes

app = FastAPI(
    title="Synergy Questionnaire AI",
    version="0.1.0",
    description="Module 2 POC: questionnaire-driven marketing advice for new coaches.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema_routes.router)
app.include_router(advise_routes.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
