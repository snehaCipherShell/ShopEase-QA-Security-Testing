import hashlib
import time
from functools import wraps
from flask import g, request
from .db import get_db
from .errors import ApiError

COOKIE_NAME = "shopease_session"


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def current_user():
    """Resolve the session cookie to a user via the SERVER-side sessions table."""
    if "_user" in g.__dict__:
        return g._user
    user = None
    token = request.cookies.get(COOKIE_NAME)
    if token and len(token) <= 128:
        row = get_db().execute(
            "SELECT u.id, u.username, u.email, u.role FROM sessions s JOIN users u ON u.id = s.user_id "
            "WHERE s.token_hash = ? AND s.expires_at > ?",
            (hash_token(token), int(time.time())),
        ).fetchone()
        user = dict(row) if row else None
    g._user = user
    return user


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            raise ApiError(401, "unauthenticated", "Authentication required.")
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user()["role"] != "admin":
            raise ApiError(403, "forbidden", "You do not have permission to perform this action.")
        return fn(*args, **kwargs)
    return wrapper
