"""Regression tests for BUG-002: integer IDs outside SQLite's 64-bit range must not cause HTTP 500."""
import pytest
from conftest import count

MAX_ID = 2**63 - 1          # largest value SQLite can store
TOO_BIG = [2**63, 10**30]   # first value out of range, and a very large one


def status(client, method, path, **kwargs):
    return client.request(method, path, **kwargs).status_code


@pytest.mark.parametrize("big", TOO_BIG)
def test_out_of_range_ids_in_url_return_404_not_500(alice, big):
    assert status(alice, "GET", f"/api/products/{big}") == 404
    assert status(alice, "GET", f"/api/orders/{big}") == 404
    assert status(alice, "POST", f"/api/orders/{big}/cancel") == 404
    assert status(alice, "PUT", f"/api/cart/items/{big}", json={"quantity": 1}) == 404
    assert status(alice, "DELETE", f"/api/cart/items/{big}") == 404


@pytest.mark.parametrize("big", TOO_BIG)
def test_out_of_range_product_id_in_body_returns_400_and_changes_nothing(alice, db, big):
    r = alice.post("/api/cart/items", json={"product_id": big, "quantity": 1})
    assert r.status_code == 400 and r.json()["error"]["code"] == "validation_error"
    assert count(db, "cart_items") == 0


def test_largest_valid_id_still_returns_normal_404(alice):
    assert status(alice, "GET", f"/api/products/{MAX_ID}") == 404
