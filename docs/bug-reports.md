# ShopEase Bug Reports

Each report must be **reproducible**: someone else can follow it and see the same thing. Include environment, exact steps, expected vs actual result, evidence, severity and priority with a reason.

> **Labels used below:** *REAL* = a defect actually observed during development of this repository. *SIMULATED EXAMPLE* = a made-up scenario to demonstrate good report writing; it is **not** a defect in ShopEase and must never be presented as one.

## Bug report template
| Field | Content |
|---|---|
| Bug ID | BUG-NNN |
| Title | Short, specific: *what* fails *where* |
| Reported by / date | |
| Build / environment | commit hash, OS, browser/tool |
| Related test case | TC-... / SEC-... |
| Preconditions | |
| Steps to reproduce | numbered |
| Expected result | |
| Actual result | |
| Evidence | screenshot, HAR, response body, SQL output |
| Severity / Priority | with justification |
| Status | New / Assigned / Open / Fixed / Retest / Verified / Reopened / Closed / Rejected / Deferred |
| Notes | frequency, workaround, suspected area (suspicion is not proof) |

---

## BUG-001 - Server response header disclosed framework and Python versions  *(REAL)*
| Field | Content |
|---|---|
| Reported by / date | Author, during development, 2026-10-09 |
| Environment | Linux sandbox, Python 3.12.3, Flask 3.1.3, Werkzeug 3.1.7, ShopEase development server |
| Related test | `tests/test_security_headers.py::test_server_header_does_not_reveal_framework_versions`; SEC-HDR-001 |
| Steps | 1. Start the server with the first version of the code (app set `Server: ShopEase` in an `after_request` hook). 2. `curl -si http://127.0.0.1:PORT/api/products`. 3. Read the `Server` header. |
| Expected | `Server` header does not reveal framework or language versions. |
| Actual | Header was `Werkzeug/3.1.7 Python/3.12.3, ShopEase` - the development server prepended its own banner to the app's value. |
| Evidence | Automated test failed on the assertion; header value captured from a `requests` call. |
| Severity / Priority | **Low / Low.** Information disclosure only; helps an attacker choose known issues for those versions but is not directly exploitable. Local-only app; low business impact. |
| Root cause | The WSGI development server adds its own `Server` value; an application hook cannot remove it. (Confirmed by reading the observed header, then fixed and retested.) |
| Fix | Custom `ShopEaseRequestHandler.version_string()` used by `run.py` and the test server. |
| Status | **Fixed and verified.** The regression test `test_server_header_does_not_reveal_framework_versions` shows PASSED in the user's pytest run (`screenshots/07-pytest-summary.png`), and `curl -si` shows `Server: ShopEase` (`screenshots/12-security-headers.png`, response dated Sat, 10 Oct 2026 06:58:54 GMT). Production deployments should use a real WSGI server behind a hardened reverse proxy - not covered here. |

---

## BUG-SIM-001 - Cart total ignores quantity after update  *(SIMULATED EXAMPLE - not a ShopEase defect)*
| Field | Content |
|---|---|
| Build / environment | Hypothetical build 0.9 / Kali Linux / Firefox |
| Related test case | TC-CRT-002 |
| Preconditions | Logged in as `alice`; cart contains 2 x Wireless Mouse (19.99) |
| Steps | 1. Change the quantity of Wireless Mouse from 2 to 5. 2. Read the subtotal. |
| Expected | Line total 99.95, subtotal 99.95 |
| Actual (hypothetical) | Line total shows 99.95 but subtotal still shows 39.98 until the page is reloaded |
| Evidence | *(would be a screenshot and the Network response of `PUT /api/cart/items/1`)* |
| Severity / Priority | **High / High** - wrong money amount visible to the customer on a core flow. |
| Investigation notes | Network tab shows the PUT response contains subtotal 99.95, so the server is likely correct; the UI is probably not using the response. *This is a hypothesis; the root cause would need developer confirmation.* |
| Status | N/A (illustration) |

## BUG-SIM-002 - Footer link colour barely readable  *(SIMULATED EXAMPLE)*
| Field | Content |
|---|---|
| Steps | Open the home page, look at the footer. |
| Expected | Text contrast meets accessibility guidance. |
| Actual (hypothetical) | Light-grey text on white. |
| Severity / Priority | **Low / Low** - cosmetic. |
| Status | N/A (illustration) |

## BUG-SIM-003 - Order of another user viewable by changing the order ID  *(SIMULATED EXAMPLE)*
| Field | Content |
|---|---|
| Related test | SEC-AUTHZ-001 |
| Steps | Log in as alice, request `/api/orders/2` (bob's order). |
| Expected | 404 (or 403). |
| Actual (hypothetical) | 200 with bob's data. |
| Severity / Priority | **High / High** - broken access control exposes other customers' data. |
| Note | In the real ShopEase build the automated test `test_user_cannot_read_another_users_order` expects 404 and passed in the author's check. This entry only shows how such a bug would be written up. |
| Status | N/A (illustration) |

## BUG-002 - HTTP 500 for integer IDs of 2^63 or larger  *(REAL, verified, OPEN)*
| Field | Content |
|---|---|
| Reported by / date | Reviewer, 2026-10-10 (executed in the review sandbox: Python 3.12.3, Flask 3.1.3, Werkzeug 3.1.7, temporary seeded database, logged in as `alice`) |
| Related test | SEC-INPUT-001 (malformed input / error handling) - not covered by the existing suite |
| Preconditions | App running; logged in as `alice` (for the authenticated endpoints) |
| Steps | 1. `GET /api/products/9223372036854775808` (2^63). 2. `GET /api/orders/1000000000000000000000000000000`. 3. `POST /api/orders/1000000000000000000000000000000/cancel`. 4. `PUT /api/cart/items/1000000000000000000000000000000` with `{"quantity":1}`. 5. `DELETE /api/cart/items/1000000000000000000000000000000`. 6. `POST /api/cart/items` with `{"product_id":1000000000000000000000000000000,"quantity":1}`. |
| Expected | A client error (404 `not_found`, or 400 `validation_error` for the JSON body), never a server error. |
| Actual | All six requests returned **500** `{"error":{"code":"server_error","message":"Internal server error."}}`. The server log shows `OverflowError: Python int too large to convert to SQLite INTEGER`. For comparison, `GET /api/products/9223372036854775807` (2^63 - 1) returned 404 as expected. |
| Evidence | Scripted run on 2026-10-10 (status codes above, server traceback). No screenshot. |
| Impact | Low. The 500 body is generic (no stack trace or path leaked), no data is changed and the server keeps running; but valid-looking input causes an unhandled exception, noisy logs and an inconsistent error contract. Authenticated endpoints require a session (except `GET /api/products/{id}`). |
| Severity / Priority | **Low / Medium**: low technical impact, but cheap to fix and visible in an input-validation review. |
| Root cause (code review, confirmed by the traceback) | Flask's `<int:...>` converter accepts arbitrarily large integers and the value is passed straight to SQLite, which supports only 64-bit integers. |
| Recommendation | Validate the range (1 .. 2^63-1) before querying, or catch `OverflowError` and return 404/400; then add parametrised tests with `9223372036854775807` and `9223372036854775808` and re-run the suite. |
| Status | **Fixed and verified (2026-10-12).** Original finding kept above for the record. |

**Fix (reviewed 2026-10-10 against the uploaded code; patch `bug002_fix_and_regression_test.patch`):** `app/api.py` gains `MAX_ID = 2**63 - 1`, a blueprint `url_value_preprocessor` that answers **404 `not_found`** for any path ID above `MAX_ID` (the same status and error shape the API already uses for unknown IDs), and `add_to_cart` now rejects a body `product_id` outside 1..`MAX_ID` with **400 `validation_error`** (the existing convention for bad input). Only `app/api.py` changed; no existing test was edited.
**Regression coverage:** new `tests/test_id_range.py` (5 items): all five path endpoints x {2^63, 10^30} -> 404; body `product_id` x {2^63, 10^30} -> 400 with an empty cart; and 2^63-1 still gives the normal 404.
**Verification:** (1) original code -> HTTP 500 on all six calls for 2^63 and 10^30 (reviewer, 2026-10-10); (2) patched code -> 404 (five path calls) and 400 (body), 2^63-1 still 404, 0/-1/`abc`/1.5/true/null/missing unchanged, normal flows unchanged (reviewer HTTP probe); (3) API replay 41 PASS + 1 FAIL on original code, 42 PASS on patched code; (4) **real pytest on the author's machine: `tests/test_id_range.py` 5 passed in 2.84 s, full suite 185 passed in 100.00 s** (Python 3.14.6, pytest 8.4.2; log `screenshots/pytest-output-after-bug002.txt`); (5) author's manual check against the running app: `GET /api/products/9223372036854775808` -> 404, `.../9223372036854775807` -> 404, `.../1` -> 200.
**Design note:** the preprocessor runs before authentication, so a huge ID answers 404 even when logged out (a normal ID answers 401). No data is exposed; if uniform 401 is preferred, move the check into the handlers.

## BUG-003 - Order history shows "(1 items)"  *(REAL, OPEN, cosmetic)*
| Field | Content |
|---|---|
| Related test case | TC-ORD-001 |
| Steps | 1. Log in as `alice`. 2. Read the Order history list. |
| Expected | Correct grammar for a single item: "1 item". |
| Actual | Orders #3 and #1 are shown as "(1 items)". |
| Evidence | `screenshots/06-order-history-cancel.png`; source `app/static/app.js` line 72 always appends " items)". |
| Severity / Priority | **Low / Low**: cosmetic wording, no functional impact. |
| Recommendation | Use "item" when the count is 1. |
| Status | **Open** |

## Bug log
| Bug ID | Title | Severity | Priority | Status | Related case |
|---|---|---|---|---|---|
| BUG-001 | Server header disclosed versions (REAL, fixed) | Low | Low | Fixed, verified (E07, E12) | SEC-HDR-001 |
| BUG-002 | HTTP 500 for integer IDs >= 2^63 (REAL) | Low | Medium | **Fixed, verified** (pytest 185 passed) | SEC-INPUT-001 |
| BUG-003 | "(1 items)" grammar in order history (REAL) | Low | Low | Open | TC-ORD-001 |
| | | | | | |
