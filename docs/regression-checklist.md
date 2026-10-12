# Regression and Smoke Checklists

**Smoke test** = quick check that the build is stable enough to test further (minutes). **Sanity test** = narrow check that a specific fix or small change works. **Regression test** = re-run of previously passing areas to confirm nothing else broke after a change. **Retest** = re-running the exact failed case after a fix.

Mark each box only after actually performing the check. Reset data first: `python -m app.init_db --reset`.

## A. Smoke (run on every new build)
- [ ] App starts with `python run.py`; `http://127.0.0.1:5000/` loads
- [ ] Product list shows 8 products
- [ ] Log in as `alice` succeeds; logout succeeds
- [ ] Add a product to the cart; subtotal is correct
- [ ] Checkout creates an order
- [ ] `pytest -q` collects and runs without import errors

## B. Sanity (after a specific fix)
| Change | Checks |
|---|---|
| Cart calculation fix | TC-CAL-001, TC-CAL-002, `pytest tests/test_cart.py tests/test_orders.py` |
| Login/session fix | TC-LOG-001..003, `pytest tests/test_auth.py tests/test_authorization.py` |
| Search fix | TC-SRC-001..003, `pytest tests/test_products.py` |

## C. Full regression
| Area | Manual cases | Automated | Done |
|---|---|---|---|
| Registration | TC-REG-001..004 | `test_auth.py` | [ ] |
| Login / logout / session | TC-LOG-001..003 | `test_auth.py`, `test_authorization.py` | [ ] |
| Search | TC-SRC-001..003 | `test_products.py` | [ ] |
| Cart | TC-CRT-001..007 | `test_cart.py` | [ ] |
| Calculations | TC-CAL-001..002 | `test_cart.py`, `test_orders.py` | [ ] |
| Checkout | TC-CHK-001..003 | `test_orders.py` | [ ] |
| Orders | TC-ORD-001..002 | `test_orders.py` | [ ] |
| API validation | Postman folders 01-05 | `test_api_validation.py` | [ ] |
| Authorization & security | SEC-* | `test_authorization.py`, `test_security_headers.py` | [ ] |
| Database integrity | SQL A11, A13, A14, A18 return 0 rows | order totals tests | [ ] |

## D. Release-style sign-off (template)
| Item | Result |
|---|---|
| Smoke passed | |
| Regression passed | |
| Open defects (Critical/High) | |
| Known limitations accepted | see README "Limitations" |
| Tester / date | |
