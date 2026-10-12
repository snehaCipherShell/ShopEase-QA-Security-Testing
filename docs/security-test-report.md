# ShopEase Security Test Report

| Field | Value |
|---|---|
| Target | ShopEase, local instance `http://127.0.0.1:5000` (Flask 3 + SQLite) |
| Report date | 2026-10-10 |
| Type | Local educational security validation: **not a certified audit or penetration test** |
| Evidence | `docs/evidence-index.md`, user's pytest log (`screenshots/pytest-output.txt`, E07), API-level replay (`docs/evidence/api-replay-output.txt`), SQL check (`docs/evidence/sql-real-db-check.txt`), source review |
| Related | `docs/security-test-cases.md` (test design), `docs/test-execution-report.md` (results), `docs/security-findings-template.md` (register) |

## 1. Scope
**In scope:** authentication and session handling, protected routes, horizontal and vertical authorization, order operations, input validation and malformed requests, cart/checkout price and quantity tampering, session cookie flags, security headers, error handling and information disclosure of the local ShopEase API and page.
**Out of scope / not tested:** any external system, TLS/HTTPS, denial of service, brute-force, scanners, CSRF exploitation, dependency vulnerabilities, concurrency races, deployment hardening, anything behind a real network. No external system was contacted.

## 2. Methodology
1. **Design:** 17 test cases (SEC-*) derived from OWASP-style categories (authentication, session management, access control, input validation, business-logic tampering, security misconfiguration).
2. **Automated checks:** 180 pytest items using `requests` against a live local server with a fresh temporary database per test; the security-relevant files are `test_authorization.py` (30), `test_security_headers.py` (9), `test_api_validation.py` (15), plus tampering/injection items in `test_cart.py`, `test_products.py`, `test_auth.py`.
3. **Manual checks:** browser console `fetch` requests and `curl` (screenshots E09, E10, E12).
4. **Source review:** reading the implementation to compare it with the documented expectations (section 4).
5. **API-level replay (2026-10-10):** `scripts/replay_manual_cases.py` replays all 17 security cases (plus the 24 functional cases and the BUG-002 regression) over real HTTP against a temporary local database; a negative control against the original code failed as expected.
6. **Classification:** *Confirmed* only with reproducible evidence; otherwise *Potential risk* or *Untested*.

## 3. Results at a glance
| Area | Cases | Manual result | Automated result (user-run, aggregate 180 passed) |
|---|---|---|---|
| Authentication | SEC-AUTH-001..004 | Browser/manual: Not Run (SEC-AUTH-001 partial). **API-level replay: 4/4 PASS** | passing |
| Session handling | SEC-SESS-001..005 | Browser/manual: Not Run (no logout screenshot, by decision). **API-level replay: 5/5 PASS**, including cookie replay after logout | passing |
| Authorization | SEC-AUTHZ-001..004 | Browser/manual: Not Run (SEC-AUTHZ-001 partial). **API-level replay: 4/4 PASS**, including the bob-200 control | passing |
| Input validation | SEC-INPUT-001..002 | Browser/manual: Not Run. **API-level replay: 2/2 PASS** | passing; gap BUG-002 found and **fixed** (regression tests pass) |
| Price tampering | SEC-PRICE-001 | Browser/manual: step (a) observed (E09). **API-level replay: steps a-c PASS**; step (d) browser edit not run | passing |
| Headers / info disclosure | SEC-HDR-001 | **Pass** | passing |

The automated pass count (180) comes from the user's real pytest log and screenshot (E07, Python 3.14.6, pytest 8.4.2); it predates the BUG-002 patch and was not re-run by the reviewer (pytest unavailable offline). API-level replay results are separate and do not replace pytest.

## 4. Control review: documented expectation vs implementation vs evidence
| Control | Documented expectation | Implementation (source review) | Evidence | Assessment |
|---|---|---|---|---|
| Server-side prices | Server never trusts client price | `cart_json` and `checkout` read `price_cents` from `products`; request fields `price`, `total`, `subtotal` are never read | E09 (unit_price 59.5 despite `price: 0.01`); automated tests | **Tested** for add-to-cart (manual) and add + checkout (automated) |
| Quantity limits | Integer 1-10, stock check | `validate_quantity` (rejects bool/float/str), merge limit, stock check (409) | automated only | Tested (automated); manual evidence none |
| Order ownership | Others' orders unreachable | `owned_order_or_404` filters `WHERE id=? AND user_id=?`; same 404 body as a missing order | E10 (identical 404 bodies), automated incl. bob-200 control | Tested (automated), partially evidenced manually |
| Cancel authorization | Only owner may cancel | `cancel_order` uses `owned_order_or_404` inside a transaction | automated only | Tested (automated) |
| Admin access | customer 403, admin 200 | `admin_required` checks `role` from the DB session join | automated only | Tested (automated) |
| Role / identity manipulation | Body `role`/`user_id` ignored | register inserts without reading `role`; checkout uses `current_user()["id"]` | automated only | Tested (automated) |
| Session invalidation | Logout kills the server session | tokens are random (`secrets.token_urlsafe(32)`), stored hashed (SHA-256) in `sessions`; logout deletes the row | automated + API-level replay (cookie replay after logout -> 401); no screenshot | Tested (automated) |
| Invalid / tampered cookies | 401 | lookup by token hash with expiry; length capped at 128 | automated only | Tested (automated) |
| Cookie flags | HttpOnly, SameSite=Lax, no Secure locally | `set_cookie(..., httponly=True, samesite="Lax", secure=COOKIE_SECURE)` | automated only | Tested (automated); manual none |
| Security headers | 5 headers + `Server: ShopEase` | `after_request` hook + custom request handler (BUG-001 fix) | **E12 manual**, automated | **Tested** (manual + automated) |
| Error handling | JSON errors, no leaks | global handlers; generic 500 | automated for common cases; **BUG-002 shows an unhandled path** | Partially tested, 1 confirmed defect |
| Password storage | hashed | Werkzeug `generate_password_hash` (scrypt default) | automated (pbkdf2 test config) | Tested (automated) |
| SQL injection | parameterised queries | all SQL uses `?` placeholders; LIKE input escaped | automated string tests | Tested for the strings used; not exhaustive |
| XSS in UI | no script execution | frontend renders with `textContent`; CSP `default-src 'self'` | automated "not reflected"; browser check not evidenced | Reasoned from code; manual check Not Run |

## 5. Verified observations
Only items with direct evidence:
1. `GET /api/products` returns `Server: ShopEase`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`, `Cache-Control: no-store` (E12, 2026-10-10 06:58:54 GMT).
2. A request carrying a client price of 0.01 for product 2 was priced at 59.5 by the server (E09).
3. Alice receives 404 with the same body for order 2 and for non-existent order 99999 (E10); no order data is returned.
4. An unauthenticated `GET /api/auth/me` returns 401 (browser console, E09/E10).
5. The user's pytest run reported `180 passed in 98.19s` (E07), including all 9 security-header tests.
6. **BUG-002 (confirmed, reviewer execution):** integer IDs >= 2^63 produce HTTP 500 on `GET /api/products/{id}`, `GET /api/orders/{id}`, `POST /api/orders/{id}/cancel`, `PUT` and `DELETE /api/cart/items/{id}`, and `POST /api/cart/items` with a huge `product_id`. Generic body, no stack trace or path leaked, no data changed.
7. An 8,000-level nested JSON body returned 400 (no defect).

## 6. Findings
| ID | Title | Class | Severity | Evidence | Status |
|---|---|---|---|---|---|
| SEC-F-001 / BUG-001 | `Server` header leaked Werkzeug/Python versions | Confirmed | Low | failing test during development; fixed; E12, E07 | Fixed |
| SEC-F-002 / BUG-002 | Unhandled `OverflowError` -> 500 for oversized integer IDs | Confirmed | Low | reviewer run on the original code | **Fixed and verified** (pytest 185 passed; manual 404/404/200) |

Severity rationale: both are information-quality / robustness issues with no demonstrated data exposure or privilege gain. They are rated Low in this local context; no CVSS score is claimed.

## 7. Potential risks and untested surface (not confirmed vulnerabilities)
| ID | Observation | Why it is not a finding | Suggested next step |
|---|---|---|---|
| PR-01 | No login rate limiting or lockout (feature is absent in the code) | Absence of a control confirmed by reading code; exploitability not tested (and brute-forcing is out of scope) | Add throttling, test it locally |
| PR-02 | No CSRF tokens; relies on `SameSite=Lax` and the JSON-only `Content-Type` check | Not tested in a browser | Local cross-origin test page against your own instance |
| PR-03 | Plain HTTP, no `Secure` cookie flag, no HSTS | By design for localhost | Test behind local TLS with `SHOPEASE_COOKIE_SECURE=1` |
| PR-04 | `POST /api/auth/register` answers 409 for existing username/email (account enumeration), while login is generic | Design trade-off, no exploit shown | Decide and document |
| PR-05 | Seeded demo accounts including `qa_admin` have documented weak passwords | Intended test data | Never run seeded database on a network; `run.py` binds to 127.0.0.1 |
| PR-06 | Logout removes only the current session; other sessions of a user stay valid; expired sessions are purged only at login | Not tested | Add "log out everywhere" and periodic cleanup |
| PR-07 | Password policy is length + letter + digit only | No breached-password check | Consider a deny-list |
| PR-08 | Flask development server, not hardened | Local only | Production WSGI server + reverse proxy for any real deployment |
| PR-09 | No audit logging of security events | Not tested | Structured logs |
| PR-10 | Concurrency (two checkouts for last stock unit) | Transactions use `BEGIN IMMEDIATE` but no concurrency test exists | Add a threaded test |

## 8. Limitations of this report
- Browser evidence is incomplete (see `docs/evidence-index.md`): no session-logout screenshot (by the user's decision; the behaviour is covered by an automated test and the API-level replay); most UI cases have no or partial screenshots and stay *Not Run* in the browser column.
- The pytest result is the user's real log (no date or commit recorded) and was not re-run after the BUG-002 patch.
- No scanner, fuzzer, dependency audit (`pip-audit`), static analysis (`bandit`) or intercepting-proxy session was run.
- The reviewer's probes covered oversized integers and nested JSON only.
- A passing test shows the checked behaviour, not the absence of other defects.

## 9. Remediation recommendations (priority order)
1. **BUG-002:** fixed and verified; keep the regression tests.
2. Re-run the suite with real pytest and store the full output; capture browser evidence for the remaining UI cases (invalid quantity, checkout confirmation).
3. Add rate limiting on login and test it; evaluate CSRF protection explicitly.
4. Add a concurrency test for checkout stock.
5. Fix the "(1 items)" wording (BUG-003) and the wrapped product rows (OBS-02) if UI polish matters.
6. For any non-local use: HTTPS, `Secure` cookies, HSTS, production WSGI server, secrets management, dependency scanning.

## 10. Conclusion
Within the tested scope the implementation matches its documented controls, with one confirmed low-severity robustness defect (BUG-002) and one fixed information-disclosure issue (BUG-001). This is **not** a statement that ShopEase is secure; the untested surface in section 7 is substantial.
