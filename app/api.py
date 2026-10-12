"""ShopEase REST API. Prices are ALWAYS read from the products table, never from the client."""
import re
import secrets
import sqlite3
import time
from flask import Blueprint, g, jsonify, request, current_app
from werkzeug.security import check_password_hash, generate_password_hash
from .auth import COOKIE_NAME, current_user, hash_token, login_required, admin_required
from .db import get_db
from .errors import ApiError

bp = Blueprint("api", __name__, url_prefix="/api")

USERNAME_RE = re.compile(r"[A-Za-z0-9_]{3,20}")
EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
MAX_QTY = 10
MAX_ID = 2**63 - 1  # SQLite integers are signed 64-bit; larger values raise OverflowError
SHIPPING_FLAT_CENTS = 500
FREE_SHIPPING_THRESHOLD_CENTS = 5000
_dummy_hashes = {}


@bp.url_value_preprocessor
def reject_out_of_range_ids(endpoint, values):
    """BUG-002: an ID that SQLite cannot store can never exist, so answer 404 instead of crashing with a 500."""
    for value in (values or {}).values():
        if isinstance(value, int) and value > MAX_ID:
            raise ApiError(404, "not_found", "Resource not found.")


def money(cents):
    return round(cents / 100, 2)


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def json_body():
    if request.mimetype != "application/json":
        raise ApiError(415, "unsupported_media_type", "Content-Type must be application/json.")
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError(400, "invalid_json", "Request body is not valid JSON.")
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_json", "Request body must be a JSON object.")
    return data


def validate_quantity(value):
    if not is_int(value) or not 1 <= value <= MAX_QTY:
        raise ApiError(400, "validation_error", f"quantity must be an integer between 1 and {MAX_QTY}.",
                       {"quantity": f"integer 1-{MAX_QTY}"})
    return value


# ---------------------------------------------------------------- auth
@bp.post("/auth/register")
def register():
    body = json_body()
    username, email, password = body.get("username"), body.get("email"), body.get("password")
    fields = {}
    if not isinstance(username, str) or not USERNAME_RE.fullmatch(username):
        fields["username"] = "3-20 characters: letters, digits, underscore"
    if not isinstance(email, str) or len(email) > 254 or not EMAIL_RE.fullmatch(email):
        fields["email"] = "must be a valid email address"
    if (not isinstance(password, str) or not 8 <= len(password) <= 64
            or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password)):
        fields["password"] = "8-64 characters with at least one letter and one digit"
    if fields:
        raise ApiError(400, "validation_error", "One or more fields are invalid.", fields)
    db = get_db()
    method = current_app.config["PASSWORD_HASH_METHOD"]
    try:
        cur = db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, generate_password_hash(password, method=method)),
        )
    except sqlite3.IntegrityError:
        raise ApiError(409, "conflict", "Username or email is already registered.")
    return jsonify({"id": cur.lastrowid, "username": username, "email": email, "role": "customer"}), 201


@bp.post("/auth/login")
def login():
    body = json_body()
    username, password = body.get("username"), body.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        raise ApiError(400, "validation_error", "username and password are required.")
    if len(username) > 64 or len(password) > 256:
        raise ApiError(401, "invalid_credentials", "Invalid username or password.")
    db = get_db()
    row = db.execute("SELECT id, username, role, password_hash FROM users WHERE username = ?", (username,)).fetchone()
    method = current_app.config["PASSWORD_HASH_METHOD"]
    if row is None:  # spend similar time for unknown users
        if method not in _dummy_hashes:
            _dummy_hashes[method] = generate_password_hash("not-a-real-password-1", method=method)
        check_password_hash(_dummy_hashes[method], password)
        raise ApiError(401, "invalid_credentials", "Invalid username or password.")
    if not check_password_hash(row["password_hash"], password):
        raise ApiError(401, "invalid_credentials", "Invalid username or password.")
    now = int(time.time())
    ttl = current_app.config["SESSION_TTL_SECONDS"]
    db.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
    token = secrets.token_urlsafe(32)  # always a NEW token at login (no session fixation)
    db.execute("INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?,?,?,?)",
               (hash_token(token), row["id"], now, now + ttl))
    resp = jsonify({"id": row["id"], "username": row["username"], "role": row["role"], "message": "Logged in."})
    resp.set_cookie(COOKIE_NAME, token, max_age=ttl, httponly=True, samesite="Lax",
                    secure=current_app.config["COOKIE_SECURE"], path="/")
    return resp


@bp.post("/auth/logout")
@login_required
def logout():
    get_db().execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(request.cookies[COOKIE_NAME]),))
    resp = jsonify({"message": "Logged out."})
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


@bp.get("/auth/me")
@login_required
def me():
    return jsonify(current_user())


# ---------------------------------------------------------------- products
def product_json(row):
    return {"id": row["id"], "sku": row["sku"], "name": row["name"], "description": row["description"],
            "category": row["category"], "price": money(row["price_cents"]), "stock": row["stock"]}


@bp.get("/products")
def list_products():
    q = request.args.get("q", "").strip()
    if len(q) > 100:
        raise ApiError(400, "validation_error", "q must be at most 100 characters.", {"q": "max 100 characters"})
    sql, params = "SELECT * FROM products", []
    if q:
        escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " WHERE name LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\'"
        params = [f"%{escaped}%", f"%{escaped}%"]
    rows = get_db().execute(sql + " ORDER BY id", params).fetchall()  # parameterised: no SQL built from input
    return jsonify({"count": len(rows), "products": [product_json(r) for r in rows]})


@bp.get("/products/<int:product_id>")
def get_product(product_id):
    row = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Product not found.")
    return jsonify(product_json(row))


# ---------------------------------------------------------------- cart
def cart_json(db, user_id):
    rows = db.execute(
        "SELECT p.id AS product_id, p.name, p.price_cents, c.quantity FROM cart_items c "
        "JOIN products p ON p.id = c.product_id WHERE c.user_id = ? ORDER BY p.id", (user_id,)).fetchall()
    items = [{"product_id": r["product_id"], "name": r["name"], "unit_price": money(r["price_cents"]),
              "quantity": r["quantity"], "line_total": money(r["price_cents"] * r["quantity"])} for r in rows]
    subtotal = sum(r["price_cents"] * r["quantity"] for r in rows)
    return {"items": items, "total_items": sum(r["quantity"] for r in rows), "subtotal": money(subtotal)}


@bp.get("/cart")
@login_required
def get_cart():
    return jsonify(cart_json(get_db(), current_user()["id"]))


@bp.post("/cart/items")
@login_required
def add_to_cart():
    body = json_body()  # any client-supplied "price" field is ignored on purpose
    product_id = body.get("product_id")
    if not is_int(product_id) or not 1 <= product_id <= MAX_ID:
        raise ApiError(400, "validation_error", "product_id must be a positive integer.", {"product_id": "integer between 1 and 9223372036854775807"})
    quantity = validate_quantity(body.get("quantity"))
    db, uid = get_db(), current_user()["id"]
    product = db.execute("SELECT id, stock FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        raise ApiError(404, "not_found", "Product not found.")
    existing = db.execute("SELECT quantity FROM cart_items WHERE user_id=? AND product_id=?", (uid, product_id)).fetchone()
    new_qty = quantity + (existing["quantity"] if existing else 0)
    if new_qty > MAX_QTY:
        raise ApiError(400, "validation_error", f"Maximum {MAX_QTY} units of a product per cart.", {"quantity": f"max {MAX_QTY} in cart"})
    if new_qty > product["stock"]:
        raise ApiError(409, "insufficient_stock", "Not enough stock available.")
    db.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?,?,?) "
               "ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = excluded.quantity", (uid, product_id, new_qty))
    return jsonify(cart_json(db, uid)), (200 if existing else 201)


@bp.put("/cart/items/<int:product_id>")
@login_required
def update_cart_item(product_id):
    body = json_body()
    quantity = validate_quantity(body.get("quantity"))
    db, uid = get_db(), current_user()["id"]
    if db.execute("SELECT 1 FROM cart_items WHERE user_id=? AND product_id=?", (uid, product_id)).fetchone() is None:
        raise ApiError(404, "not_found", "Item is not in your cart.")
    stock = db.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()["stock"]
    if quantity > stock:
        raise ApiError(409, "insufficient_stock", "Not enough stock available.")
    db.execute("UPDATE cart_items SET quantity=? WHERE user_id=? AND product_id=?", (quantity, uid, product_id))
    return jsonify(cart_json(db, uid))


@bp.delete("/cart/items/<int:product_id>")
@login_required
def remove_cart_item(product_id):
    db, uid = get_db(), current_user()["id"]
    cur = db.execute("DELETE FROM cart_items WHERE user_id=? AND product_id=?", (uid, product_id))
    if cur.rowcount == 0:
        raise ApiError(404, "not_found", "Item is not in your cart.")
    return jsonify(cart_json(db, uid))


@bp.delete("/cart")
@login_required
def clear_cart():
    db, uid = get_db(), current_user()["id"]
    db.execute("DELETE FROM cart_items WHERE user_id=?", (uid,))
    return jsonify(cart_json(db, uid))


# ---------------------------------------------------------------- checkout & orders
def order_json(db, row, with_items=True):
    data = {"id": row["id"], "status": row["status"], "subtotal": money(row["subtotal_cents"]),
            "shipping": money(row["shipping_cents"]), "total": money(row["total_cents"]),
            "shipping_name": row["shipping_name"], "shipping_address": row["shipping_address"],
            "created_at": row["created_at"]}
    items = db.execute("SELECT product_id, product_name, unit_price_cents, quantity, line_total_cents "
                       "FROM order_items WHERE order_id=? ORDER BY id", (row["id"],)).fetchall()
    data["item_count"] = sum(i["quantity"] for i in items)
    if with_items:
        data["items"] = [{"product_id": i["product_id"], "name": i["product_name"],
                          "unit_price": money(i["unit_price_cents"]), "quantity": i["quantity"],
                          "line_total": money(i["line_total_cents"])} for i in items]
    return data


@bp.post("/checkout")
@login_required
def checkout():
    body = json_body()
    name, address, payment = body.get("shipping_name"), body.get("shipping_address"), body.get("payment_method")
    fields = {}
    if not isinstance(name, str) or not 2 <= len(name.strip()) <= 60:
        fields["shipping_name"] = "2-60 characters"
    if not isinstance(address, str) or not 5 <= len(address.strip()) <= 200:
        fields["shipping_address"] = "5-200 characters"
    if payment != "SIMULATED":
        fields["payment_method"] = "must be 'SIMULATED' (no real payments are supported)"
    if fields:
        raise ApiError(400, "validation_error", "One or more fields are invalid.", fields)
    db, uid = get_db(), current_user()["id"]
    db.execute("BEGIN IMMEDIATE")
    try:
        lines = db.execute(
            "SELECT p.id, p.name, p.price_cents, p.stock, c.quantity FROM cart_items c "
            "JOIN products p ON p.id = c.product_id WHERE c.user_id=? ORDER BY p.id", (uid,)).fetchall()
        if not lines:
            raise ApiError(400, "empty_cart", "Your cart is empty.")
        for ln in lines:
            if ln["quantity"] > ln["stock"]:
                raise ApiError(409, "insufficient_stock", f"Not enough stock for {ln['name']}.")
        subtotal = sum(ln["price_cents"] * ln["quantity"] for ln in lines)
        shipping = 0 if subtotal >= FREE_SHIPPING_THRESHOLD_CENTS else SHIPPING_FLAT_CENTS
        cur = db.execute(
            "INSERT INTO orders (user_id,status,subtotal_cents,shipping_cents,total_cents,shipping_name,shipping_address) "
            "VALUES (?,?,?,?,?,?,?)", (uid, "PLACED", subtotal, shipping, subtotal + shipping, name.strip(), address.strip()))
        order_id = cur.lastrowid
        for ln in lines:
            db.execute("INSERT INTO order_items (order_id,product_id,product_name,unit_price_cents,quantity,line_total_cents) "
                       "VALUES (?,?,?,?,?,?)", (order_id, ln["id"], ln["name"], ln["price_cents"], ln["quantity"],
                                               ln["price_cents"] * ln["quantity"]))
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (ln["quantity"], ln["id"]))
        db.execute("DELETE FROM cart_items WHERE user_id=?", (uid,))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    row = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return jsonify(order_json(db, row)), 201


@bp.get("/orders")
@login_required
def list_orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (current_user()["id"],)).fetchall()
    return jsonify({"count": len(rows), "orders": [order_json(db, r, with_items=False) for r in rows]})


def owned_order_or_404(db, order_id):
    """Authorization check: another user's order is indistinguishable from a missing one (404)."""
    row = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, current_user()["id"])).fetchone()
    if row is None:
        raise ApiError(404, "not_found", "Order not found.")
    return row


@bp.get("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    db = get_db()
    return jsonify(order_json(db, owned_order_or_404(db, order_id)))


@bp.post("/orders/<int:order_id>/cancel")
@login_required
def cancel_order(order_id):
    db = get_db()
    db.execute("BEGIN IMMEDIATE")
    try:
        order = owned_order_or_404(db, order_id)
        if order["status"] != "PLACED":
            raise ApiError(409, "invalid_state", "Only PLACED orders can be cancelled.")
        for it in db.execute("SELECT product_id, quantity FROM order_items WHERE order_id=?", (order_id,)).fetchall():
            db.execute("UPDATE products SET stock = stock + ? WHERE id=?", (it["quantity"], it["product_id"]))
        db.execute("UPDATE orders SET status='CANCELLED' WHERE id=?", (order_id,))
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    return jsonify(order_json(db, db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()))


# ---------------------------------------------------------------- admin
@bp.get("/admin/orders")
@admin_required
def admin_orders():
    db = get_db()
    rows = db.execute("SELECT o.*, u.username FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id").fetchall()
    out = []
    for r in rows:
        d = order_json(db, r, with_items=False)
        d["username"] = r["username"]
        out.append(d)
    return jsonify({"count": len(out), "orders": out})
