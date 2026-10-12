# ShopEase Test Execution Report

Review date: **2026-10-10** (second review, after the project ZIP, pytest log and DB were supplied). This report records only what is supported by supplied evidence (`docs/evidence-index.md`) or by executions the reviewer actually ran. Manual and automated results are kept separate.

## 1. Status rules (applied strictly)
| Status | Meaning |
|---|---|
| **Pass** | Executed, and the *complete* expected result is visible in the evidence (or in a verified run) |
| **Fail** | Executed and the observed result differs from expected; a defect is logged |
| **Blocked** | Could not be executed (reason recorded) |
| **Not Run** | No evidence, or the evidence covers only part of the expected result, or used different data/preconditions |

A screenshot never makes a case *Pass* on its own. Where evidence is partial the **Actual result** states exactly what was seen, and the status stays *Not Run*. "Evidence strength" is None, Partial or Full.

## 2. Summary
| Group | Total | Pass | Fail | Blocked | Not Run | Notes |
|---|---|---|---|---|---|---|
| Automated pytest suite, **historical run** (user, before the BUG-002 patch) | 180 items (7 files) | 180 | 0 | 0 | 0 | Real log `screenshots/pytest-output.txt` + screenshot E07; Python 3.14.6, pytest 8.4.2 |
| Automated pytest suite, **latest run after the BUG-002 patch** | 185 items (180 + 5 new) | 185 | 0 | 0 | 0 | Real run by the author: `185 passed in 100.00s (0:01:39)`; Python 3.14.6, pytest 8.4.2 |
| Manual UI cases TC-* (section 5), browser | 24 | 0 | 0 | 0 | 24 | 12 have partial or variant screenshot evidence, 12 have none |
| Manual cases TC-* replayed at **API level** (scripted HTTP, not UI) | 24 | 24 | 0 | 0 | 0 | `scripts/replay_manual_cases.py`; output in `docs/evidence/api-replay-output.txt` |
| Security cases SEC-*, manual evidence (section 6) | 17 | 1 | 0 | 0 | 16 | SEC-HDR-001 Pass; 3 partial (SEC-AUTH-001, SEC-AUTHZ-001, SEC-PRICE-001) |
| Security cases SEC-* replayed at **API level** | 17 | 17 | 0 | 0 | 0 | same script/output; browser-only step SEC-PRICE-001(d) not covered |
| Postman collection (45 requests) | 45 | 0 | 0 | 0 | 45 | One manual `GET /api/products` seen in Postman (E08); collection never run |
| Exploratory sessions EXP-01/02 | 2 | 0 | 0 | 0 | 2 | No notes supplied |

Defects and observations: see section 7 (BUG-002 fixed and verified; BUG-003 open).

## 3. Environment and what was actually executed
| Item | Detail |
|---|---|
| Application | ShopEase on `http://127.0.0.1:5000`, local only |
| User's run (evidence) | Browser (Chrome), Kali terminal (curl, pytest), Postman Lightweight API Client. Seeded data (stock of product 1 = 45 and orders #1-#4 in the screenshots show earlier manual activity). |
| Date evidence | Only the curl response `Date: Sat, 10 Oct 2026 06:58:54 GMT` (E12). The other screenshots carry no date. |
| Commit / build | Not recorded in any evidence |
| Reviewer's environment | Offline sandbox, Python 3.12.3, Flask 3.1.3, Werkzeug 3.1.7, requests 2.33.1; **pytest is not installed and could not be installed** (no network) |
| User's environment (from the pytest log) | Linux, Python 3.14.6, pytest 8.4.2, pluggy 1.6.0, project under `~/Downloads/ShopEase-QA-Security-Testing` with `.venv` |
| Git | The uploaded project ZIP contains **no `.git` folder**, so branch, commit hash, staged files and history could not be inspected |

### Executions by the reviewer on 2026-10-10 (real, in the sandbox, on a scratch copy of your upload)
| # | What | Command / method | Result |
|---|---|---|---|
| 1 | Your `merge_docs_update.sh`, dry run then `--apply` | script as supplied | your target files were unmodified, so 8 files updated, 2 new docs, 2 sanitized screenshots, `.gitignore` appended; no conflicts; links OK |
| 2 | Apply `bug002_fix_and_regression_test.patch` | `git apply --check`, `git apply`, `py_compile` | applies cleanly to your code and compiles |
| 3 | BUG-002 reproduction on your **original** code | scripted HTTP calls | HTTP 500 for IDs >= 2^63 (path and body) |
| 4 | BUG-002 boundary probe on the **patched** code | scripted HTTP calls | 404 (path) / 400 (body) for 2^63 and 10^30; 2^63-1 still 404; 0, -1, `abc`, 1.5, true, null and a missing field behave as before; normal flows still 200/201 |
| 5 | API-level replay: 24 manual + 17 security cases + BUG-002 regression | `python scripts/replay_manual_cases.py` | **42 PASS, 0 FAIL** on patched code (`docs/evidence/api-replay-output.txt`) |
| 6 | Negative control: same replay on your original code | same script | **41 PASS, 1 FAIL** (BUG-002-REG), proving the script can fail |
| 7 | Read-only SQL integrity checks on a copy of your local database | sqlite3 `mode=ro` | 0 mismatches / orphans / negative stock / FK violations (`docs/evidence/sql-real-db-check.txt`) |

**Not executed by the reviewer:** pytest (neither the old suite nor the new `tests/test_id_range.py`), Postman, any browser/UI step. The replay in #5 is **not** a pytest or Postman result and does not replace them.

## 4. Automated results (separate from manual)
**Source:** `screenshots/pytest-output.txt` (real pytest output saved by the user; file time 2026-10-09 14:02 per ZIP metadata, a file timestamp, not a run timestamp) and screenshot E07.
**Log header:** `platform linux -- Python 3.14.6, pytest-8.4.2, pluggy-1.6.0`, `configfile: pytest.ini`, `testpaths: tests`, `collected 180 items`.
**Observed:** 180 lines marked PASSED; final line `180 passed in 98.19s (0:01:38)`; no FAILED, ERROR, SKIPPED, XFAIL or warning entries (the five keyword matches are test names containing "error"). `.pytest_cache` in the upload also lists 180 collected node ids.
**Command:** not printed in the log; the verbose line format and `pytest.ini` indicate `pytest -v` from the project root.
**Not recorded:** exact date/time of the run and commit hash (no Git repository in the upload).
**Scope:** produced **before** the BUG-002 patch, so it does not include `tests/test_id_range.py` (5 new items); the later run below includes them.

### Latest run (after the BUG-002 patch), executed by the author on their machine
| Field | Value |
|---|---|
| Folder | `~/Downloads/ShopEase-final/ShopEase-QA-Security-Testing` (fresh virtual environment, `pip install -r requirements.txt`) |
| Environment | Linux (Kali), Python 3.14.6, pytest 8.4.2, pluggy 1.6.0, `configfile: pytest.ini` |
| Targeted command | `python -m pytest tests/test_id_range.py -v` -> **5 passed in 2.84s** |
| Full command | `python -m pytest -v 2>&1 \| tee screenshots/pytest-output-after-bug002.txt` -> **`185 passed in 100.00s (0:01:39)`** |
| Failures / skips / warnings | none reported in the pasted output (the author pasted the last 15 lines; the full log is in `screenshots/pytest-output-after-bug002.txt`) |
| Date | 12 Oct 2026: pytest prints no date; this is the date of a `curl` response header (`Date: Mon, 12 Oct 2026 05:42:01 GMT`) from the same session |
| Commit | not recorded (the folder was not yet a Git repository) |

Same session, other checks by the author: `python scripts/replay_manual_cases.py` -> **42 PASS, 0 FAIL**; app started with `python run.py`; `GET /api/products/9223372036854775808` -> 404, `.../9223372036854775807` -> 404, `.../1` -> 200; response headers show `Server: ShopEase`, nosniff, DENY, no-referrer, CSP and `Cache-Control: no-store`; privacy grep of docs found no personal names or addresses outside `screenshots/private/`.

Totals after the patch: auth 40, products 23, cart 35, orders 28, api_validation 15, authorization 30, security_headers 9, **id_range 5** = 185.

| File | Items | Status | Basis |
|---|---|---|---|
| `tests/test_auth.py` | 40 | Pass (historical run) | all 180 items PASSED in the log |
| `tests/test_products.py` | 23 | Pass | aggregate; 12 lines visible in E07 |
| `tests/test_cart.py` | 35 | Pass | aggregate |
| `tests/test_orders.py` | 28 | Pass | aggregate |
| `tests/test_api_validation.py` | 15 | Pass | aggregate |
| `tests/test_authorization.py` | 30 | Pass | aggregate |
| `tests/test_security_headers.py` | 9 | Pass | all 9 lines visible in E07 and in the latest run |
| `tests/test_id_range.py` | 5 | Pass (latest run only) | 5 passed in 2.84s |


**What the suite covers:** API behaviour and database side effects of registration, login/logout, search, cart, checkout, orders, validation errors, authorization (401/403/404), price/role tampering, cookie flags, security headers and error leakage. Each test uses a fresh temporary database and a live local server.
**What it does not cover:** the browser UI/JavaScript, CSRF, rate limiting/brute force, TLS, concurrency/race conditions, integer IDs >= 2^63 (hence BUG-002 passed unnoticed), load/performance, accessibility, dependency vulnerabilities.

## 5. Manual test cases (UI / manual API)
Each case has two separate statuses: **UI / browser** (from screenshots, strict rules) and **API-level replay** (scripted HTTP steps of the same case). Test data, steps and expected results are copied from `docs/test-cases.md`; the automated tests that exercise the same behaviour are listed for traceability but are **not** counted as manual results.

### TC-REG-001 - Register with valid details
| Field | Detail |
|---|---|
| Scenario / objective | TS-01 / requirement R-01: Register with valid details |
| Preconditions | Application running; DB freshly initialised; username `qa_tester1` does not exist. |
| Account / role | anonymous visitor |
| Test data | username `qa_tester1`, email `qa_tester1@example.test`, password `Passw0rd1` |
| Expected result | Message 'Registration successful'. API returns **201** with id, username, email, role `customer` and **no** password fields. Exactly 1 row in `users`; `password_hash` differs from the typed password. |
| Actual result | Partial evidence only. Screenshot E03a shows the message 'Registration successful. You can now log in.' and the user still logged out. HTTP 201, response body, database row and password hash were not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E03a |
| Defect | - |
| Automated counterpart | test_auth: register_success_returns_201_and_no_password, stores_hashed_password |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Open http://127.0.0.1:5000/
2. In the Register form enter the test data
3. Click **Register**
4. Open DevTools > Network and check the `register` request
5. Run SQL A4 (`sql/qa-validation-queries.sql`) for `qa_tester1`

### TC-REG-002 - Register with an already used username (case variation)
| Field | Detail |
|---|---|
| Scenario / objective | TS-02 / requirement R-01: Register with an already used username (case variation) |
| Preconditions | Seed data loaded (user `alice` exists). |
| Account / role | anonymous visitor |
| Test data | username `ALICE`, email `other@example.test`, password `Passw0rd1` |
| Expected result | Error message shown; API returns **409**; no new row in `users`. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_auth: duplicate_username_case_insensitive_returns_409 |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Open the app
2. Enter the test data in the Register form
3. Click **Register**
4. Count rows in `users` before and after (SQL A16)

### TC-REG-003 - Register with a 7-character password (boundary - below minimum)
| Field | Detail |
|---|---|
| Scenario / objective | TS-02 / requirement R-01: Register with a 7-character password (boundary - below minimum) |
| Preconditions | App running. |
| Account / role | anonymous visitor |
| Test data | username `qa_tester2`, email `qa_tester2@example.test`, password `Abcdef1` (7 chars) |
| Expected result | Registration rejected; API **400** `validation_error` with a `password` field message; no row created for `qa_tester2`. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_auth: password_boundaries[7 chars] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Open the app
2. Enter the test data
3. Click **Register**

### TC-REG-004 - Register with an 8-character password (boundary - minimum)
| Field | Detail |
|---|---|
| Scenario / objective | TS-02 / requirement R-01: Register with an 8-character password (boundary - minimum) |
| Preconditions | App running; `qa_tester3` does not exist. |
| Account / role | anonymous visitor |
| Test data | username `qa_tester3`, email `qa_tester3@example.test`, password `Abcdef12` (8 chars) |
| Expected result | Registration succeeds (**201**). |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_auth: password_boundaries[8 chars] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Open the app
2. Enter the test data
3. Click **Register**

### TC-LOG-001 - Log in with valid credentials
| Field | Detail |
|---|---|
| Scenario / objective | TS-03 / requirement R-02: Log in with valid credentials |
| Preconditions | Seed data loaded. |
| Account / role | anonymous -> alice (customer) |
| Test data | username `alice`, password `AlicePass123` |
| Expected result | Header shows 'Logged in as alice'. Login returns **200**. Cookie `shopease_session` exists with HttpOnly and SameSite=Lax. Cart and order history load. |
| Actual result | Partial evidence only. E03b shows 'Logged in.' and header 'Logged in as alice' with a Logout button. HTTP status, cookie and its flags were not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E03b |
| Defect | - |
| Automated counterpart | test_auth: login_success_sets_session_cookie_and_me_works; test_security_headers: session_cookie_attributes |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Open the app
2. Enter credentials in the Login form and click **Login**
3. Observe the header text
4. DevTools > Application > Cookies: inspect `shopease_session`

### TC-LOG-002 - Log in with a wrong password
| Field | Detail |
|---|---|
| Scenario / objective | TS-04 / requirement R-02: Log in with a wrong password |
| Preconditions | Seed data loaded; logged out. |
| Account / role | anonymous (target user alice) |
| Test data | username `alice`, password `WrongPass123` |
| Expected result | Message 'Invalid username or password'; API **401**; no session cookie set; header still says 'Not logged in'. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_auth: login_wrong_password_returns_401_without_cookie |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Enter the data in the Login form
2. Click **Login**
3. Check cookies

### TC-LOG-003 - Log out and confirm the session is closed
| Field | Detail |
|---|---|
| Scenario / objective | TS-03 / requirement R-02: Log out and confirm the session is closed |
| Preconditions | Logged in as `alice`. |
| Account / role | alice (customer) |
| Test data | n/a |
| Expected result | Header shows 'Not logged in'; `GET /api/auth/me` returns **401**; the session row is gone from `sessions`; cart/orders are not shown. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_auth: logout_invalidates_server_side_session, logout_removes_session_row |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Click **Logout**
2. Refresh the page
3. In DevTools Network note the `me` request status
4. Run SQL A17 to check the `sessions` table

### TC-SRC-001 - Search for an existing product
| Field | Detail |
|---|---|
| Scenario / objective | TS-05 / requirement R-03: Search for an existing product |
| Preconditions | App running. |
| Account / role | anonymous (catalogue is public) |
| Test data | search text `mouse` |
| Expected result | Only 'Wireless Mouse' (19.99) is listed. |
| Actual result | Variant data only. E02 shows the query 'laptop stand' returning just 'Laptop Stand - 34.00'. The query 'mouse' of this case was not run/captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E02 |
| Defect | - |
| Automated counterpart | test_products: search_matches[mouse] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Type `mouse` in the search box
2. Click **Search**

### TC-SRC-002 - Search with no matching product
| Field | Detail |
|---|---|
| Scenario / objective | TS-05 / requirement R-03: Search with no matching product |
| Preconditions | App running. |
| Account / role | anonymous (catalogue is public) |
| Test data | search text `zzzz-nothing` |
| Expected result | 'No products found.' is shown; API returns **200** with `count` 0 (not an error). |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_products: search_no_match_returns_empty_list_not_error |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Type the text
2. Click **Search**

### TC-SRC-003 - Search is case-insensitive
| Field | Detail |
|---|---|
| Scenario / objective | TS-05 / requirement R-03: Search is case-insensitive |
| Preconditions | App running. |
| Account / role | anonymous (catalogue is public) |
| Test data | search text `LAPTOP` |
| Expected result | 'Laptop Stand' is listed. |
| Actual result | Variant data only. E02 shows a lowercase query matching the capitalised product name, which is consistent with case-insensitive search, but the case's data 'LAPTOP' was not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E02 |
| Defect | - |
| Automated counterpart | test_products: search_matches[MOUSE/laptop] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Type the text
2. Click **Search**

### TC-CRT-001 - Add a product to the cart
| Field | Detail |
|---|---|
| Scenario / objective | TS-06 / requirement R-04: Add a product to the cart |
| Preconditions | Logged in as `alice`; cart empty. |
| Account / role | alice (customer) |
| Test data | product Wireless Mouse (19.99), quantity 2 |
| Expected result | Cart shows Wireless Mouse x2, line total 39.98, subtotal 39.98. |
| Actual result | Variant data only. E05 shows banner 'Added Mechanical Keyboard to cart.' and cart lines Wireless Mouse x1 and Mechanical Keyboard x1; the case's data (Wireless Mouse x2, subtotal 39.98) was not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E05 |
| Defect | - |
| Automated counterpart | test_cart: add_item_returns_201_and_correct_totals |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Search or list products
2. Set the quantity field of Wireless Mouse to 2
3. Click **Add to cart**

### TC-CRT-002 - Update the quantity of a cart item
| Field | Detail |
|---|---|
| Scenario / objective | TS-06 / requirement R-04: Update the quantity of a cart item |
| Preconditions | Cart contains Wireless Mouse x2. |
| Account / role | alice (customer) |
| Test data | new quantity 5 |
| Expected result | Line total 99.95, subtotal 99.95; message 'Cart updated.' |
| Actual result | Variant conditions. E04 shows 'Cart updated.' with Wireless Mouse x5, line total 99.95. The cart also holds USB-C Cable x4, so the subtotal is 139.91 instead of the case's 99.95 (precondition differs). The shown arithmetic is correct (99.95 + 39.96). |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E04 |
| Defect | - |
| Automated counterpart | test_cart: update_quantity_with_put |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. In the cart change the quantity of Wireless Mouse to 5 and press Tab/Enter

### TC-CRT-003 - Remove an item from the cart
| Field | Detail |
|---|---|
| Scenario / objective | TS-06 / requirement R-04: Remove an item from the cart |
| Preconditions | Cart contains at least one item. |
| Account / role | alice (customer) |
| Test data | n/a |
| Expected result | The line disappears and the subtotal is recalculated; API returns 200. |
| Actual result | No evidence supplied (E04 and E05 only show Remove buttons; no removal was captured). |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_cart: remove_item_with_delete |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Click **Remove** on one line

### TC-CRT-004 - Add quantity 0 (invalid, boundary below minimum)
| Field | Detail |
|---|---|
| Scenario / objective | TS-07 / requirement R-04: Add quantity 0 (invalid, boundary below minimum) |
| Preconditions | Logged in; cart empty. |
| Account / role | alice (customer) |
| Test data | product 1, quantity 0 |
| Expected result | Error message; API **400** `validation_error`; cart still empty. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_cart: quantity_boundaries[0] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Set quantity 0 on Wireless Mouse
2. Click **Add to cart**
3. Run SQL A15 for the user

### TC-CRT-005 - Add quantity 10 (valid, boundary maximum)
| Field | Detail |
|---|---|
| Scenario / objective | TS-07 / requirement R-04: Add quantity 10 (valid, boundary maximum) |
| Preconditions | Logged in; cart empty. |
| Account / role | alice (customer) |
| Test data | product 1, quantity 10 |
| Expected result | Item added (201), subtotal 199.90. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_cart: quantity_boundaries[10] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Set quantity 10
2. Click **Add to cart**

### TC-CRT-006 - Add quantity 11 (invalid, boundary above maximum)
| Field | Detail |
|---|---|
| Scenario / objective | TS-07 / requirement R-04: Add quantity 11 (invalid, boundary above maximum) |
| Preconditions | Logged in; cart empty. |
| Account / role | alice (customer) |
| Test data | product 1, quantity 11 |
| Expected result | Error message; API **400**; cart unchanged. (The server must enforce this even if the browser input is bypassed.) |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_cart: quantity_boundaries[11] |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Set quantity 11 (type the value; the spinner limit is only a UI hint)
2. Click **Add to cart**

### TC-CRT-007 - Add an out-of-stock product
| Field | Detail |
|---|---|
| Scenario / objective | TS-08 / requirement R-04: Add an out-of-stock product |
| Preconditions | Logged in; Desk Lamp has stock 0. |
| Account / role | alice (customer) |
| Test data | product 7 (Desk Lamp), quantity 1 |
| Expected result | Error message 'Not enough stock available.'; API **409** `insufficient_stock`; cart unchanged. |
| Actual result | Precondition only. E06/E09 list 'Desk Lamp - 24.99 (out of stock)'; no attempt to add it was captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E06, E09 (product list only) |
| Defect | - |
| Automated counterpart | test_cart: out_of_stock_product_cannot_be_added |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Find 'Desk Lamp' (listed as out of stock)
2. Click **Add to cart**

### TC-CAL-001 - Cart subtotal with two products
| Field | Detail |
|---|---|
| Scenario / objective | TS-09 / requirement R-05: Cart subtotal with two products |
| Preconditions | Logged in; cart empty. |
| Account / role | alice (customer) |
| Test data | 2 x Wireless Mouse (19.99), 3 x USB-C Cable (9.99) |
| Expected result | Subtotal = 39.98 + 29.97 = **69.95**. |
| Actual result | Variant data only. E04: 99.95 + 39.96 = 139.91 and E05: 19.99 + 59.50 = 79.49 are both arithmetically correct, but the case's data (2 x 19.99 + 3 x 9.99 = 69.95) was not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E04, E05 |
| Defect | - |
| Automated counterpart | test_cart: subtotal_with_multiple_products |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Add both items
2. Read the cart subtotal

### TC-CAL-002 - Free-shipping boundary at 50.00
| Field | Detail |
|---|---|
| Scenario / objective | TS-09 / requirement R-06: Free-shipping boundary at 50.00 |
| Preconditions | Logged in; cart empty; seeded stock. |
| Account / role | alice (customer) |
| Test data | Case A: 9 x Notebook A5 (5.00) = 45.00. Case B: 10 x Notebook A5 = 50.00 |
| Expected result | Case A: shipping **5.00**, total **50.00**. Case B: shipping **0.00**, total **50.00**. |
| Actual result | No direct evidence. E06 shows Order #4 total 139.91 (9 items), consistent with free shipping above 50.00 if the subtotal was 139.91, but the shipping line and the 9-vs-10 notebook boundary were not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E06 (indirect) |
| Defect | - |
| Automated counterpart | test_orders: free_shipping_boundary_at_50 |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Case A: add 9 notebooks and check out with valid details
2. Note shipping and total
3. Case B: (new cart) add 10 notebooks and check out
4. Note shipping and total

### TC-CHK-001 - Successful checkout with simulated payment
| Field | Detail |
|---|---|
| Scenario / objective | TS-10 / requirement R-07: Successful checkout with simulated payment |
| Preconditions | Logged in as `alice`; cart has 2 x Wireless Mouse. |
| Account / role | alice (customer) |
| Test data | name `Test Buyer`, address `1 Test Street, Testville` |
| Expected result | Message with order number; total 44.98 (39.98 + 5.00 shipping); order appears in history as PLACED; cart empty; stock of product 1 reduced by 2; stored totals consistent (A11 returns 0 rows). |
| Actual result | Partial / indirect. E05 shows the form filled before submission (not submitted in the image). E06 later lists Order #4 PLACED, total 139.91 (9 items), consistent with the cart in E04. Confirmation message, shipping, stock change and database checks were not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E04, E05, E06 |
| Defect | - |
| Automated counterpart | test_orders: checkout_creates_order_with_correct_totals, decrements_stock_and_clears_cart, stored_order_total_matches_item_lines |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Enter shipping name and address
2. Click **Place order (simulated payment)**
3. Run SQL A9, A10, A11 and check stock of product 1

### TC-CHK-002 - Checkout with an empty cart
| Field | Detail |
|---|---|
| Scenario / objective | TS-11 / requirement R-07: Checkout with an empty cart |
| Preconditions | Logged in; cart empty. |
| Account / role | alice (customer) |
| Test data | valid shipping details |
| Expected result | Error 'Your cart is empty.'; API **400** `empty_cart`; no order created. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_orders: empty_cart_checkout_rejected_and_no_order_created |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Enter details and click **Place order**
2. Run SQL A16 before/after

### TC-CHK-003 - Checkout with missing shipping address
| Field | Detail |
|---|---|
| Scenario / objective | TS-11 / requirement R-07: Checkout with missing shipping address |
| Preconditions | Cart has one item. |
| Account / role | alice (customer) |
| Test data | name `Test Buyer`, address empty |
| Expected result | API **400** with a `shipping_address` field message; no order; cart preserved. |
| Actual result | No evidence supplied. |
| Status (UI / browser) | **Not Run** (evidence strength: None) |
| Evidence | - |
| Defect | - |
| Automated counterpart | test_orders: checkout_missing_field_rejected |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Leave the address blank (remove the browser `required` attribute via DevTools Elements to reach the server check)
2. Submit
3. Check the response in Network

### TC-ORD-001 - Order history shows only my orders
| Field | Detail |
|---|---|
| Scenario / objective | TS-12 / requirement R-08: Order history shows only my orders |
| Preconditions | Seed data loaded. |
| Account / role | alice and bob (customers) |
| Test data | users `alice` and `bob` |
| Expected result | alice sees orders #3 and #1 only; bob sees order #2 only. |
| Actual result | Partial. E06 (alice) lists orders #4, #3, #1 and not bob's #2, which matches the expected alice list plus the new order. Bob's history was not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E06 |
| Defect | BUG-003 (cosmetic text seen in E06) |
| Automated counterpart | test_orders: order_history_lists_only_own_orders_newest_first; test_authorization: order_ids_in_list_never_include_other_users |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Log in as alice and read Order history
2. Log out; log in as bob and read Order history

### TC-ORD-002 - Cancel a PLACED order and restock
| Field | Detail |
|---|---|
| Scenario / objective | TS-13 / requirement R-09: Cancel a PLACED order and restock |
| Preconditions | Logged in; one PLACED order exists (from TC-CHK-001). |
| Account / role | alice (customer) |
| Test data | the order id |
| Expected result | Status becomes CANCELLED, stock restored; the second cancel returns **409** `invalid_state`. |
| Actual result | Partial. E10 shows banner 'Order cancelled.' (order id not visible). E06 shows seeded Order #3 as CANCELLED. The status change, stock restoration and the second-cancel 409 were not captured. |
| Status (UI / browser) | **Not Run** (evidence strength: Partial) |
| Evidence | E06, E10 |
| Defect | - |
| Automated counterpart | test_orders: cancel_order_restocks_and_sets_status, cancelling_twice_returns_409 |
| Status (API-level replay, scripted) | **Pass**: 2026-10-10, `docs/evidence/api-replay-output.txt` (API behaviour only; on-screen messages not covered) |

Steps:
1. Click **Cancel** next to the order
2. Check status and stock of product 1
3. Try cancelling again via Postman 'Cancel my order again'

## 6. Security test cases (see `docs/security-test-cases.md` and `docs/security-test-report.md`)
Manual results only; the matching automated tests are listed for traceability and counted in section 4.

| ID | Objective | Account / role | Procedure (short) | Expected | Actual (evidence-based) | Status | Evidence | Automated counterpart |
|---|---|---|---|---|---|---|---|---|
| SEC-AUTH-001 | Protected routes while logged out | anonymous | GET /api/cart, /api/orders, POST /api/checkout, GET /api/admin/orders without a cookie | 401 `unauthenticated` for every call | Partial: the browser console in E09/E10 shows `GET /api/auth/me` answered 401 (UNAUTHORIZED) while logged out. The other protected routes were not captured. | Not Run | E09, E10 | test_authorization: protected_endpoints_return_401_when_logged_out (12 routes) |
| SEC-AUTH-002 | Login error message / user enumeration | anonymous | Login unknown user vs alice with wrong password; compare | Both 401 with identical body | No evidence. | Not Run | - | test_auth: login_unknown_user_message_matches_wrong_password |
| SEC-AUTH-003 | Password storage | tester with DB access | Register a user, inspect `users.password_hash` | Salted hash, never plaintext | Real database evidence: the registered user in the tester's local DB has a hash with scheme prefix `scrypt:` (`docs/evidence/sql-real-db-check.txt`); API replay confirms the hash is not plaintext. Source review: `generate_password_hash` is used in `app/api.py` register (code review only, not an execution). | Not Run | - | test_auth: register_stores_hashed_password_not_plaintext |
| SEC-AUTH-004 | SQL-injection-style login input | anonymous | Login with `alice' OR '1'='1' --` | 401, no session, tables intact | No evidence. Source review: all queries are parameterised (`?` placeholders). | Not Run | - | test_auth: sql_injection_string_in_login_does_not_authenticate |
| SEC-SESS-001 | Session invalid after logout (replay old cookie) | alice | Log in, copy cookie, log out, replay cookie on /api/auth/me | 401 | No screenshot (not captured, by the user's decision). API-level replay 2026-10-10: after logout the old cookie returns 401 -> **Pass (API level)**; automated test exists. | Not Run | none (E14 API-level only) | test_auth: logout_invalidates_server_side_session |
| SEC-SESS-002 | Invalid / tampered cookies | anonymous | Send garbage, over-long, SQL-like and altered-token cookies | 401, never 500 | No evidence. | Not Run | - | test_authorization: invalid_session_cookie_is_rejected, tampered_valid_token_is_rejected |
| SEC-SESS-003 | Expired session | alice + DB access | Set `expires_at` to the past in a test DB; call /api/auth/me | 401 | No evidence. | Not Run | - | test_authorization: expired_session_is_rejected |
| SEC-SESS-004 | Cookie attributes | anonymous -> alice | Inspect `Set-Cookie` of the login response | HttpOnly, SameSite=Lax, Path=/, Max-Age=3600, no Secure locally | No evidence: E12 is a response without `Set-Cookie`. Cookie values must not be published. | Not Run | - | test_security_headers: session_cookie_attributes_for_local_config, secure_flag_is_added_when_configured |
| SEC-SESS-005 | New token at each login | alice | Log in twice; compare cookie values | Values differ | No evidence. | Not Run | - | test_auth: each_login_issues_a_new_token |
| SEC-AUTHZ-001 | Alice reads Bob's order (IDOR) | alice (customer) | `GET /api/orders/2` and `/api/orders/99999` while logged in as alice; control: bob reads order 2 | 404 with identical body for both; no data of bob; bob gets 200 | Partial. E10: `/api/orders/2` -> 404 `{"error":{"code":"not_found","message":"Order not found."}}` and `/api/orders/99999` -> 404 with the identical body. The control request (bob -> 200) was not captured, so ownership enforcement is not proven by the screenshot. | Not Run | E10 | test_authorization: user_cannot_read_another_users_order (includes the bob 200 control), other_users_order_is_indistinguishable_from_missing_order |
| SEC-AUTHZ-002 | Alice cancels Bob's order | alice (customer) | `POST /api/orders/2/cancel` as alice; check status in DB | 404; order 2 stays PLACED | No evidence. (E10 shows an 'Order cancelled.' banner, but the order id and owner are not visible.) | Not Run | E10 (insufficient) | test_authorization: user_cannot_cancel_another_users_order |
| SEC-AUTHZ-003 | Customer calls admin endpoint | alice, then qa_admin | `GET /api/admin/orders` | alice 403; admin 200 | No evidence. | Not Run | - | test_authorization: customer_gets_403_on_admin_endpoint, admin_can_list_all_orders |
| SEC-AUTHZ-004 | Role / user-id manipulation | anonymous / alice | Register with `role:admin`; checkout with `user_id:2` | role stays customer; order owned by caller | No evidence. | Not Run | - | test_api_validation: extra_unknown_fields_are_ignored_not_trusted; test_authorization: self_registration_cannot_create_admin, checkout_uses_authenticated_user_not_body_user_id |
| SEC-INPUT-001 | Malformed requests and error handling | anonymous / alice | Form body, broken JSON, JSON array, empty and oversized body; unknown routes; wrong method | 415/400/400/400/413/404/405 with the standard error shape, no stack trace | No evidence. **Reviewer's own run found HTTP 500 for integer IDs >= 2^63 (BUG-002); the suite does not test that range.** | Not Run | reviewer run | test_api_validation (15 items), test_security_headers: error_responses_do_not_leak_stack_traces_or_paths |
| SEC-INPUT-002 | Injection / script-like search input | anonymous | Search `' OR '1'='1`, `'; DROP TABLE products; --`, `<script>alert(1)</script>`, `%`, `_` | 200, empty result, table intact, nothing executed | No evidence of the manual browser check. | Not Run | - | test_products: search_sql_injection_string_is_harmless, search_script_tag_is_not_reflected, search_wildcards_are_treated_literally |
| SEC-PRICE-001 | Price, total and quantity tampering | alice (customer) | (a) add with extra `price:0.01`; (b) checkout with `total/subtotal`; (c) invalid quantities; (d) edit quantity input in DevTools | Server price used; total from DB; invalid quantities 400 | Partial. Step (a) observed in E09: request with `price: 0.01` returned 200 and unit_price 59.5, line_total 119.0, subtotal 119.0 (quantity 2 after merging with an existing item). Steps (b)-(d) were not captured. | Not Run | E09 | test_cart: client_supplied_price_is_ignored, quantity_boundaries, quantity_wrong_types...; test_authorization: price_tampering_at_checkout_is_ignored |
| SEC-HDR-001 | Security headers and server banner | anonymous | `curl -si http://127.0.0.1:5000/api/products` | nosniff, X-Frame-Options DENY, Referrer-Policy, CSP, Cache-Control no-store, `Server: ShopEase` | **All expected headers observed** in E12: `Server: ShopEase`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`, `Cache-Control: no-store`; server `Date` Sat, 10 Oct 2026 06:58:54 GMT. Scope: JSON endpoint only (page `/` and error responses not captured). No HSTS by design (plain HTTP). | **Pass** | E12 | test_security_headers (9 items, all PASSED visible in E07) |

**API-level replay of the security cases (separate from the table above):** SEC-AUTH-001..004, SEC-SESS-001..005, SEC-AUTHZ-001..004, SEC-INPUT-001..002, SEC-PRICE-001 (steps a-c) and SEC-HDR-001 all returned PASS on 2026-10-10 (`docs/evidence/api-replay-output.txt`). This is scripted HTTP evidence, not browser, Postman or pytest evidence, and it does not change the manual-evidence statuses in the table.

## 7. Defects and observations
| ID | Title | Severity / Priority | Status | Evidence |
|---|---|---|---|---|
| BUG-001 | `Server` header disclosed framework and Python versions | Low / Low | Fixed; regression test passes (E07) and header observed as `Server: ShopEase` (E12) | `docs/bug-reports.md` |
| **BUG-002** | HTTP 500 when an integer ID >= 2^63 is used in the URL or JSON on six endpoints | Low / Medium | **Fix applied in the working copy (patch reviewed); behaviour verified by HTTP reproduction before/after and by the API replay (41 PASS + 1 FAIL on original code, 42 PASS on patched). Pytest confirmation of the 5 new tests: Not Run.** Not yet marked Fixed. | `docs/bug-reports.md` |
| **BUG-003** | Order history prints "(1 items)" (grammar) | Low / Low | **Open** | E06; `app/static/app.js` line 72 |
| OBS-01 | A red `401 (UNAUTHORIZED)` for `/api/auth/me` appears in the browser console whenever the page loads logged out | Informational | Expected behaviour of the API contract, no action required | E09, E10 |
| OBS-03 | Seeded orders do not deduct stock, so cancelling a seeded order raises stock above its seed value (product 2: 31 instead of 30 in the tester's DB) | Low (seed-data inconsistency) | Open | `docs/evidence/sql-real-db-check.txt` |
| OBS-02 | Product list rows wrap the quantity box inconsistently for longer product names | Low / Low | Open (cosmetic) | E01, E04 |

## 8. Gaps and how to close them
1. Initialise Git in the project folder and record the commit hash with the next test run.
2. Execute the 24 manual cases in the browser exactly as written and capture the missing evidence listed in `docs/evidence-index.md`; change the *UI / browser* status only for cases whose entire expected result you observed.
3. Run the Postman collection (Runner) and capture the Test Results tab.
4. `11-session-logout` has no screenshot; the behaviour is covered by the automated test and the API-level replay (SEC-SESS-001) only.
5. Initialise or locate the Git repository and record the commit hash with the next test run.
