"""
產品解析器測試（階段 2 GREEN）。

階段 2：實際斷言，驗收條件為全部 PASS。
"""

from __future__ import annotations

from pathlib import Path

from app.services.parsers.products import parse_products

# rawdata 路徑
RAWDATA_DIR = Path(__file__).parents[4] / "rawdata"
CATALOG_XLSX = RAWDATA_DIR / "product_catalog.xlsx"
IMAGES_DOCX = RAWDATA_DIR / "Synergy 產品圖片連結.docx"


def test_parse_returns_at_least_ten_products() -> None:
    """產品目錄至少應有 10 個產品。"""
    result = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    assert len(result.products) >= 10, (
        f"預期至少 10 個產品，實際得到 {len(result.products)} 個"
    )


def test_every_product_has_sku() -> None:
    """每個產品必須有非空的 sku 欄位。"""
    result = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    for product in result.products:
        assert product.sku and product.sku.strip() != "", (
            f"產品 {product.name!r} 的 sku 為空"
        )


def test_unmatched_images_is_list() -> None:
    """unmatched_images 必須是 tuple（即使為空也合法），每個元素含 name_in_docx 與 url。"""
    result = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    assert isinstance(result.unmatched_images, tuple), (
        f"unmatched_images 應為 tuple，實際為 {type(result.unmatched_images)}"
    )
    for item in result.unmatched_images:
        assert item.name_in_docx != "", "name_in_docx 不得為空"
        assert item.url != "", "url 不得為空"


def test_at_least_one_product_has_image_url() -> None:
    """至少一個產品應有非 None 的 image_url（圖片匹配至少命中一次）。"""
    result = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    products_with_image = [p for p in result.products if p.image_url is not None]
    assert len(products_with_image) >= 1, (
        "至少應有一個產品匹配到圖片連結，但所有產品的 image_url 皆為 None"
    )


def test_proargi9_exists() -> None:
    """SKU 96371 應存在，且產品名稱含 PROARGI。"""
    result = parse_products(CATALOG_XLSX, IMAGES_DOCX)
    sku_map = {p.sku: p for p in result.products}
    assert "96371" in sku_map, (
        f"SKU '96371' 不在產品清單中，現有 SKU：{list(sku_map.keys())[:10]}"
    )
    product = sku_map["96371"]
    assert "PROARGI" in product.name.upper(), (
        f"SKU 96371 的產品名稱應含 'PROARGI'，實際為 {product.name!r}"
    )
