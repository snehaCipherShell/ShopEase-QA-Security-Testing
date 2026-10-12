# ShopEase Test Plan

| Field | Value |
|---|---|
| Project | ShopEase: E-commerce QA, API Testing & Security Validation |
| Document owner | *(your name)* |
| Version | 1.0 |
| Application under test | ShopEase (Flask + SQLite), local instance `http://127.0.0.1:5000` |
| Test environment | Linux / Kali Linux, Python 3.9+, Chrome/Firefox with DevTools, Postman, `sqlite3` |

> ShopEase is a fictional, local educational application. This plan describes learning exercises, not client work.

## 1. Objectives
1. Verify that ShopEase behaves according to its documented requirements (**validation** that the right product was built, **verification** that it was built correctly).
2. Find defects in registration, login, search, cart, checkout and order history before "release".
3. Validate the REST API contract: status codes, bodies, data types, required fields, authentication and authorization.
4. Validate stored data with SQL.
5. Perform basic, local-only security checks (authentication, authorization, input handling, session handling, price tampering).

## 2. Scope
**In scope:** registration, login/logout, session handling, product list and search, cart (add / update / remove / clear), subtotal and shipping calculation, simulated checkout, order history and cancellation, role check on `/api/admin/orders`, API error handling, basic security headers and cookie flags.

**Out of scope:** real payments, performance/load testing, accessibility audit, cross-browser matrix, email flows (none exist), mobile apps, any system other than the local ShopEase instance.

## 3. Requirements summary (the "specification" being tested)
| ID | Requirement |
|---|---|
| R-01 | A visitor can register with a unique username (3-20 chars: letters, digits, `_`), valid email, password 8-64 chars containing a letter and a digit. |
| R-02 | A registered user can log in and out; logout invalidates the session on the server. |
| R-03 | Anyone can list products and search by name/description (case-insensitive, max 100 chars). |
| R-04 | A logged-in user can add products to a cart: quantity is an integer 1-10 per product, limited by stock. |
| R-05 | Cart subtotal = sum(server price x quantity). Prices come only from the product table. |
| R-06 | Shipping is 5.00, free when subtotal >= 50.00. Order total = subtotal + shipping. |
| R-07 | Checkout (simulated payment only) creates an order, snapshots prices, reduces stock, clears the cart. |
| R-08 | A user sees only their own orders; others' orders are not accessible or modifiable. |
| R-09 | A PLACED order can be cancelled by its owner (restocks items); other states return 409. |
| R-10 | Errors use a consistent JSON shape and appropriate HTTP status codes; no stack traces are exposed. |

## 4. Test approach
| Level / type | How | Where |
|---|---|---|
| Manual functional (UI) | Execute detailed test cases in the browser | `docs/test-cases.md` |
| Exploratory | Time-boxed sessions with a charter (e.g. "explore cart edge cases for 30 min") | notes in `docs/test-execution-report.md` |
| API testing (manual) | Postman collection; scripted API-level replay of the manual cases | `postman/`, `scripts/replay_manual_cases.py` |
| API testing (automated) | pytest + requests against a live local server, fresh DB per test | `tests/` |
| Database validation | SQL queries | `sql/`, `docs/sql-validation.md` |
| Security (local only) | Manual + automated authorization/validation checks | `docs/security-test-cases.md` |
| Smoke / sanity / regression | Checklists | `docs/regression-checklist.md` |

**Techniques:** equivalence partitioning, boundary value analysis, positive/negative testing, error guessing, state-transition thinking (order PLACED -> CANCELLED).

## 5. Entry and exit criteria
**Entry:** build starts locally; database initialised with `python -m app.init_db --reset`; smoke checklist passes.
**Exit:** all planned test cases have a status other than *Not Run*; no open Critical/High defects; every failed case has a bug report; results documented honestly.

## 6. Test data
Seeded fictional users (`alice`, `bob`, `qa_admin`), 8 products with fixed prices, 3 seeded orders (see README). Automated tests create a new database for every test.

## 7. Risks and assumptions
| Risk | Mitigation |
|---|---|
| Manual results recorded from memory | Fill the execution report immediately after each case; attach screenshots |
| Shared database state between manual runs | Re-initialise with `--reset` before each cycle |
| Using these techniques on real systems | Prohibited; see Responsible Testing Scope in README |

## 8. Deliverables
Test plan, scenarios, cases, execution report (`test-execution-report.md`), evidence index (`evidence-index.md`), bug reports, security test cases, security test report (`security-test-report.md`) and findings register, regression checklist, API collection and automated suite, SQL queries.

## 9. Defect handling
Defects follow the lifecycle in `docs/qa-interview-notes.md` (New -> Assigned -> Open -> Fixed -> Retest -> Verified/Reopened -> Closed). Severity and priority are assigned using `docs/severity-priority-matrix.md`.
