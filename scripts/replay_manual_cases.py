"""Replay the steps of the manual (TC-*) and security (SEC-*) cases over real HTTP at API level.

- Starts ShopEase on 127.0.0.1 with a NEW temporary database; never touches instance/shopease.db.
- Prints PASS/FAIL per case. UI-only expectations (messages on screen, DevTools clicks) are NOT covered.
- This is NOT pytest and NOT Postman; it supports the manual execution report with reproducible API-level results.
Run from the repository root with the virtual environment active:  python scripts/replay_manual_cases.py
"""
import logging
import os
import sqlite3
import sys
import tempfile
import threading

import requests
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import ShopEaseRequestHandler, create_app  # noqa: E402
from app.seed import init_database  # noqa: E402

HASH = "pbkdf2:sha256:1000"
COOKIE = "shopease_session"
GOOD = {"shipping_name": "Test Buyer", "shipping_address": "1 Test Street, Testville", "payment_method": "SIMULATED"}
results = []


def new_env():
    path = os.path.join(tempfile.mkdtemp(), "replay.db")
    init_database(path, hash_method=HASH)
    app = create_app({"DATABASE": path, "PASSWORD_HASH_METHOD": HASH})
    app.logger.disabled = True
    logging.getLogger("werkzeug").disabled = True
    srv = make_server("127.0.0.1", 0, app, threaded=True, request_handler=ShopEaseRequestHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return path, f"http://127.0.0.1:{srv.server_port}", srv


class C:
    def __init__(self, base, user=None, pw=None):
        self.b, self.s = base, requests.Session()
        if user:
            assert self.post("/api/auth/login", json={"username": user, "password": pw}).status_code == 200

    def req(self, m, p, **k): return self.s.request(m, self.b + p, timeout=10, **k)
    def get(self, p, **k): return self.req("GET", p, **k)
    def post(self, p, **k): return self.req("POST", p, **k)
    def put(self, p, **k): return self.req("PUT", p, **k)
    def delete(self, p, **k): return self.req("DELETE", p, **k)


def case(cid, title, fn):
    """Run one case in a fresh environment; PASS only if every check is true."""
    path, base, srv = new_env()
    db = sqlite3.connect(path, isolation_level=None)
    checks = []
    def ok(cond, note): checks.append((bool(cond), note))
    try:
        fn(base, db, ok)
    except Exception as exc:  # a crash is a FAIL, never a silent pass
        checks.append((False, f"exception: {type(exc).__name__}: {exc}"))
    finally:
        srv.shutdown(); db.close()
    status = "PASS" if checks and all(c for c, _ in checks) else "FAIL"
    results.append((cid, title, status, checks))


def n(db, table, where="1=1", args=()): return db.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", args).fetchone()[0]
def stock(db, pid=1): return db.execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()[0]
def add(c, pid, q): return c.post("/api/cart/items", json={"product_id": pid, "quantity": q})
REG = {"username": "qa_tester1", "email": "qa_tester1@example.test", "password": "Passw0rd1"}

def t_reg1(b, db, ok):
    r = C(b).post("/api/auth/register", json=REG); j = r.json()
    ok(r.status_code == 201, f"status {r.status_code}"); ok(j.get("username") == "qa_tester1" and j.get("role") == "customer", "body fields")
    ok("password" not in j and "password_hash" not in j, "no password fields in response")
    h = db.execute("SELECT password_hash FROM users WHERE username='qa_tester1'").fetchone()
    ok(n(db, "users", "username='qa_tester1'") == 1 and h and h[0] != REG["password"], "1 DB row, hash differs from password")
def t_reg2(b, db, ok):
    before = n(db, "users"); r = C(b).post("/api/auth/register", json={**REG, "username": "ALICE"})
    ok(r.status_code == 409, f"status {r.status_code}"); ok(n(db, "users") == before, "no new row")
def t_reg3(b, db, ok):
    r = C(b).post("/api/auth/register", json={**REG, "password": "Abcdef1"})
    ok(r.status_code == 400 and "password" in r.json()["error"]["fields"], f"status {r.status_code}, password field error"); ok(n(db, "users", "username='qa_tester1'") == 0, "no row")
def t_reg4(b, db, ok): ok(C(b).post("/api/auth/register", json={**REG, "password": "Abcdef12"}).status_code == 201, "8-char password accepted (201)")
def t_log1(b, db, ok):
    c = C(b); r = c.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123"}); sc = r.headers.get("Set-Cookie", "")
    ok(r.status_code == 200, "login 200"); ok(COOKIE in c.s.cookies, "session cookie set"); ok("HttpOnly" in sc and "SameSite=Lax" in sc, "HttpOnly + SameSite=Lax")
    ok(c.get("/api/auth/me").json()["username"] == "alice", "me returns alice"); ok(c.get("/api/cart").status_code == 200 and c.get("/api/orders").status_code == 200, "cart and orders load")
def t_log2(b, db, ok):
    c = C(b); r = c.post("/api/auth/login", json={"username": "alice", "password": "WrongPass123"}); ok(r.status_code == 401, "401"); ok(COOKIE not in c.s.cookies, "no cookie")
def t_log3(b, db, ok):
    c = C(b, "alice", "AlicePass123"); ok(n(db, "sessions") == 1, "1 session row before"); ok(c.post("/api/auth/logout").status_code == 200, "logout 200")
    ok(c.get("/api/auth/me").status_code == 401, "me -> 401 after logout"); ok(n(db, "sessions") == 0, "session row removed")
def t_src(q, names):
    def f(b, db, ok):
        r = C(b).get("/api/products", params={"q": q}); got = [p["name"] for p in r.json()["products"]]
        ok(r.status_code == 200 and got == names, f"{q!r} -> {got}")
    return f
def t_crt1(b, db, ok):
    r = add(C(b, "alice", "AlicePass123"), 1, 2); ok(r.status_code == 201 and r.json()["subtotal"] == 39.98, f"{r.status_code} subtotal {r.json().get('subtotal')}")
def t_crt2(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 1, 2); r = c.put("/api/cart/items/1", json={"quantity": 5}); j = r.json()
    ok(r.status_code == 200 and j["items"][0]["line_total"] == 99.95 and j["subtotal"] == 99.95, f"line {j['items'][0]['line_total']} subtotal {j['subtotal']}")
def t_crt3(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 1, 1); add(c, 3, 1); r = c.delete("/api/cart/items/1"); ok(r.status_code == 200 and [i["product_id"] for i in r.json()["items"]] == [3] and r.json()["subtotal"] == 9.99, "line removed, subtotal 9.99")
def t_qty(q, status, subtotal=None):
    def f(b, db, ok):
        c = C(b, "alice", "AlicePass123"); r = add(c, 1, q); ok(r.status_code == status, f"qty {q} -> {r.status_code}")
        if subtotal is not None: ok(r.json()["subtotal"] == subtotal, f"subtotal {r.json()['subtotal']}")
        if status == 400: ok(n(db, "cart_items") == 0, "cart unchanged")
    return f
def t_crt7(b, db, ok): r = add(C(b, "alice", "AlicePass123"), 7, 1); ok(r.status_code == 409 and r.json()["error"]["code"] == "insufficient_stock", "409 insufficient_stock"); ok(n(db, "cart_items") == 0, "cart unchanged")
def t_cal1(b, db, ok): c = C(b, "alice", "AlicePass123"); add(c, 1, 2); add(c, 3, 3); ok(c.get("/api/cart").json()["subtotal"] == 69.95, "subtotal 69.95")
def t_cal2(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 6, 9); a = c.post("/api/checkout", json=GOOD).json(); add(c, 6, 10); bb = c.post("/api/checkout", json=GOOD).json()
    ok(a["shipping"] == 5.0 and a["total"] == 50.0, f"9 notebooks: shipping {a['shipping']} total {a['total']}"); ok(bb["shipping"] == 0.0 and bb["total"] == 50.0, f"10 notebooks: shipping {bb['shipping']} total {bb['total']}")
def t_chk1(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 1, 2); r = c.post("/api/checkout", json=GOOD); o = r.json(); oid = o["id"]
    ok(r.status_code == 201 and o["status"] == "PLACED" and o["total"] == 44.98 and o["shipping"] == 5.0, f"{r.status_code} total {o['total']}")
    ok(c.get("/api/cart").json()["items"] == [] and stock(db) == 48, "cart empty, stock 48")
    row = db.execute("SELECT user_id,subtotal_cents,shipping_cents,total_cents FROM orders WHERE id=?", (oid,)).fetchone(); li = db.execute("SELECT SUM(line_total_cents) FROM order_items WHERE order_id=?", (oid,)).fetchone()[0]
    ok(row[0] == 1 and row[1] == li and row[3] == row[1] + row[2], "DB: owner alice, totals consistent")
def t_chk2(b, db, ok): before = n(db, "orders"); r = C(b, "alice", "AlicePass123").post("/api/checkout", json=GOOD); ok(r.status_code == 400 and r.json()["error"]["code"] == "empty_cart", "400 empty_cart"); ok(n(db, "orders") == before, "no order")
def t_chk3(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 1, 1); before = n(db, "orders"); r = c.post("/api/checkout", json={**GOOD, "shipping_address": ""})
    ok(r.status_code == 400 and "shipping_address" in r.json()["error"]["fields"], "400 shipping_address error"); ok(n(db, "orders") == before and n(db, "cart_items") == 1, "no order, cart preserved")
def t_ord1(b, db, ok):
    a = [o["id"] for o in C(b, "alice", "AlicePass123").get("/api/orders").json()["orders"]]; bo = [o["id"] for o in C(b, "bob", "BobPass1234").get("/api/orders").json()["orders"]]
    ok(a == [3, 1], f"alice {a}"); ok(bo == [2], f"bob {bo}")
def t_ord2(b, db, ok):
    c = C(b, "alice", "AlicePass123"); add(c, 1, 2); oid = c.post("/api/checkout", json=GOOD).json()["id"]; r = c.post(f"/api/orders/{oid}/cancel")
    ok(r.status_code == 200 and r.json()["status"] == "CANCELLED", "CANCELLED"); ok(stock(db) == 50, "stock restored to 50"); ok(c.post(f"/api/orders/{oid}/cancel").status_code == 409, "second cancel 409")

def s_auth1(b, db, ok):
    c = C(b)
    for m, p in [("GET", "/api/cart"), ("GET", "/api/orders"), ("POST", "/api/checkout"), ("GET", "/api/admin/orders")]: ok(c.req(m, p, json={}).status_code == 401, f"{m} {p} -> 401")
def s_auth2(b, db, ok):
    u = C(b).post("/api/auth/login", json={"username": "nobody", "password": "WrongPass123"}); w = C(b).post("/api/auth/login", json={"username": "alice", "password": "WrongPass123"}); ok(u.status_code == w.status_code == 401 and u.json() == w.json(), "identical 401 bodies")
def s_auth3(b, db, ok): h = db.execute("SELECT password_hash FROM users WHERE username='alice'").fetchone()[0]; ok("AlicePass123" not in h and h.startswith("pbkdf2:"), "hashed (test config pbkdf2); production default is scrypt")
def s_auth4(b, db, ok): before = n(db, "users"); r = C(b).post("/api/auth/login", json={"username": "alice' OR '1'='1' --", "password": "x"}); ok(r.status_code == 401 and n(db, "sessions") == 0 and n(db, "users") == before, "401, no session, tables intact")
def s_sess1(b, db, ok):
    c = C(b, "alice", "AlicePass123"); old = c.s.cookies.get(COOKIE); c.post("/api/auth/logout"); r = C(b); r.s.cookies.set(COOKIE, old); ok(r.get("/api/auth/me").status_code == 401, "old cookie replay -> 401 after logout")
def s_sess2(b, db, ok):
    c = C(b, "alice", "AlicePass123"); t = c.s.cookies.get(COOKIE)
    for v in ["", "garbage", "A" * 500, "' OR '1'='1", t[:-1] + ("A" if t[-1] != "A" else "B")]:
        x = C(b); x.s.cookies.set(COOKIE, v); ok(x.get("/api/orders").status_code == 401, "bad cookie variant -> 401")
def s_sess3(b, db, ok): c = C(b, "alice", "AlicePass123"); db.execute("UPDATE sessions SET expires_at=1"); ok(c.get("/api/auth/me").status_code == 401, "expired -> 401")
def s_sess4(b, db, ok):
    sc = C(b).post("/api/auth/login", json={"username": "alice", "password": "AlicePass123"}).headers["Set-Cookie"]
    ok(all(x in sc for x in ("HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=3600")) and "Secure" not in sc, "HttpOnly, SameSite=Lax, Path=/, Max-Age=3600, no Secure (local HTTP)")
def s_sess5(b, db, ok): c = C(b, "alice", "AlicePass123"); t1 = c.s.cookies.get(COOKIE); c.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123"}); ok(c.s.cookies.get(COOKIE) != t1, "new token each login")
def s_az1(b, db, ok):
    a, bo = C(b, "alice", "AlicePass123"), C(b, "bob", "BobPass1234"); r2, r99 = a.get("/api/orders/2"), a.get("/api/orders/99999")
    ok(r2.status_code == 404 and r2.json() == r99.json(), "alice: order 2 -> 404, same body as missing order"); ok("Bob" not in r2.text and "Sampletown" not in r2.text, "no bob data"); ok(bo.get("/api/orders/2").status_code == 200, "control: bob -> 200")
def s_az2(b, db, ok): r = C(b, "alice", "AlicePass123").post("/api/orders/2/cancel"); ok(r.status_code == 404, "404"); ok(db.execute("SELECT status FROM orders WHERE id=2").fetchone()[0] == "PLACED", "order 2 still PLACED")
def s_az3(b, db, ok): ok(C(b, "alice", "AlicePass123").get("/api/admin/orders").status_code == 403, "customer 403"); ok(C(b, "qa_admin", "AdminPass123").get("/api/admin/orders").status_code == 200, "admin 200")
def s_az4(b, db, ok):
    c = C(b); j = c.post("/api/auth/register", json={**REG, "role": "admin", "is_admin": True}).json(); ok(j["role"] == "customer", "role stays customer")
    a = C(b, "alice", "AlicePass123"); add(a, 3, 1); oid = a.post("/api/checkout", json={**GOOD, "user_id": 2}).json()["id"]; ok(db.execute("SELECT user_id FROM orders WHERE id=?", (oid,)).fetchone()[0] == 1, "order owned by alice, body user_id ignored")
def s_in1(b, db, ok):
    c = C(b); J = {"Content-Type": "application/json"}
    ok(c.post("/api/auth/login", data="u=a", headers={"Content-Type": "application/x-www-form-urlencoded"}).status_code == 415, "form body -> 415")
    ok(c.post("/api/auth/login", data="{bad", headers=J).status_code == 400, "broken JSON -> 400"); ok(c.post("/api/auth/register", data="[]", headers=J).status_code == 400, "JSON array -> 400")
    ok(c.post("/api/auth/register", json={"username": "x" * 20000, "email": "a@b.co", "password": "Passw0rd1"}).status_code == 413, "20 KB body -> 413")
    ok(c.get("/api/nope").status_code == 404 and c.delete("/api/products").status_code == 405, "404 unknown route, 405 wrong method")
    ok(all("Traceback" not in x.text and "sqlite" not in x.text.lower() for x in (c.get("/api/nope"), c.get("/api/products/abc"))), "no stack trace / SQL text in errors")
def s_in2(b, db, ok):
    c = C(b)
    for q in ["' OR '1'='1", "'; DROP TABLE products; --", "<script>alert(1)</script>", "%", "_"]:
        r = c.get("/api/products", params={"q": q}); ok(r.status_code == 200 and r.json()["count"] == 0, f"{q!r} -> 200, 0 results")
    ok(n(db, "products") == 8, "products table intact"); ok("<script>" not in c.get("/api/products", params={"q": "<script>"}).text, "script text not reflected")
def s_pr(b, db, ok):
    c = C(b, "alice", "AlicePass123"); r = c.post("/api/cart/items", json={"product_id": 2, "quantity": 1, "price": 0.01}); ok(r.json()["items"][0]["unit_price"] == 59.5, "(a) client price 0.01 ignored, 59.5 used")
    o = c.post("/api/checkout", json={**GOOD, "total": 0.01, "subtotal": 0.01, "shipping": 0}).json(); ok(o["total"] == 59.5, f"(b) checkout total {o['total']} despite tampered total fields")
    for q in (-1, 0, 11, "5", 1.5, True, None): ok(add(c, 1, q).status_code == 400, f"(c) quantity {q!r} -> 400")
    ok(n(db, "cart_items") == 0, "(c) nothing stored"); ok(True, "(d) editing the HTML input in DevTools = same server request as (c): server validation shown; browser step itself NOT run")
def s_hdr(b, db, ok):
    h = C(b).get("/api/products").headers
    ok(h.get("Server") == "ShopEase", "Server: ShopEase"); ok(h.get("X-Content-Type-Options") == "nosniff" and h.get("X-Frame-Options") == "DENY" and h.get("Referrer-Policy") == "no-referrer", "nosniff / DENY / no-referrer")
    ok("default-src 'self'" in h.get("Content-Security-Policy", "") and h.get("Cache-Control") == "no-store", "CSP + no-store")
def b2(b, db, ok):
    c = C(b, "alice", "AlicePass123")
    for big in (2 ** 63, 10 ** 30):
        codes = [c.get(f"/api/products/{big}").status_code, c.get(f"/api/orders/{big}").status_code, c.post(f"/api/orders/{big}/cancel").status_code, c.put(f"/api/cart/items/{big}", json={"quantity": 1}).status_code, c.delete(f"/api/cart/items/{big}").status_code]
        ok(codes == [404] * 5, f"id {big}: path routes {codes}"); ok(add(c, big, 1).status_code == 400, f"id {big}: body product_id -> 400")
    ok(c.get(f"/api/products/{2**63-1}").status_code == 404 and c.get("/api/products/1").status_code == 200, "boundary 2^63-1 -> 404; normal id still 200")

CASES = [("TC-REG-001", "Register with valid details", t_reg1), ("TC-REG-002", "Duplicate username (case variation)", t_reg2), ("TC-REG-003", "7-char password rejected", t_reg3), ("TC-REG-004", "8-char password accepted", t_reg4),
 ("TC-LOG-001", "Login valid", t_log1), ("TC-LOG-002", "Login wrong password", t_log2), ("TC-LOG-003", "Logout closes session", t_log3),
 ("TC-SRC-001", "Search 'mouse'", t_src("mouse", ["Wireless Mouse"])), ("TC-SRC-002", "Search no match", t_src("zzzz-nothing", [])), ("TC-SRC-003", "Search case-insensitive 'LAPTOP'", t_src("LAPTOP", ["Laptop Stand"])),
 ("TC-CRT-001", "Add to cart", t_crt1), ("TC-CRT-002", "Update quantity", t_crt2), ("TC-CRT-003", "Remove item", t_crt3), ("TC-CRT-004", "Quantity 0 rejected", t_qty(0, 400)), ("TC-CRT-005", "Quantity 10 accepted", t_qty(10, 201, 199.9)),
 ("TC-CRT-006", "Quantity 11 rejected", t_qty(11, 400)), ("TC-CRT-007", "Out-of-stock product", t_crt7), ("TC-CAL-001", "Subtotal two products", t_cal1), ("TC-CAL-002", "Free-shipping boundary 45.00 vs 50.00", t_cal2),
 ("TC-CHK-001", "Successful checkout", t_chk1), ("TC-CHK-002", "Checkout empty cart", t_chk2), ("TC-CHK-003", "Checkout missing address", t_chk3), ("TC-ORD-001", "Order history own orders only", t_ord1), ("TC-ORD-002", "Cancel and restock", t_ord2),
 ("SEC-AUTH-001", "Protected routes logged out", s_auth1), ("SEC-AUTH-002", "Login message / enumeration", s_auth2), ("SEC-AUTH-003", "Password stored hashed", s_auth3), ("SEC-AUTH-004", "SQL-injection-style login", s_auth4),
 ("SEC-SESS-001", "Session invalid after logout (cookie replay)", s_sess1), ("SEC-SESS-002", "Invalid / tampered cookies", s_sess2), ("SEC-SESS-003", "Expired session", s_sess3), ("SEC-SESS-004", "Cookie attributes", s_sess4), ("SEC-SESS-005", "New token each login", s_sess5),
 ("SEC-AUTHZ-001", "Alice reads Bob's order (IDOR)", s_az1), ("SEC-AUTHZ-002", "Alice cancels Bob's order", s_az2), ("SEC-AUTHZ-003", "Customer vs admin endpoint", s_az3), ("SEC-AUTHZ-004", "Role / user_id manipulation", s_az4),
 ("SEC-INPUT-001", "Malformed requests / error handling", s_in1), ("SEC-INPUT-002", "Injection / script-like search input", s_in2), ("SEC-PRICE-001", "Price, total, quantity tampering", s_pr), ("SEC-HDR-001", "Security headers and banner", s_hdr),
 ("BUG-002-REG", "Out-of-range IDs (BUG-002 regression)", b2)]

if __name__ == "__main__":
    for cid, title, fn in CASES: case(cid, title, fn)
    print(f"{'ID':<14} {'RESULT':<6} TITLE")
    for cid, title, status, checks in results:
        print(f"{cid:<14} {status:<6} {title}")
        for good, note in checks:
            if status == "FAIL" or "NOT run" in note: print(f"      {'ok ' if good else 'BAD'} {note}")
    p = sum(r[2] == "PASS" for r in results); print(f"\n{p} PASS, {len(results) - p} FAIL out of {len(results)} (API-level replay; not pytest, not Postman)")
    sys.exit(0 if p == len(results) else 1)
