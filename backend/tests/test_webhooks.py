"""Webhook signature + idempotency tests (C1, H4)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.models.content import ContentQueue


def _content_payload() -> dict:
    return {
        "title": "X",
        "master_caption": "x",
        "platforms": "ig,x",
    }


async def _seed_content(db_session, platforms: str = "ig,x") -> uuid.UUID:
    c = ContentQueue(
        title="t", master_caption="c", platforms=platforms, status="publishing"
    )
    db_session.add(c)
    await db_session.commit()
    await db_session.refresh(c)
    return c.id


@pytest.mark.asyncio
async def test_webhook_rejects_missing_signature(client: AsyncClient, db_session):
    cid = await _seed_content(db_session)
    resp = await client.post(
        "/api/v1/webhooks/publish-result",
        json={"content_id": str(cid), "platform": "ig", "status": "success"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "webhook_verification_failed"


@pytest.mark.asyncio
async def test_webhook_rejects_wrong_signature(client: AsyncClient, db_session):
    cid = await _seed_content(db_session)
    resp = await client.post(
        "/api/v1/webhooks/publish-result",
        json={"content_id": str(cid), "platform": "ig", "status": "success"},
        headers={"x-n8n-signature": "wrong-secret"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_accepts_correct_signature(client: AsyncClient, db_session):
    cid = await _seed_content(db_session)
    resp = await client.post(
        "/api/v1/webhooks/publish-result",
        json={"content_id": str(cid), "platform": "ig", "status": "success"},
        headers={"x-n8n-signature": settings.N8N_WEBHOOK_SECRET},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


@pytest.mark.asyncio
async def test_webhook_idempotent_on_duplicate_delivery(
    client: AsyncClient, db_session
):
    """H4: a repeated webhook for (content_id, platform) must not inflate
    success counts or create a second log row."""
    cid = await _seed_content(db_session, platforms="ig,x")
    body = {"content_id": str(cid), "platform": "ig", "status": "success"}
    headers = {"x-n8n-signature": settings.N8N_WEBHOOK_SECRET}

    r1 = await client.post(
        "/api/v1/webhooks/publish-result", json=body, headers=headers
    )
    r2 = await client.post(
        "/api/v1/webhooks/publish-result", json=body, headers=headers
    )

    assert r1.status_code == 200
    assert r2.status_code == 200
    # second call must report duplicate, not create a new log
    assert r2.json()["data"].get("duplicate") is True
    assert r1.json()["data"]["log_id"] == r2.json()["data"]["log_id"]


@pytest.mark.asyncio
async def test_webhook_status_aggregation_partial_success(
    client: AsyncClient, db_session
):
    cid = await _seed_content(db_session, platforms="ig,x")
    headers = {"x-n8n-signature": settings.N8N_WEBHOOK_SECRET}

    await client.post(
        "/api/v1/webhooks/publish-result",
        json={"content_id": str(cid), "platform": "ig", "status": "success"},
        headers=headers,
    )
    await client.post(
        "/api/v1/webhooks/publish-result",
        json={"content_id": str(cid), "platform": "x", "status": "failed"},
        headers=headers,
    )

    # Re-fetch via API
    detail = await client.get(f"/api/v1/contents/{cid}")
    assert detail.json()["data"]["status"] == "partial_success"
