"""Happy/sad-path tests for /api/v1/contents."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


def _payload(**overrides) -> dict:
    base = {
        "title": "Hello",
        "master_caption": "Hello world",
        "platforms": "ig,x",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_content_happy_path(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/contents", json=_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["title"] == "Hello"
    assert body["data"]["status"] == "draft"


@pytest.mark.asyncio
async def test_create_content_rejects_invalid_platform(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/contents", json=_payload(platforms="instagram")
    )
    assert resp.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_delete_returns_204_with_empty_body(client: AsyncClient) -> None:
    create = await client.post("/api/v1/contents", json=_payload())
    content_id = create.json()["data"]["id"]

    resp = await client.delete(f"/api/v1/contents/{content_id}")
    assert resp.status_code == 204
    assert resp.content == b""  # H2: 204 must have empty body


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_404_json(client: AsyncClient) -> None:
    resp = await client.delete(
        "/api/v1/contents/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "resource_not_found"


@pytest.mark.asyncio
async def test_schedule_requires_pydantic_schema(client: AsyncClient) -> None:
    """H1: /schedule must reject payloads without publish_at via Pydantic."""
    create = await client.post("/api/v1/contents", json=_payload())
    content_id = create.json()["data"]["id"]

    # Missing publish_at — should be 422 (Pydantic), not 400 hand-rolled
    resp = await client.post(
        f"/api/v1/contents/{content_id}/schedule", json={}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_schedule_happy_path(client: AsyncClient) -> None:
    create = await client.post("/api/v1/contents", json=_payload())
    content_id = create.json()["data"]["id"]

    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    resp = await client.post(
        f"/api/v1/contents/{content_id}/schedule",
        json={"publish_at": future},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "queued"


@pytest.mark.asyncio
async def test_schedule_rejects_past_time(client: AsyncClient) -> None:
    create = await client.post("/api/v1/contents", json=_payload())
    content_id = create.json()["data"]["id"]

    past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    resp = await client.post(
        f"/api/v1/contents/{content_id}/schedule",
        json={"publish_at": past},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_schedule_time"
