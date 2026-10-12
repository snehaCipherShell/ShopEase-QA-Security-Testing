"""Create and seed a LOCAL TEST database with fictional data only."""
import os
import sqlite3
from werkzeug.security import generate_password_hash

HERE = os.path.dirname(os.path.abspath(__file__))

# Fictional, local-only test accounts. These are documented test data, not real credentials.
SEED_USERS = [
    ("alice", "alice@example.test", "AlicePass123", "customer"),
    ("bob", "bob@example.test", "BobPass1234", "customer"),
    ("qa_admin", "admin@example.test", "AdminPass123", "admin"),
]

# (id, sku, name, description, category, price_cents, stock)
SEED_PRODUCTS = [
    (1, "MSE-001", "Wireless Mouse", "Ergonomic 2.4 GHz wireless mouse with silent clicks", "Accessories", 1999, 50),
    (2, "KBD-001", "Mechanical Keyboard", "Tenkeyless keyboard with tactile switches", "Electronics", 5950, 30),
    (3, "CBL-001", "USB-C Cable", "1 metre braided charging cable", "Accessories", 999, 100),
    (4, "STD-001", "Laptop Stand", "Aluminium stand that raises a laptop to eye level", "Home", 3400, 20),
    (5, "CAM-001", "Webcam HD", "1080p webcam with built-in microphone", "Electronics", 4500, 15),
    (6, "NTB-001", "Notebook A5", "A5 ruled notebook, 80 pages", "Stationery", 500, 200),
    (7, "LMP-001", "Desk Lamp", "LED desk lamp with three brightness levels", "Home", 2499, 0),
    (8, "HDP-001", "Headphones", "Over-ear headphones with noise isolation", "Electronics", 8999, 10),
]

# Seeded orders: (user, status, created_at, shipping_name, address, [(product_id, qty)])
SEED_ORDERS = [
    ("alice", "PLACED", "2026-01-10 10:00:00", "Alice Test", "1 Test Street, Testville", [(2, 1)]),
    ("bob", "PLACED", "2026-01-11 11:30:00", "Bob Test", "2 Sample Road, Sampletown", [(6, 2), (3, 1)]),
    ("alice", "CANCELLED", "2026-01-12 09:15:00", "Alice Test", "1 Test Street, Testville", [(8, 1)]),
]


def init_database(path, hash_method="scrypt", seed=True):
    """Create a NEW database file at `path`. Refuses to overwrite an existing file."""
    if os.path.exists(path):
        raise FileExistsError(f"{path} already exists; delete it or use --reset")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(os.path.join(HERE, "schema.sql"), encoding="utf-8") as fh:
        conn.executescript(fh.read())
    if seed:
        for username, email, password, role in SEED_USERS:
            conn.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)",
                (username, email, generate_password_hash(password, method=hash_method), role),
            )
        conn.executemany("INSERT INTO products VALUES (?,?,?,?,?,?,?)", SEED_PRODUCTS)
        prices = {p[0]: (p[2], p[5]) for p in SEED_PRODUCTS}
        for username, status, created, name, addr, items in SEED_ORDERS:
            uid = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
            subtotal = sum(prices[pid][1] * qty for pid, qty in items)
            shipping = 0 if subtotal >= 5000 else 500
            cur = conn.execute(
                "INSERT INTO orders (user_id,status,subtotal_cents,shipping_cents,total_cents,"
                "shipping_name,shipping_address,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (uid, status, subtotal, shipping, subtotal + shipping, name, addr, created),
            )
            for pid, qty in items:
                pname, pcents = prices[pid]
                conn.execute(
                    "INSERT INTO order_items (order_id,product_id,product_name,unit_price_cents,"
                    "quantity,line_total_cents) VALUES (?,?,?,?,?,?)",
                    (cur.lastrowid, pid, pname, pcents, qty, pcents * qty),
                )
    conn.commit()
    conn.close()
