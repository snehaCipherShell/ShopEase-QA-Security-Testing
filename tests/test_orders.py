import pytest
from conftest import GOOD_CHECKOUT, count


def add(c, pid, qty):
    r = c.post("/api/cart/items", json={"product_id": pid, "quantity": qty})
    assert r.status_code in (200, 201), r.text


def stock(db, pid):
    return db.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()[0]


def test_checkout_creates_order_with_correct_totals(alice, db):
    add(alice, 1, 2)
    add(alice, 3, 3)  # subtotal 69.95 -> free shipping
    r = alice.post("/api/checkout", json=GOOD_CHECKOUT)
    assert r.status_code == 201
    o = r.json()
    assert o["status"] == "PLACED" and o["subtotal"] == 69.95 and o["shipping"] == 0.0 and o["total"] == 69.95
    assert o["item_count"] == 5 and len(o["items"]) == 2
    assert count(db, "orders", "id = ?", (o["id"],)) == 1


def test_flat_shipping_below_free_shipping_threshold(alice):
    add(alice, 1, 1)  # 19.99 -> +5.00 shipping
    o = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()
    assert o["subtotal"] == 19.99 and o["shipping"] == 5.0 and o["total"] == 24.99


@pytest.mark.parametrize("qty,shipping,total", [(9, 5.0, 50.0), (10, 0.0, 50.0)])
def test_free_shipping_boundary_at_50(alice, qty, shipping, total):
    add(alice, 6, qty)  # Notebook A5 @ 5.00: 9 -> 45.00 (pays shipping), 10 -> 50.00 (free shipping)
    o = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()
    assert o["shipping"] == shipping and o["total"] == total


def test_checkout_decrements_stock_and_clears_cart(alice, db):
    add(alice, 1, 2)
    alice.post("/api/checkout", json=GOOD_CHECKOUT)
    assert stock(db, 1) == 48
    assert alice.get("/api/cart").json()["items"] == []
    assert count(db, "cart_items") == 0


def test_stored_order_total_matches_item_lines_in_database(alice, db):
    add(alice, 2, 1)
    add(alice, 5, 2)
    oid = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()["id"]
    row = db.execute("SELECT subtotal_cents, shipping_cents, total_cents FROM orders WHERE id=?", (oid,)).fetchone()
    line_sum = db.execute("SELECT SUM(unit_price_cents*quantity), SUM(line_total_cents) FROM order_items WHERE order_id=?", (oid,)).fetchone()
    assert row["subtotal_cents"] == line_sum[0] == line_sum[1]
    assert row["total_cents"] == row["subtotal_cents"] + row["shipping_cents"]


def test_empty_cart_checkout_rejected_and_no_order_created(alice, db):
    before = count(db, "orders")
    r = alice.post("/api/checkout", json=GOOD_CHECKOUT)
    assert r.status_code == 400 and r.json()["error"]["code"] == "empty_cart"
    assert count(db, "orders") == before


@pytest.mark.parametrize("override", [
    {"shipping_name": ""}, {"shipping_name": "A"}, {"shipping_name": "x" * 61},
    {"shipping_address": "1234"}, {"shipping_address": "x" * 201},
    {"payment_method": "VISA"}, {"payment_method": None}, {"shipping_name": 42},
])
def test_invalid_checkout_fields_rejected_and_nothing_changes(alice, db, override):
    add(alice, 1, 1)
    before = (count(db, "orders"), count(db, "order_items"), stock(db, 1))
    r = alice.post("/api/checkout", json={**GOOD_CHECKOUT, **override})
    assert r.status_code == 400
    assert (count(db, "orders"), count(db, "order_items"), stock(db, 1)) == before
    assert count(db, "cart_items") == 1  # cart preserved so the user can retry


@pytest.mark.parametrize("missing", ["shipping_name", "shipping_address", "payment_method"])
def test_checkout_missing_field_rejected(alice, missing):
    add(alice, 1, 1)
    payload = {k: v for k, v in GOOD_CHECKOUT.items() if k != missing}
    assert alice.post("/api/checkout", json=payload).status_code == 400


def test_checkout_fails_cleanly_if_stock_dropped_after_adding(alice, db):
    add(alice, 1, 2)
    db.execute("UPDATE products SET stock = 1 WHERE id = 1")
    before_orders = count(db, "orders")
    r = alice.post("/api/checkout", json=GOOD_CHECKOUT)
    assert r.status_code == 409 and r.json()["error"]["code"] == "insufficient_stock"
    assert count(db, "orders") == before_orders and stock(db, 1) == 1 and count(db, "cart_items") == 1


def test_order_history_lists_only_own_orders_newest_first(alice, bob):
    ids = [o["id"] for o in alice.get("/api/orders").json()["orders"]]
    assert ids == [3, 1]  # seeded alice orders, newest first
    assert [o["id"] for o in bob.get("/api/orders").json()["orders"]] == [2]


def test_new_order_appears_in_history(alice):
    add(alice, 3, 1)
    oid = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()["id"]
    history = alice.get("/api/orders").json()
    assert history["orders"][0]["id"] == oid and history["count"] == 3


def test_order_detail_has_expected_fields_and_types(alice):
    o = alice.get("/api/orders/1").json()
    assert o["status"] == "PLACED" and o["total"] == 59.5 and o["items"][0]["name"] == "Mechanical Keyboard"
    assert isinstance(o["id"], int) and isinstance(o["items"], list) and isinstance(o["total"], float)


def test_order_keeps_price_snapshot_when_catalog_price_changes(alice, db):
    add(alice, 1, 1)
    oid = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()["id"]
    db.execute("UPDATE products SET price_cents = 99999 WHERE id = 1")
    assert alice.get(f"/api/orders/{oid}").json()["items"][0]["unit_price"] == 19.99


def test_cancel_order_restocks_and_sets_status(alice, db):
    add(alice, 1, 2)
    oid = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()["id"]
    assert stock(db, 1) == 48
    r = alice.post(f"/api/orders/{oid}/cancel")
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"
    assert stock(db, 1) == 50


def test_cancelling_twice_returns_409_and_does_not_restock_again(alice, db):
    add(alice, 1, 2)
    oid = alice.post("/api/checkout", json=GOOD_CHECKOUT).json()["id"]
    alice.post(f"/api/orders/{oid}/cancel")
    r = alice.post(f"/api/orders/{oid}/cancel")
    assert r.status_code == 409 and stock(db, 1) == 50


def test_seeded_cancelled_order_cannot_be_cancelled_again(alice):
    assert alice.post("/api/orders/3/cancel").status_code == 409


def test_unknown_order_returns_404(alice):
    assert alice.get("/api/orders/99999").status_code == 404
    assert alice.post("/api/orders/99999/cancel").status_code == 404


def test_orders_and_checkout_require_authentication(client):
    assert client.get("/api/orders").status_code == 401
    assert client.get("/api/orders/1").status_code == 401
    assert client.post("/api/checkout", json=GOOD_CHECKOUT).status_code == 401
    assert client.post("/api/orders/1/cancel").status_code == 401
