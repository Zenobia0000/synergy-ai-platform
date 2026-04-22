"""
整合測試：GET /questionnaire/schema 與 GET /products 路由。

使用 FastAPI TestClient（httpx-based），真實讀取 data/schemas/*.json，
不 mock 檔案 I/O——確保資料結構驗證正確。
"""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.deps import load_questionnaire, load_products

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_cache():
    """每個測試前清除 lru_cache，避免跨測試汙染。"""
    load_questionnaire.cache_clear()
    load_products.cache_clear()
    yield
    load_questionnaire.cache_clear()
    load_products.cache_clear()


@pytest.fixture(scope="module")
def client():
    """共用 TestClient（module scope 以節省啟動成本）。"""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 1. 回歸測試：/health 仍可用
# ---------------------------------------------------------------------------


def test_health_still_works(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 2-5. GET /questionnaire/schema
# ---------------------------------------------------------------------------


def test_questionnaire_schema_returns_200(client: TestClient) -> None:
    resp = client.get("/questionnaire/schema")
    assert resp.status_code == 200


def test_questionnaire_schema_content_type_json(client: TestClient) -> None:
    resp = client.get("/questionnaire/schema")
    assert "application/json" in resp.headers["content-type"]


def test_questionnaire_schema_has_sections_field(client: TestClient) -> None:
    resp = client.get("/questionnaire/schema")
    body = resp.json()
    assert "sections" in body
    assert isinstance(body["sections"], list)
    assert len(body["sections"]) > 0


def test_questionnaire_schema_has_meta_field(client: TestClient) -> None:
    resp = client.get("/questionnaire/schema")
    body = resp.json()
    assert "_meta" in body
    meta = body["_meta"]
    assert "source_file" in meta
    assert "generated_at" in meta


def test_questionnaire_schema_field_ids_unique(client: TestClient) -> None:
    """所有欄位的 field_id 在整份問卷中不重複。"""
    resp = client.get("/questionnaire/schema")
    body = resp.json()
    field_ids: list[str] = []
    for section in body["sections"]:
        for field in section.get("fields", []):
            field_ids.append(field["field_id"])
    assert len(field_ids) == len(set(field_ids)), (
        f"Duplicate field_ids detected: {[x for x in field_ids if field_ids.count(x) > 1]}"
    )


# ---------------------------------------------------------------------------
# 6-10. GET /products
# ---------------------------------------------------------------------------


def test_products_returns_200(client: TestClient) -> None:
    resp = client.get("/products")
    assert resp.status_code == 200


def test_products_has_meta_and_total(client: TestClient) -> None:
    resp = client.get("/products")
    body = resp.json()
    assert "_meta" in body
    assert "total" in body
    assert "products" in body
    assert isinstance(body["products"], list)
    assert isinstance(body["total"], int)
    assert body["total"] > 0


def test_products_limit_respected(client: TestClient) -> None:
    """?limit=3 應回傳 <= 3 筆，但 total 仍是原始總數。"""
    resp_all = client.get("/products")
    total_all = resp_all.json()["total"]

    resp = client.get("/products?limit=3")
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["products"]) <= 3
    # total 永遠反映 category-filter 後的筆數，未 filter 時等於全部
    assert body["total"] == total_all


def test_products_category_filter(client: TestClient) -> None:
    """已知分類 filter 後，所有回傳產品的 category 都符合。"""
    # 先取得所有產品，找出第一個 category
    resp_all = client.get("/products")
    all_products = resp_all.json()["products"]
    assert len(all_products) > 0
    first_category = all_products[0]["category"]

    resp = client.get(f"/products?category={first_category}")
    body = resp.json()
    assert resp.status_code == 200
    for product in body["products"]:
        assert product["category"] == first_category


def test_products_category_no_match_returns_empty(client: TestClient) -> None:
    """不存在的分類 → products=[]，total 仍等於原始總數。"""
    resp_all = client.get("/products")
    total_all = resp_all.json()["total"]

    resp = client.get("/products?category=__nonexistent__")
    body = resp.json()
    assert resp.status_code == 200
    assert body["products"] == []
    # total 反映 filter 前的筆數
    assert body["total"] == total_all


# ---------------------------------------------------------------------------
# 11. CORS preflight
# ---------------------------------------------------------------------------


def test_cors_headers_present(client: TestClient) -> None:
    """OPTIONS preflight 對 localhost:3000 應回傳正確 CORS headers。"""
    resp = client.options(
        "/questionnaire/schema",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI CORS middleware 對允許的 origin 應回傳 200
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
