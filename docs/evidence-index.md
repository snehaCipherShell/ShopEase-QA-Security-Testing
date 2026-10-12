# Evidence Index

Screenshots are **supporting evidence**, not a substitute for reproducible tests. Each entry says what the image actually shows and what it does **not** show. A screenshot never turns a test into *Pass* by itself: see the status rules in `docs/test-execution-report.md`.

Review date: 2026-10-10. Twelve screenshots were supplied. The expected 11th (`11-session-logout`) was **intentionally not captured** (user decision); that behaviour is evidenced only by the automated test and by the API-level replay (E14), not by a screenshot.

Besides the screenshots, three non-image evidence files exist: E13 `screenshots/pytest-output.txt`, E14 `docs/evidence/api-replay-output.txt`, E15 `docs/evidence/sql-real-db-check.txt` (entries at the end).

## Filename mapping
Original filenames were kept (nothing renamed, no duplicates created) so the original evidence is preserved. The table shows which expected slot each file fills.

| # | Expected name | File in `screenshots/` | Present |
|---|---|---|---|
| 1 | `01-home-page.png` | `01__Home_page.png` | yes |
| 2 | `02-product-search.png` | `02-product-search.png` | yes |
| 3 | `03-registration-login.png` | `03-registration-.png` **and** `03-login.png` (two images share slot 3) | yes (2 files) |
| 4 | `04-cart-quantity-validation.png` | `04-cart-quantity-validation.png` | yes (content differs from name, see below) |
| 5 | `05-checkout-order.png` | `private/05-checkout-order.png` (original, git-ignored) + `sanitized/05-checkout-order_sanitized.png` | yes |
| 6 | `06-order-history-cancel.png` | `06-order-history-cancel.png` | yes |
| 7 | `07-pytest-summary.png` | `07-pytest-summary.png` | yes |
| 8 | `08-api-validation.png` | `private/08-api-validation.png` (original, git-ignored) + `sanitized/08-api-validation_sanitized.png` | yes (content differs from name) |
| 9 | `09-price-tampering.png` | `09-price-tampering.png` | yes |
| 10 | `10-authorization-test.png` | `10-authorization-test.png` | yes |
| 11 | `11-session-logout.png` | - | not captured (user decision) |
| 12 | `12-security-headers.png` | `12-security-headers.png` | yes |

## Evidence entries
Related IDs: **TC-** manual case (`docs/test-cases.md`), **SEC-** security case (`docs/security-test-cases.md`), **AUTO** automated test file.

### E01 - `screenshots/01__Home_page.png`
- **Purpose:** baseline home page, logged out.
- **Shows:** ShopEase header with the "fictional data only" badge, status "Not logged in", Register/Login forms, product list with prices and stock (Wireless Mouse 19.99 / 50 in stock, Mechanical Keyboard 59.50 / 30, USB-C Cable 9.99 / 100, Laptop Stand 34.00 / 20, Webcam HD 45.00 / 15), empty cart (subtotal 0.00). Server address `127.0.0.1:5000`.
- **Related:** smoke check; TC-SRC-001 precondition (catalogue listing).
- **Does not show:** the full catalogue (page is cut off), the API call behind the list, any test result.
- **Observation:** rows for the two longest product names wrap the quantity box onto a second line while shorter names stay on one line (minor layout inconsistency, OBS-02).

### E02 - `screenshots/02-product-search.png`
- **Purpose:** product search.
- **Shows:** query `laptop stand` returns only "Laptop Stand - 34.00 (20 in stock)".
- **Related:** TC-SRC-001 / TC-SRC-003 (variant data); AUTO `test_products.py`.
- **Limitation:** the query used (`laptop stand`, lowercase, two words) is **not** the data of any written case (`mouse`, `LAPTOP`, `zzzz-nothing`). It supports the general behaviour only. No negative search (no results) is shown.

### E03a - `screenshots/03-registration-.png`
- **Purpose:** registration feedback.
- **Shows:** green message "Registration successful. You can now log in.", status still "Not logged in".
- **Related:** TC-REG-001 (partial).
- **Does not show:** the input values, the 201 response, the absence of password fields in the response, the database row or hash. The trailing hyphen in the filename is a typo only; the file works as is.

### E03b - `screenshots/03-login.png`
- **Purpose:** login.
- **Shows:** message "Logged in." and header "Logged in as alice" with a Logout button; empty cart.
- **Related:** TC-LOG-001 (partial); AUTO `test_auth.py`.
- **Does not show:** HTTP status, the session cookie or its flags (HttpOnly / SameSite), failed-login behaviour. No credentials or tokens are visible.

### E04 - `screenshots/04-cart-quantity-validation.png`
- **Purpose (by name):** cart quantity validation.
- **Shows:** logged in as alice; message "Cart updated."; cart lines Wireless Mouse 19.99 x5 = 99.95 and USB-C Cable 9.99 x4 = 39.96; subtotal 139.91 (arithmetic is correct: 99.95 + 39.96).
- **Related:** TC-CRT-002 (variant: cart also holds cables so subtotal differs from the case), TC-CAL-001 (different quantities).
- **Limitation (important):** the image shows *valid* updates. It does **not** show any rejected quantity (0, 11, text), so it does not evidence quantity *validation* despite its filename. Re-capture an invalid-quantity attempt (error message and 400 response) to match the name.

### E05 - `screenshots/private/05-checkout-order.png` (original, git-ignored; contains typed shipping data)
- **Purpose (by name):** checkout.
- **Shows:** new cart (Wireless Mouse x1, Mechanical Keyboard x1, subtotal 79.49 = 19.99 + 59.50) with a shipping name and address typed in; product stock shown as Wireless Mouse 45 and USB-C Cable 96 (consistent with 5 mice and 4 cables having been sold in an earlier order).
- **Related:** TC-CHK-001 (partial, pre-submit state only).
- **Limitation:** the order has **not** been submitted in this image; no confirmation message, order number, shipping line or total is visible.
- **Privacy:** the typed shipping name and address are personal data, and the same values are stored in the tester's local `instance/shopease.db` (git-ignored; never publish or share that file). Use the sanitized copy publicly: `screenshots/sanitized/05-checkout-order_sanitized.png`. The original is kept privately in `screenshots/private/` (git-ignored).

### E06 - `screenshots/06-order-history-cancel.png`
- **Purpose:** order history and cancellation.
- **Shows:** Order #4 PLACED total 139.91 (9 items) with a Cancel button; Order #3 CANCELLED total 89.99 (1 items); Order #1 PLACED total 59.50 (1 items). Totals are consistent with the seeded data and with the 5 x 19.99 + 4 x 9.99 cart in E04 (free shipping above 50.00).
- **Related:** TC-ORD-001 (alice's half only), TC-ORD-002 (partial).
- **Does not show:** a cancellation being performed, a changed status, restocked inventory, or bob's history. Bob's order #2 is correctly absent from alice's list, but that alone does not prove authorization.
- **Defect visible:** the text "(1 items)" is grammatically wrong: see BUG-003.

### E07 - `screenshots/07-pytest-summary.png`
- **Purpose:** automated test result.
- **Shows:** the tail of a pytest verbose run: several `PASSED` lines from `test_products.py` and `test_security_headers.py` and the final line `180 passed in 98.19s (0:01:38)`.
- **Related:** AUTO, all files.
- **Limitation:** only the end of the output is visible, and no command line, date or commit. The full log of the same run is E13, which lists all 180 items as PASSED. The run predates the BUG-002 patch and was not repeated by the reviewer (pytest unavailable offline).

### E08 - `screenshots/private/08-api-validation.png` (original, git-ignored; Postman history panel)
- **Purpose (by name):** API validation.
- **Shows:** Postman Lightweight API Client, `GET http://127.0.0.1:5000/api/products` -> `200 OK`, 33 ms, 1.52 KB, body begins `"count": 8` with product 1 (Wireless Mouse, price 19.99, stock 45).
- **Related:** Postman folder 02 "List products" (positive case only); AUTO `test_products.py`.
- **Limitation:** one successful GET. No invalid input, missing field or error response is shown, so it is not API *validation* evidence. The collection itself was not run; the "Test Results" tab is empty.
- **Privacy/scope:** the left History panel lists older requests to unrelated public websites. They are not part of this project (the project's scope is local only). Use `screenshots/sanitized/08-api-validation_sanitized.png` publicly.

### E09 - `screenshots/09-price-tampering.png`
- **Purpose:** server-side price validation.
- **Shows:** console `fetch POST /api/cart/items` with `product_id: 2, quantity: 1, price: 0.01`; result `HTTP status: 200`; response shows Mechanical Keyboard `unit_price 59.5`, `quantity 2`, `line_total 119.0`, `subtotal 119.0`. The client-supplied price 0.01 was not used.
- **Related:** SEC-PRICE-001 step (a); AUTO `test_client_supplied_price_is_ignored`.
- **Notes:** status 200 (not 201) and quantity 2 are consistent with the API contract because the keyboard was already in the cart (merge). The red 401 on `/api/auth/me` at the top is the page's normal logged-out probe (OBS-01).
- **Does not show:** tampering at checkout (`total`/`subtotal` fields), quantity tampering via DevTools, or the order total after checkout.

### E10 - `screenshots/10-authorization-test.png`
- **Purpose:** horizontal authorization (IDOR) and order operations.
- **Shows:** logged in as alice; message "Order cancelled."; console requests `GET /api/orders/2` -> `404` `{"error":{"code":"not_found","message":"Order not found."}}` and `GET /api/orders/99999` -> `404` with an identical body.
- **Related:** SEC-AUTHZ-001 (partial); AUTO `test_authorization.py`.
- **Limitation:** no control request shows that order 2 exists and belongs to bob (bob receiving 200), so the screenshot shows identical responses but cannot by itself prove ownership enforcement. The "Order cancelled." banner proves some cancel action succeeded in the UI but not which order, nor the restocking. Cancelling someone else's order, admin access and role manipulation are not shown.

### E11 - `11-session-logout.png` - not captured
No screenshot exists (user decision). SEC-SESS-001 and TC-LOG-003 have **no browser evidence**. Their behaviour was checked at API level on 2026-10-10 (E14: logout -> `/api/auth/me` 401, old cookie replay 401, session row removed) and by automated tests; no cookie value is recorded anywhere.

### E12 - `screenshots/12-security-headers.png`
- **Purpose:** security headers and server banner.
- **Shows:** `curl -si http://127.0.0.1:5000/api/products` -> `HTTP/1.1 200 OK`, `Server: ShopEase`, `Content-Type: application/json`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`, `Cache-Control: no-store`; response `Date: Sat, 10 Oct 2026 06:58:54 GMT` (server-generated timestamp for this run).
- **Related:** SEC-HDR-001; AUTO `test_security_headers.py`; BUG-001 regression (banner no longer leaks versions).
- **Limitations:** an unauthenticated product list only; no `Set-Cookie` header, no error response, no page (`/`) request. `Strict-Transport-Security` is absent by design on plain HTTP. The terminal prompt shows the author's username and host name.

## Repository-safety notes for screenshots
- No password, session cookie, token or secret is visible in any supplied image.
- E05 and E08 contain content that should not be published as-is. Sanitized copies are in `screenshots/sanitized/`; originals were not modified.
- In the delivered tree the two originals are already in `screenshots/private/`, which `.gitignore` excludes. In your own repository, make sure they are not left in `screenshots/` (`mkdir -p screenshots/private && mv screenshots/05-checkout-order.png screenshots/08-api-validation.png screenshots/private/`), and check `git ls-files screenshots/` before the first commit.
- `screenshots/pytest-output.txt` contains your local home path (`/home/<username>/Downloads/...`); harmless, but replace it if you prefer not to publish your username.
- Screenshots of `curl -c`/`-b` cookie jars, HAR exports or `Set-Cookie` values must be cropped or avoided.

## Missing or weak evidence (to capture next)
1. An invalid quantity (0 and 11) rejected with message and `400` (TC-CRT-004/006).
2. The checkout confirmation, or `POST /api/checkout` response with order total and shipping.
3. A real Postman collection run with the Test Results tab, including negative requests.
4. bob's `200` on `/api/orders/2` as the control for SEC-AUTHZ-001, and `403` on `/api/admin/orders` as alice.
5. A pytest run after the BUG-002 patch with the command line visible (`pytest -v | tee ...`).

## Non-image evidence
### E13 - `screenshots/pytest-output.txt`
Real pytest output saved by the user. Header: Python 3.14.6, pytest 8.4.2, pluggy 1.6.0, `configfile: pytest.ini`, `collected 180 items`; 180 PASSED lines; final line `180 passed in 98.19s (0:01:38)`; no failures, errors, skips or warnings. Date/commit not in the log (file time 2026-10-09 14:02 per ZIP). Predates the BUG-002 patch.

### E14 - `docs/evidence/api-replay-output.txt`
Output of `python scripts/replay_manual_cases.py` run by the reviewer on 2026-10-10 (Python 3.12.3, temporary database): 24 TC replays + 17 SEC replays + BUG-002 regression = **42 PASS, 0 FAIL** on the patched code. A negative control on the original code gave 41 PASS and 1 FAIL (BUG-002-REG). API-level only: not pytest, not Postman, not a browser.

### E15 - `docs/evidence/sql-real-db-check.txt`
Read-only integrity queries (A5, A11, A13, A14, A18, foreign-key check) on a copy of the tester's local database: no mismatches, orphans, negative stock or FK violations; registered user's hash uses the `scrypt` scheme. Counts only; the database itself is git-ignored and must not be published.

### E16 - `screenshots/pytest-output-after-bug002.txt`
Real pytest output saved by the author after the BUG-002 patch (created on the author's machine; keep this file in the repository). The author reported: targeted run `5 passed in 2.84s`; full run `185 passed in 100.00s (0:01:39)`, Python 3.14.6, pytest 8.4.2. The log has no date or commit. Review the file before publishing: it contains your local home path.
