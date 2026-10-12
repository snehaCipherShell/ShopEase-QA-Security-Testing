import pytest
from conftest import COOKIE, ApiClient, count

VALID = {"username": "new_user1", "email": "new_user1@example.test", "password": "Passw0rdOK"}


def test_register_success_returns_201_and_no_password(client, db):
    r = client.post("/api/auth/register", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "new_user1" and body["email"] == VALID["email"]
    assert isinstance(body["id"], int)
    assert "password" not in body and "password_hash" not in body
    assert count(db, "users", "username = ?", ("new_user1",)) == 1


def test_register_stores_hashed_password_not_plaintext(client, db):
    client.post("/api/auth/register", json=VALID)
    stored = db.execute("SELECT password_hash FROM users WHERE username='new_user1'").fetchone()[0]
    assert stored != VALID["password"] and VALID["password"] not in stored
    assert stored.startswith("pbkdf2:sha256")


@pytest.mark.parametrize("username", ["ab", "a" * 21, "has space", "semi;colon", "", "<script>"])
def test_register_rejects_invalid_username(client, db, username):
    before = count(db, "users")
    r = client.post("/api/auth/register", json={**VALID, "username": username})
    assert r.status_code == 400
    assert "username" in r.json()["error"]["fields"]
    assert count(db, "users") == before


@pytest.mark.parametrize("username", ["abc", "a" * 20])
def test_register_accepts_username_length_boundaries(client, username):
    r = client.post("/api/auth/register", json={**VALID, "username": username, "email": username + "@example.test"})
    assert r.status_code == 201


@pytest.mark.parametrize("password,expected", [
    ("Abcdef1", 400),        # 7 chars: just below minimum
    ("Abcdef12", 201),       # 8 chars: minimum
    ("A1" + "b" * 62, 201),  # 64 chars: maximum
    ("A1" + "b" * 63, 400),  # 65 chars: just above maximum
    ("abcdefgh", 400),       # no digit
    ("12345678", 400),       # no letter
])
def test_register_password_boundaries(client, password, expected):
    r = client.post("/api/auth/register", json={**VALID, "password": password})
    assert r.status_code == expected


@pytest.mark.parametrize("email", ["plainaddress", "no@tld", "@example.test", "a b@example.test", ""])
def test_register_rejects_invalid_email(client, email):
    r = client.post("/api/auth/register", json={**VALID, "email": email})
    assert r.status_code == 400 and "email" in r.json()["error"]["fields"]


@pytest.mark.parametrize("missing", ["username", "email", "password"])
def test_register_missing_required_field(client, db, missing):
    payload = {k: v for k, v in VALID.items() if k != missing}
    before = count(db, "users")
    r = client.post("/api/auth/register", json=payload)
    assert r.status_code == 400 and missing in r.json()["error"]["fields"]
    assert count(db, "users") == before


def test_register_duplicate_username_case_insensitive_returns_409(client, db):
    before = count(db, "users")
    r = client.post("/api/auth/register", json={**VALID, "username": "ALICE"})
    assert r.status_code == 409
    assert count(db, "users") == before


def test_register_duplicate_email_returns_409(client):
    r = client.post("/api/auth/register", json={**VALID, "email": "alice@example.test"})
    assert r.status_code == 409


def test_login_success_sets_session_cookie_and_me_works(client):
    r = client.login("alice", "AlicePass123")
    assert r.json()["username"] == "alice" and r.json()["role"] == "customer"
    assert COOKIE in client.session.cookies
    me = client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["username"] == "alice"
    assert "password_hash" not in me.json()


def test_login_is_case_insensitive_for_username(client):
    assert client.post("/api/auth/login", json={"username": "ALICE", "password": "AlicePass123"}).status_code == 200


def test_login_wrong_password_returns_401_without_cookie(client):
    r = client.post("/api/auth/login", json={"username": "alice", "password": "WrongPass123"})
    assert r.status_code == 401 and COOKIE not in client.session.cookies


def test_login_unknown_user_message_matches_wrong_password(client):
    unknown = client.post("/api/auth/login", json={"username": "nobody", "password": "WrongPass123"})
    wrong = client.post("/api/auth/login", json={"username": "alice", "password": "WrongPass123"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()  # no username enumeration through the message


@pytest.mark.parametrize("payload", [{}, {"username": "alice"}, {"password": "x"}, {"username": "", "password": ""},
                                     {"username": 123, "password": "x"}])
def test_login_missing_or_wrong_type_fields_return_400(client, payload):
    assert client.post("/api/auth/login", json=payload).status_code == 400


def test_sql_injection_string_in_login_does_not_authenticate(client, db):
    users_before = count(db, "users")
    r = client.post("/api/auth/login", json={"username": "alice' OR '1'='1' --", "password": "x"})
    assert r.status_code == 401
    assert count(db, "users") == users_before


def test_logout_requires_login(client):
    assert client.post("/api/auth/logout").status_code == 401


def test_logout_invalidates_server_side_session(alice, server):
    old_token = alice.token
    assert alice.post("/api/auth/logout").status_code == 200
    replay = ApiClient(server.base_url)
    replay.session.cookies.set(COOKIE, old_token)
    assert replay.get("/api/auth/me").status_code == 401  # old cookie is dead on the server


def test_logout_removes_session_row(alice, db):
    assert count(db, "sessions") == 1
    alice.post("/api/auth/logout")
    assert count(db, "sessions") == 0


def test_each_login_issues_a_new_token(server):
    c = ApiClient(server.base_url)
    c.login("alice", "AlicePass123")
    first = c.token
    c.login("alice", "AlicePass123")
    assert c.token != first
