import pytest
from conftest import count


def add(c, product_id, quantity, **extra):
    return c.post("/api/cart/items", json={"product_id": product_id, "quantity": quantity, **extra})


def test_add_item_returns_201_and_correct_totals(alice):
    r = add(alice, 1, 2)
    assert r.status_code == 201
    cart = r.json()
    assert cart["items"][0] == {"product_id": 1, "name": "Wireless Mouse", "unit_price": 19.99, "quantity": 2, "line_total": 39.98}
    assert cart["subtotal"] == 39.98 and cart["total_items"] == 2


def test_adding_same_product_again_merges_quantity_and_returns_200(alice):
    add(alice, 1, 2)
    r = add(alice, 1, 3)
    assert r.status_code == 200 and r.json()["items"][0]["quantity"] == 5


def test_subtotal_with_multiple_products(alice):
    add(alice, 1, 2)  # 2 x 19.99 = 39.98
    add(alice, 3, 3)  # 3 x  9.99 = 29.97
    cart = alice.get("/api/cart").json()
    assert cart["subtotal"] == 69.95 and cart["total_items"] == 5 and len(cart["items"]) == 2


def test_update_quantity_with_put(alice):
    add(alice, 3, 1)
    r = alice.put("/api/cart/items/3", json={"quantity": 4})
    assert r.status_code == 200 and r.json()["subtotal"] == 39.96


def test_update_quantity_of_item_not_in_cart_returns_404(alice):
    assert alice.put("/api/cart/items/3", json={"quantity": 2}).status_code == 404


def test_remove_item_with_delete(alice):
    add(alice, 1, 1)
    add(alice, 3, 1)
    r = alice.delete("/api/cart/items/1")
    assert r.status_code == 200
    assert [i["product_id"] for i in r.json()["items"]] == [3] and r.json()["subtotal"] == 9.99


def test_remove_item_not_in_cart_returns_404(alice):
    assert alice.delete("/api/cart/items/1").status_code == 404


def test_clear_cart(alice, db):
    add(alice, 1, 1)
    add(alice, 3, 2)
    r = alice.delete("/api/cart")
    assert r.status_code == 200 and r.json() == {"items": [], "total_items": 0, "subtotal": 0.0}
    assert count(db, "cart_items") == 0


@pytest.mark.parametrize("quantity,expected", [(1, 201), (2, 201), (9, 201), (10, 201), (0, 400), (-1, 400), (11, 400)])
def test_quantity_boundaries(alice, quantity, expected):
    assert add(alice, 1, quantity).status_code == expected


@pytest.mark.parametrize("quantity", ["2", 1.5, None, True, [1], {"n": 1}])
def test_quantity_wrong_types_rejected_and_cart_unchanged(alice, db, quantity):
    r = add(alice, 1, quantity)
    assert r.status_code == 400 and r.json()["error"]["code"] == "validation_error"
    assert count(db, "cart_items") == 0


def test_missing_fields_rejected(alice):
    assert alice.post("/api/cart/items", json={"quantity": 1}).status_code == 400
    assert alice.post("/api/cart/items", json={"product_id": 1}).status_code == 400


@pytest.mark.parametrize("product_id", ["1", 0, -5, 1.0, None])
def test_invalid_product_id_rejected(alice, product_id):
    assert add(alice, product_id, 1).status_code == 400


def test_unknown_product_returns_404_and_nothing_stored(alice, db):
    assert add(alice, 9999, 1).status_code == 404
    assert count(db, "cart_items") == 0


def test_merged_quantity_over_limit_rejected_and_cart_unchanged(alice):
    add(alice, 1, 8)
    assert add(alice, 1, 3).status_code == 400
    assert alice.get("/api/cart").json()["items"][0]["quantity"] == 8


def test_out_of_stock_product_cannot_be_added(alice, db):
    r = add(alice, 7, 1)  # Desk Lamp has stock 0
    assert r.status_code == 409 and r.json()["error"]["code"] == "insufficient_stock"
    assert count(db, "cart_items") == 0


def test_quantity_above_stock_rejected(alice, db):
    db.execute("UPDATE products SET stock = 2 WHERE id = 1")
    assert add(alice, 1, 3).status_code == 409


def test_client_supplied_price_is_ignored(alice):
    r = add(alice, 2, 1, price=0.01, unit_price=0.01, line_total=0.01)
    assert r.status_code == 201
    assert r.json()["items"][0]["unit_price"] == 59.50 and r.json()["subtotal"] == 59.50


def test_cart_requires_authentication(client):
    for r in (client.get("/api/cart"), add(client, 1, 1), client.put("/api/cart/items/1", json={"quantity": 1}),
              client.delete("/api/cart/items/1"), client.delete("/api/cart")):
        assert r.status_code == 401


def test_carts_are_isolated_between_users(alice, bob):
    add(alice, 1, 2)
    assert bob.get("/api/cart").json()["items"] == []
    add(bob, 3, 1)
    assert [i["product_id"] for i in alice.get("/api/cart").json()["items"]] == [1]


def test_bob_cannot_modify_alices_cart_item_via_same_product_id(alice, bob):
    add(alice, 1, 2)
    assert bob.put("/api/cart/items/1", json={"quantity": 9}).status_code == 404
    assert bob.delete("/api/cart/items/1").status_code == 404
    assert alice.get("/api/cart").json()["items"][0]["quantity"] == 2
