# ShopEase Security Test Cases (local only)

## Scope and rules
- Test **only** your own local ShopEase instance (`http://127.0.0.1:5000`) or another environment you are explicitly authorised to test.
- No tests against public websites, third-party systems, or other people's accounts. No denial-of-service, brute-force or scanning of anything you do not own.
- ShopEase uses fictional data. Use the seeded accounts `alice`, `bob`, `qa_admin`.
- Results below are *Not Run* until you execute them. **Do not invent findings.** A *confirmed vulnerability* has reproducible evidence; a *potential risk* is a hypothesis or design observation. Keep them separate (see `security-findings-template.md`).
- Core design principles being validated: **the server never trusts a price (or user id, or role) sent by the browser, and enforces authorization on every protected operation.**

How to read each case: *Automated* shows where an automated test exists (the user's pytest run reported 180 passed, see `docs/test-execution-report.md`). Manual results and evidence are tracked in `docs/test-execution-report.md` and `docs/evidence-index.md`; the security conclusions are in `docs/security-test-report.md`. *Actual result* and *Evidence* stay blank until you test.

---
## Authentication
### SEC-AUTH-001 - Protected routes while logged out
**Preconditions:** no session cookie. **Steps:** 1. In a private window or with `curl` (no cookie) call `GET /api/cart`, `GET /api/orders`, `POST /api/checkout`, `GET /api/admin/orders`. **Expected:** every call returns **401** with `unauthenticated`; no data. **Automated:** `test_authorization.py::test_protected_endpoints_return_401_when_logged_out`. **Actual:** ____ **Evidence:** ____ **Severity rationale if failing:** High - unauthenticated data access/modification.

### SEC-AUTH-002 - Login error messages and user enumeration
**Steps:** 1. Login with unknown user + any password. 2. Login with `alice` + wrong password. 3. Compare status and body. **Expected:** both **401**, identical message. **Automated:** `test_login_unknown_user_message_matches_wrong_password`. **Actual:** ____ **Evidence:** ____ **Severity if failing:** Low-Medium - helps attackers enumerate accounts (note: registration still reveals "already registered", a common accepted trade-off - document it).

### SEC-AUTH-003 - Password storage
**Steps:** register a user, then `SELECT username, substr(password_hash,1,20) FROM users WHERE username='...'` (sqlite3 on the test DB). **Expected:** salted hash with a scheme prefix (scrypt by default), never the plaintext. **Automated:** `test_register_stores_hashed_password_not_plaintext` (checks pbkdf2 test config). **Actual:** ____ **Evidence:** ____ **Severity if failing:** High/Critical - credential exposure.

### SEC-AUTH-004 - SQL-injection-style login input
**Steps:** username `alice' OR '1'='1' --`, any password. **Expected:** **401**, no session, tables intact (queries are parameterised). **Automated:** `test_sql_injection_string_in_login_does_not_authenticate`. **Actual:** ____ **Evidence:** ____ **Severity if failing:** Critical - authentication bypass.

## Session handling
### SEC-SESS-001 - Session after logout (replay)
**Steps:** 1. Log in, copy the `shopease_session` value (DevTools > Application > Cookies). 2. Log out. 3. Send `curl -b "shopease_session=<old value>" http://127.0.0.1:5000/api/auth/me`. **Expected:** **401** (the session is deleted on the server, not merely removed from the browser). **Automated:** `test_logout_invalidates_server_side_session`. **Actual:** ____ **Evidence:** ____ **Severity if failing:** Medium-High.

### SEC-SESS-002 - Invalid and tampered cookies
**Steps:** send garbage, an over-long value, a SQL-like string, and a valid token with the last character changed. **Expected:** **401** each time; no 500. **Automated:** `test_invalid_session_cookie_is_rejected`, `test_tampered_valid_token_is_rejected`. **Actual:** ____ **Evidence:** ____ **Severity if failing:** High.

### SEC-SESS-003 - Expired session
**Steps (test DB only):** `UPDATE sessions SET expires_at = 1;` then call `/api/auth/me`. **Expected:** **401**. **Automated:** `test_expired_session_is_rejected`. **Actual:** ____ **Evidence:** ____

### SEC-SESS-004 - Cookie attributes (local configuration)
**Steps:** inspect the `Set-Cookie` header of the login response (DevTools Network or `curl -si`). **Expected locally:** `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age=3600`; **no `Secure`** because local HTTP is documented (Secure cookies are not sent over plain HTTP). With `SHOPEASE_COOKIE_SECURE=1` behind HTTPS, `Secure` must be present. **Automated:** `test_session_cookie_attributes_for_local_config`, `test_secure_flag_is_added_when_configured`. **Actual:** ____ **Evidence:** ____ **Rationale:** missing HttpOnly would make theft via script easier (Medium); missing Secure over real HTTPS would expose the cookie on the network.

### SEC-SESS-005 - New session token at every login
**Steps:** log in twice in the same browser; compare the cookie values. **Expected:** values differ (no session fixation). **Automated:** `test_each_login_issues_a_new_token`. **Actual:** ____

## Authorization
### SEC-AUTHZ-001 - User A reads User B's order (IDOR / broken object-level authorization)
**Preconditions:** seeded data; order 2 belongs to `bob`. **Steps:** log in as `alice`; `GET /api/orders/2`. Also request a non-existent id (99999) and compare. **Expected:** **404** with the same body for both (no existence oracle); none of bob's data in the response; bob himself gets 200. **Automated:** `test_user_cannot_read_another_users_order`, `test_other_users_order_is_indistinguishable_from_missing_order`. **Actual:** ____ **Evidence:** ____ **Severity if failing:** High - exposure of other users' personal data. *Design note: the API returns 404 instead of 403 on purpose; either is acceptable if documented consistently.*

### SEC-AUTHZ-002 - User A cancels User B's order
**Steps:** as `alice`, `POST /api/orders/2/cancel`; then check `SELECT status FROM orders WHERE id=2`. **Expected:** **404**; status still `PLACED`. **Automated:** `test_user_cannot_cancel_another_users_order`. **Actual:** ____ **Severity if failing:** High - unauthorised modification.

### SEC-AUTHZ-003 - Vertical access: customer calls an admin endpoint
**Steps:** as `alice`, `GET /api/admin/orders`; then as `qa_admin`. **Expected:** alice **403**; admin **200**. **Automated:** `test_customer_gets_403_on_admin_endpoint`, `test_admin_can_list_all_orders`. **Actual:** ____ **Severity if failing:** High.

### SEC-AUTHZ-004 - Mass assignment: self-registering as admin / forging user ids
**Steps:** register with extra field `"role":"admin"`; at checkout send `"user_id": 2`. **Expected:** role is `customer`; order belongs to the logged-in user. **Automated:** `test_extra_unknown_fields_are_ignored_not_trusted`, `test_self_registration_cannot_create_admin`, `test_checkout_uses_authenticated_user_not_body_user_id`. **Actual:** ____ **Severity if failing:** Critical (privilege escalation).

## Input validation and tampering
### SEC-INPUT-001 - Malformed requests and error handling
**Steps:** send form-encoded body, broken JSON, JSON array, empty body, 20 KB body to `POST /api/auth/register`/`login`; call unknown routes and wrong methods. **Expected:** 415 / 400 / 400 / 400 / 413 / 404 / 405 with the standard JSON error shape; no stack trace, file paths or SQL text. **Automated:** `test_api_validation.py`, `test_error_responses_do_not_leak_stack_traces_or_paths`. **Actual:** ____ **Severity if failing:** Low-Medium (information disclosure) up to High if a 500 reveals secrets.

### SEC-INPUT-002 - Injection-style and script-like search input
**Steps:** search `' OR '1'='1`, `'; DROP TABLE products; --`, `<script>alert(1)</script>`, `%`, `_`. **Expected:** 200, empty result, products table intact (SQL A16 counts unchanged), input not reflected unescaped; the UI uses `textContent`, so no script runs. **Automated:** `test_search_sql_injection_string_is_harmless`, `test_search_script_tag_is_not_reflected`, `test_search_wildcards_are_treated_literally`. **Manual part:** confirm in the browser that nothing executes and no alert appears. **Actual:** ____ **Severity if failing:** Critical (SQLi) / Medium-High (XSS).

### SEC-PRICE-001 - Price, total and quantity tampering
**Steps:** (a) `POST /api/cart/items` with `{"product_id":2,"quantity":1,"price":0.01}`; (b) checkout with `"total":0.01,"subtotal":0.01,"shipping":0`; (c) quantity `-1`, `0`, `11`, `"5"`, `1.5`, `true`; (d) edit the quantity input in DevTools > Elements to 99 and submit. **Expected:** server price 59.50 used; total 59.50; invalid quantities **400**; nothing stored. **Automated:** `test_client_supplied_price_is_ignored`, `test_price_tampering_at_checkout_is_ignored`, `test_quantity_boundaries`, `test_quantity_wrong_types_rejected_and_cart_unchanged`. **Actual:** ____ **Severity if failing:** High - direct financial integrity impact.

## Headers
### SEC-HDR-001 - Basic security headers and server banner
**Steps:** `curl -si http://127.0.0.1:5000/api/products`. **Expected:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, a `Content-Security-Policy`, `Cache-Control: no-store` for JSON, and `Server: ShopEase` (no Werkzeug/Python versions - see BUG-001). **Automated:** `test_security_headers.py`. **Actual:** ____ **Severity if failing:** Low. Note `Strict-Transport-Security` is intentionally absent: it only makes sense over HTTPS.

---
## Coverage summary
| Case | Automated | Manual verification suggested |
|---|---|---|
| SEC-AUTH-001..004 | yes | curl / Postman |
| SEC-SESS-001..005 | yes | DevTools cookies |
| SEC-AUTHZ-001..004 | yes | Postman with two users |
| SEC-INPUT-001..002 | yes | browser (XSS check) |
| SEC-PRICE-001 | yes | DevTools Elements edit |
| SEC-HDR-001 | yes | `curl -si` |

## Not covered (be honest about it)
CSRF token testing, rate limiting/lockout, HTTPS/TLS configuration, dependency vulnerability scanning, file upload, business-logic race conditions under concurrency, automated scanners. These are listed in `next-improvements.md`.
