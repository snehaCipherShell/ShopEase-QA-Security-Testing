"""Shared fixtures. Every test gets a brand-new, seeded SQLite database in a temp directory
and its own live ShopEase server on 127.0.0.1 (random free port). Real data is never touched."""
import os
import sqlite3
import sys
import threading

import pytest
import requests
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import ShopEaseRequestHandler, create_app  # noqa: E402
from app.seed import init_database  # noqa: E402

TEST_HASH = "pbkdf2:sha256:1000"  # fast hashing for tests only
COOKIE = "shopease_session"
USERS = {
    "alice": "AlicePass123",
    "bob": "BobPass1234",
    "qa_admin": "AdminPass123",
}
GOOD_CHECKOUT = {"shipping_name": "Test Buyer", "shipping_address": "1 Test Street, Testville", "payment_method": "SIMULATED"}


class ApiClient:
    """Thin wrapper around requests.Session with a base URL."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def request(self, method, path, **kwargs):
        kwargs.setdefault("timeout", 10)
        return self.session.request(method, self.base_url + path, **kwargs)

    def get(self, path, **kw): return self.request("GET", path, **kw)
    def post(self, path, **kw): return self.request("POST", path, **kw)
    def put(self, path, **kw): return self.request("PUT", path, **kw)
    def delete(self, path, **kw): return self.request("DELETE", path, **kw)

    @property
    def token(self):
        return self.session.cookies.get(COOKIE)

    def login(self, username, password):
        r = self.post("/api/auth/login", json={"username": username, "password": password})
        assert r.status_code == 200, r.text
        return r


class Server:
    def __init__(self, base_url, db_path, app):
        self.base_url, self.db_path, self.app = base_url, db_path, app


@pytest.fixture
def server(tmp_path):
    db_path = str(tmp_path / "test_shopease.db")
    assert db_path.startswith(str(tmp_path)), "tests must only use a temp database"
    init_database(db_path, hash_method=TEST_HASH, seed=True)
    app = create_app({"DATABASE": db_path, "PASSWORD_HASH_METHOD": TEST_HASH})
    httpd = make_server("127.0.0.1", 0, app, threaded=True, request_handler=ShopEaseRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield Server(f"http://127.0.0.1:{httpd.server_port}", db_path, app)
    httpd.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def db(server):
    conn = sqlite3.connect(server.db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def client(server):
    return ApiClient(server.base_url)


def _logged_in(server, username):
    c = ApiClient(server.base_url)
    c.login(username, USERS[username])
    return c


@pytest.fixture
def alice(server): return _logged_in(server, "alice")


@pytest.fixture
def bob(server): return _logged_in(server, "bob")


@pytest.fixture
def admin(server): return _logged_in(server, "qa_admin")


def count(db, table, where="1=1", params=()):
    return db.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
