# ShopEase API Testing Guide

Base URL: `http://127.0.0.1:5000` (local only). Format: JSON. Authentication: session cookie `shopease_session` set by `POST /api/auth/login`. **The exact status codes below are the API contract: tests must assert them precisely**, not just "2xx".

Error body (all errors): `{"error": {"code": "<machine_code>", "message": "<text>", "fields": {...optional...}}}`

## 1. Endpoint reference
| Method | Path | Auth | Success | Notable errors |
|---|---|---|---|---|
| POST | `/api/auth/register` | no | **201** `{id, username, email, role}` | 400 validation, 409 duplicate, 415 not JSON |
| POST | `/api/auth/login` | no | **200** + cookie | 400 missing fields, 401 invalid credentials |
| POST | `/api/auth/logout` | yes | **200** | 401 |
| GET | `/api/auth/me` | yes | **200** `{id, username, email, role}` | 401 |
| GET | `/api/products?q=` | no | **200** `{count, products[]}` | 400 if `q` > 100 chars |
| GET | `/api/products/{id}` | no | **200** | 404 |
| GET | `/api/cart` | yes | **200** `{items[], total_items, subtotal}` | 401 |
| POST | `/api/cart/items` | yes | **201** new line / **200** merged | 400 (qty not int 1-10, merged > 10), 404 product, 409 stock |
| PUT | `/api/cart/items/{product_id}` | yes | **200** | 400, 404 not in cart, 409 stock |
| DELETE | `/api/cart/items/{product_id}` | yes | **200** (returns cart) | 404 not in cart |
| DELETE | `/api/cart` | yes | **200** | 401 |
| POST | `/api/checkout` | yes | **201** order | 400 invalid/empty cart, 409 stock |
| GET | `/api/orders` | yes | **200** `{count, orders[]}` (own only) | 401 |
| GET | `/api/orders/{id}` | yes | **200** | 404 (also for other users' orders) |
| POST | `/api/orders/{id}/cancel` | yes | **200** | 404, 409 not PLACED |
| GET | `/api/admin/orders` | admin | **200** | 401, **403** for customers |

Money values are JSON numbers with 2 decimals. Quantity must be a JSON integer 1-10 (strings, decimals, booleans, null are rejected). Any `price`/`total` sent by the client is ignored.

## 2. Importing into Postman
1. Start the app (`python run.py`).
2. Postman > **Import** > select `postman/ShopEase.postman_collection.json` and `postman/ShopEase.local.postman_environment.json`.
3. Choose the **ShopEase Local** environment (top-right). `baseUrl` must be `http://127.0.0.1:5000`.
4. Run requests in folder order. Folder `01 Auth` ends with *Login as alice*, which folders 03 and 04 need. Postman stores the session cookie automatically.
5. Use **Run collection** to execute everything; view the *Test Results* tab. Reset data with `python -m app.init_db --reset` before re-running (otherwise stock, orders and cart state differ).
6. Postman assertions use `pm.test`, e.g. status code, JSON content type, required fields, data types, calculated subtotal.

> The collection has **not** been run inside Postman yet (only one manual `GET /api/products` is evidenced, `screenshots/sanitized/08-api-validation_sanitized.png`). Status codes in the collection were cross-checked earlier by replaying the requests with a script. Run the collection with the Collection Runner and record the results in `docs/test-execution-report.md`.

## 3. Using curl (alternative)
```bash
curl -si -c jar.txt -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"AlicePass123"}' http://127.0.0.1:5000/api/auth/login
curl -si -b jar.txt http://127.0.0.1:5000/api/cart
curl -si -b jar.txt -H 'Content-Type: application/json' \
  -d '{"product_id":1,"quantity":2}' http://127.0.0.1:5000/api/cart/items
```

## 4. What to assert in every API test
1. **Status code** (exact).  2. **Content-Type** `application/json`.  3. **Required fields** present.  4. **Data types** (id int, price number, name string, items array).  5. **Business values** (subtotal arithmetic).  6. **No sensitive fields** (`password_hash`).  7. **Side effects**: DB changed (or not changed for invalid requests) - check with SQL.

## 5. Negative test ideas covered
| Category | Examples |
|---|---|
| Missing authentication | all protected endpoints without cookie -> 401 |
| Invalid authentication | garbage, tampered or expired cookie -> 401; wrong password -> 401 |
| Authorization | alice requests bob's order -> 404; customer calls admin -> 403 |
| Invalid input | wrong types, boundary quantities, 7/65-char passwords, over-long strings |
| Malformed requests | broken JSON, JSON array, form body (415), oversized body (413) |
| Wrong method / route | 405 with `Allow`, 404 JSON |

## 6. Automated suite
| File | Focus |
|---|---|
| `tests/test_auth.py` | register, login, logout, session |
| `tests/test_products.py` | listing, search, product detail |
| `tests/test_cart.py` | GET/POST/PUT/DELETE cart, quantities, stock, price tampering |
| `tests/test_orders.py` | checkout, totals, shipping boundary, history, cancellation |
| `tests/test_api_validation.py` | malformed requests, error shape |
| `tests/test_authorization.py` | 401/403/404 rules, IDOR, role escalation |
| `tests/test_security_headers.py` | headers, cookie flags, information leakage |

Each test gets a **new temporary SQLite database** and its own server on a random local port (`tests/conftest.py`), so tests are independent of execution order and never touch `instance/shopease.db`. Run: `pytest -v`.
