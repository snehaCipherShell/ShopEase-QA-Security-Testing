# ShopEase Test Scenarios

A **test scenario** is a one-line statement of *what* to test ("Verify a user can register"). A **test case** (see `test-cases.md`) says *exactly how*: data, steps and expected result. One scenario usually produces several test cases.

| Scenario ID | Scenario | Requirement | Detailed test cases | Automated coverage (file) |
|---|---|---|---|---|
| TS-01 | Verify a new user can register with valid data | R-01 | TC-REG-001 | `test_auth.py` |
| TS-02 | Verify registration rejects duplicate or invalid data | R-01 | TC-REG-002, 003, 004 | `test_auth.py` |
| TS-03 | Verify a registered user can log in and out | R-02 | TC-LOG-001, 003 | `test_auth.py` |
| TS-04 | Verify login rejects wrong credentials | R-02 | TC-LOG-002 | `test_auth.py` |
| TS-05 | Verify product search returns relevant results | R-03 | TC-SRC-001, 002, 003 | `test_products.py` |
| TS-06 | Verify items can be added, updated and removed from the cart | R-04 | TC-CRT-001, 002, 003 | `test_cart.py` |
| TS-07 | Verify quantity limits are enforced | R-04 | TC-CRT-004, 005, 006 | `test_cart.py` |
| TS-08 | Verify out-of-stock products cannot be bought | R-04 | TC-CRT-007 | `test_cart.py` |
| TS-09 | Verify cart and order totals are calculated correctly | R-05, R-06 | TC-CAL-001, 002 | `test_cart.py`, `test_orders.py` |
| TS-10 | Verify checkout creates an order | R-07 | TC-CHK-001 | `test_orders.py` |
| TS-11 | Verify checkout rejects an empty cart or incomplete details | R-07 | TC-CHK-002, 003 | `test_orders.py` |
| TS-12 | Verify order history shows only the user's own orders | R-08 | TC-ORD-001 | `test_orders.py`, `test_authorization.py` |
| TS-13 | Verify an order can be cancelled once | R-09 | TC-ORD-002 | `test_orders.py` |
| TS-14 | Verify API errors are consistent and safe | R-10 | (API/Postman) | `test_api_validation.py`, `test_security_headers.py` |
| TS-15 | Verify protected data cannot be reached without permission | R-08 | SEC-AUTHZ-001..004 | `test_authorization.py` |

## Equivalence partitions and boundary values (test design)

| Input | Valid partition | Invalid partitions | Boundary values to test |
|---|---|---|---|
| Username length | 3-20 allowed chars | <3, >20, illegal characters, empty | 2, **3**, **20**, 21 |
| Password length | 8-64 with letter + digit | <8, >64, letters only, digits only | 7, **8**, **64**, 65 |
| Cart quantity | integers 1-10 | 0, negatives, >10, text, decimal, null, boolean | 0, **1**, **10**, 11 |
| Subtotal (shipping) | >= 50.00 free | < 50.00 pays 5.00 | 45.00 (9 notebooks), **50.00** (10 notebooks) |
| Search text | 0-100 chars | >100 chars | 100, 101 |
| Shipping name | 2-60 chars | <2, >60, non-text | 1, **2**, **60**, 61 |
