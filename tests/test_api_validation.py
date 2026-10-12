import pytest
from conftest import count


def test_non_json_content_type_returns_415(client):
    r = client.post("/api/auth/login", data="username=alice&password=x", headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 415 and r.json()["error"]["code"] == "unsupported_media_type"


def test_malformed_json_returns_400(client):
    r = client.post("/api/auth/login", data="{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_json"


@pytest.mark.parametrize("body", ["[]", '"text"', "123", "null"])
def test_json_body_must_be_an_object(client, body):
    r = client.post("/api/auth/register", data=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 400


def test_empty_body_returns_400(client):
    assert client.post("/api/auth/login", data="", headers={"Content-Type": "application/json"}).status_code == 400


def test_unknown_route_returns_json_404(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_wrong_method_returns_405_with_allow_header(client):
    r = client.delete("/api/products")
    assert r.status_code == 405 and "GET" in r.headers.get("Allow", "")


def test_error_responses_share_one_shape(client):
    for r in (client.get("/api/cart"), client.get("/api/nope"), client.post("/api/auth/login", json={})):
        err = r.json()["error"]
        assert set(err) >= {"code", "message"} and isinstance(err["code"], str) and isinstance(err["message"], str)


def test_oversized_body_is_rejected(client):
    r = client.post("/api/auth/register", json={"username": "x" * 20000, "email": "a@b.co", "password": "Passw0rd1"})
    assert r.status_code == 413


def test_very_long_register_values_rejected_without_server_error(client, db):
    before = count(db, "users")
    r = client.post("/api/auth/register", json={"username": "u" * 5000, "email": "a" * 5000 + "@b.co", "password": "P1" + "x" * 5000})
    assert r.status_code == 400 and count(db, "users") == before


def test_unicode_and_null_byte_inputs_do_not_cause_server_errors(client):
    for value in ["\u00e9\u00e8\u4e2d\u6587", "abc\x00def", "\ud83d\ude00".encode("utf-16", "surrogatepass").decode("utf-16")]:
        r = client.post("/api/auth/register", json={"username": value, "email": "x@example.test", "password": "Passw0rd1"})
        assert r.status_code == 400
        assert client.get("/api/products", params={"q": value}).status_code == 200


def test_extra_unknown_fields_are_ignored_not_trusted(client, db):
    r = client.post("/api/auth/register", json={"username": "extra_fields", "email": "ef@example.test",
                                                 "password": "Passw0rd1", "role": "admin", "is_admin": True})
    assert r.status_code == 201 and r.json()["role"] == "customer"
    assert db.execute("SELECT role FROM users WHERE username='extra_fields'").fetchone()[0] == "customer"


def test_json_responses_use_json_content_type(client):
    assert client.get("/api/products").headers["Content-Type"].startswith("application/json")
