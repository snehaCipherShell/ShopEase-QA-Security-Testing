from app import create_app
from conftest import COOKIE


def test_security_headers_present_on_api_and_page(client):
    for path in ("/api/products", "/"):
        h = client.get(path).headers
        assert h["X-Content-Type-Options"] == "nosniff"
        assert h["X-Frame-Options"] == "DENY"
        assert h["Referrer-Policy"] == "no-referrer"
        assert "default-src 'self'" in h["Content-Security-Policy"]


def test_api_json_is_not_cached(client):
    assert client.get("/api/products").headers["Cache-Control"] == "no-store"


def test_server_header_does_not_reveal_framework_versions(client):
    server = client.get("/api/products").headers.get("Server", "")
    assert server == "ShopEase"  # BUG-001 regression: default dev server leaked Werkzeug/Python versions


def test_session_cookie_attributes_for_local_config(client):
    r = client.post("/api/auth/login", json={"username": "alice", "password": "AlicePass123"})
    cookie = r.headers["Set-Cookie"]
    assert cookie.startswith(COOKIE + "=")
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie and "Path=/" in cookie
    assert "Max-Age=3600" in cookie
    assert "Secure" not in cookie  # documented: plain-HTTP localhost; enable via SHOPEASE_COOKIE_SECURE=1 behind HTTPS


def test_secure_flag_is_added_when_configured(server):
    app = create_app({"DATABASE": server.db_path, "PASSWORD_HASH_METHOD": "pbkdf2:sha256:1000", "COOKIE_SECURE": True})
    r = app.test_client().post("/api/auth/login", json={"username": "alice", "password": "AlicePass123"})
    assert "Secure" in r.headers["Set-Cookie"]


def test_logout_expires_cookie(alice):
    r = alice.post("/api/auth/logout")
    assert COOKIE in r.headers["Set-Cookie"] and "Expires=Thu, 01 Jan 1970" in r.headers["Set-Cookie"]


def test_error_responses_do_not_leak_stack_traces_or_paths(client):
    for r in (client.get("/api/nope"), client.post("/api/auth/login", data="{bad", headers={"Content-Type": "application/json"}),
              client.get("/api/products/abc")):
        text = r.text
        assert "Traceback" not in text and "/home/" not in text and "sqlite" not in text.lower()


def test_login_responses_do_not_contain_password_hashes(alice):
    assert "pbkdf2" not in alice.get("/api/auth/me").text


def test_session_token_is_stored_hashed_not_raw(alice, db):
    raw = alice.token
    stored = [r[0] for r in db.execute("SELECT token_hash FROM sessions")]
    assert raw not in stored and len(stored[0]) == 64
