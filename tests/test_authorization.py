import pytest
from conftest import COOKIE, GOOD_CHECKOUT, ApiClient, count

PROTECTED = [
    ("GET", "/api/auth/me"), ("POST", "/api/auth/logout"), ("GET", "/api/cart"), ("POST", "/api/cart/items"),
    ("PUT", "/api/cart/items/1"), ("DELETE", "/api/cart/items/1"), ("DELETE", "/api/cart"), ("POST", "/api/checkout"),
    ("GET", "/api/orders"), ("GET", "/api/orders/1"), ("POST", "/api/orders/1/cancel"), ("GET", "/api/admin/orders"),
]


@pytest.mark.parametrize("method,path", PROTECTED)
def test_protected_endpoints_return_401_when_logged_out(client, method, path):
    kwargs = {"json": {}} if method in ("POST", "PUT") else {}
    r = client.request(method, path, **kwargs)
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthenticated"


@pytest.mark.parametrize("token", ["", "garbage", "A" * 43, "A" * 500, "' OR '1'='1", "../../etc/passwd"])
def test_invalid_session_cookie_is_rejected(server, token):
    c = ApiClient(server.base_url)
    c.session.cookies.set(COOKIE, token)
    assert c.get("/api/orders").status_code == 401


def test_tampered_valid_token_is_rejected(alice, server):
    tampered = alice.token[:-1] + ("A" if alice.token[-1] != "A" else "B")
    c = ApiClient(server.base_url)
    c.session.cookies.set(COOKIE, tampered)
    assert c.get("/api/auth/me").status_code == 401


def test_expired_session_is_rejected(alice, db):
    db.execute("UPDATE sessions SET expires_at = 1")
    assert alice.get("/api/auth/me").status_code == 401


def test_user_cannot_read_another_users_order(alice, bob):
    # Order 2 belongs to bob. Alice must not see any of it.
    r = alice.get("/api/orders/2")
    assert r.status_code == 404
    assert "Bob" not in r.text and "Sampletown" not in r.text
    assert bob.get("/api/orders/2").status_code == 200  # control: the owner can


def test_other_users_order_is_indistinguishable_from_missing_order(alice):
    assert alice.get("/api/orders/2").json() == alice.get("/api/orders/99999").json()  # no ID enumeration oracle


def test_user_cannot_cancel_another_users_order(alice, bob, db):
    assert alice.post("/api/orders/2/cancel").status_code == 404
    assert db.execute("SELECT status FROM orders WHERE id=2").fetchone()[0] == "PLACED"
    assert bob.get("/api/orders/2").json()["status"] == "PLACED"


def test_order_ids_in_list_never_include_other_users(alice):
    owners = {o["id"] for o in alice.get("/api/orders").json()["orders"]}
    assert 2 not in owners


def test_customer_gets_403_on_admin_endpoint(alice):
    r = alice.get("/api/admin/orders")
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_admin_can_list_all_orders(admin):
    r = admin.get("/api/admin/orders")
    assert r.status_code == 200 and r.json()["count"] == 3
    assert {o["username"] for o in r.json()["orders"]} == {"alice", "bob"}


def test_self_registration_cannot_create_admin(client, server):
    client.post("/api/auth/register", json={"username": "sneaky", "email": "s@example.test", "password": "Passw0rd1", "role": "admin"})
    c = ApiClient(server.base_url)
    c.login("sneaky", "Passw0rd1")
    assert c.get("/api/admin/orders").status_code == 403


def test_checkout_uses_authenticated_user_not_body_user_id(alice, db):
    alice.post("/api/cart/items", json={"product_id": 3, "quantity": 1})
    r = alice.post("/api/checkout", json={**GOOD_CHECKOUT, "user_id": 2})
    assert r.status_code == 201
    owner = db.execute("SELECT user_id FROM orders WHERE id=?", (r.json()["id"],)).fetchone()[0]
    assert owner == 1  # alice, not bob


def test_price_tampering_at_checkout_is_ignored(alice):
    alice.post("/api/cart/items", json={"product_id": 2, "quantity": 1, "price": 0.01})
    o = alice.post("/api/checkout", json={**GOOD_CHECKOUT, "total": 0.01, "subtotal": 0.01, "shipping": 0}).json()
    assert o["total"] == 59.50


def test_logging_out_one_user_does_not_log_out_another(alice, bob):
    alice.post("/api/auth/logout")
    assert bob.get("/api/auth/me").status_code == 200
