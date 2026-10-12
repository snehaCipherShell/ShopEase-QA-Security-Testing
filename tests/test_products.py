import pytest
from conftest import count


def test_list_products_returns_seeded_catalog(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 8 == len(body["products"])
    for p in body["products"]:
        assert set(p) == {"id", "sku", "name", "description", "category", "price", "stock"}
        assert isinstance(p["id"], int) and isinstance(p["price"], float) and isinstance(p["stock"], int)
        assert isinstance(p["name"], str)


def test_seeded_prices_are_predictable(client):
    prices = {p["name"]: p["price"] for p in client.get("/api/products").json()["products"]}
    assert prices["Wireless Mouse"] == 19.99
    assert prices["Mechanical Keyboard"] == 59.50
    assert prices["USB-C Cable"] == 9.99
    assert prices["Notebook A5"] == 5.00


@pytest.mark.parametrize("query,expected", [
    ("mouse", ["Wireless Mouse"]),
    ("MOUSE", ["Wireless Mouse"]),        # case-insensitive
    ("  mouse  ", ["Wireless Mouse"]),    # surrounding spaces trimmed
    ("laptop", ["Laptop Stand"]),
    ("a5", ["Notebook A5"]),
])
def test_search_matches(client, query, expected):
    names = [p["name"] for p in client.get("/api/products", params={"q": query}).json()["products"]]
    assert names == expected


def test_search_no_match_returns_empty_list_not_error(client):
    r = client.get("/api/products", params={"q": "zzzz-no-such-product"})
    assert r.status_code == 200 and r.json() == {"count": 0, "products": []}


def test_search_empty_query_returns_everything(client):
    assert client.get("/api/products", params={"q": ""}).json()["count"] == 8


@pytest.mark.parametrize("q", ["%", "_", "100%"])
def test_search_wildcards_are_treated_literally(client, q):
    assert client.get("/api/products", params={"q": q}).json()["count"] == 0


def test_search_sql_injection_string_is_harmless(client, db):
    payload = "'; DROP TABLE products; --"
    r = client.get("/api/products", params={"q": payload})
    assert r.status_code == 200 and r.json()["count"] == 0
    assert count(db, "products") == 8
    r2 = client.get("/api/products", params={"q": "' OR '1'='1"})
    assert r2.status_code == 200 and r2.json()["count"] == 0


def test_search_script_tag_is_not_reflected(client):
    r = client.get("/api/products", params={"q": "<script>alert(1)</script>"})
    assert r.status_code == 200 and "<script>" not in r.text


@pytest.mark.parametrize("length,expected", [(100, 200), (101, 400)])
def test_search_length_boundary(client, length, expected):
    assert client.get("/api/products", params={"q": "a" * length}).status_code == expected


def test_get_single_product(client):
    r = client.get("/api/products/1")
    assert r.status_code == 200 and r.json()["name"] == "Wireless Mouse" and r.json()["price"] == 19.99


@pytest.mark.parametrize("path", ["/api/products/9999", "/api/products/0"])
def test_get_unknown_product_returns_404(client, path):
    r = client.get(path)
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


@pytest.mark.parametrize("path", ["/api/products/abc", "/api/products/-1", "/api/products/1.5"])
def test_get_product_with_non_numeric_id_returns_404(client, path):
    assert client.get(path).status_code == 404


def test_catalog_is_public_no_login_needed(client):
    assert client.get("/api/products").status_code == 200
