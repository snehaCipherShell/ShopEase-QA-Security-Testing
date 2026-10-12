# ShopEase Detailed Test Cases

All results below are **Not Run** until you execute them. Fill in *Actual result*, *Status* (Pass / Fail / Blocked / Not Run), *Remarks* and attach evidence in `screenshots/`. Never mark Pass without having executed the case and observed the expected result. Reset data with `python -m app.init_db --reset` before each cycle.

Base URL: `http://127.0.0.1:5000`. Test accounts: `alice / AlicePass123`, `bob / BobPass1234`, `qa_admin / AdminPass123` (fictional, local only).

## Index

| ID | Title | Requirement | Scenario |
|---|---|---|---|
| TC-REG-001 | Register with valid details | R-01 | TS-01 |
| TC-REG-002 | Register with an already used username (case variation) | R-01 | TS-02 |
| TC-REG-003 | Register with a 7-character password (boundary - below minimum) | R-01 | TS-02 |
| TC-REG-004 | Register with an 8-character password (boundary - minimum) | R-01 | TS-02 |
| TC-LOG-001 | Log in with valid credentials | R-02 | TS-03 |
| TC-LOG-002 | Log in with a wrong password | R-02 | TS-04 |
| TC-LOG-003 | Log out and confirm the session is closed | R-02 | TS-03 |
| TC-SRC-001 | Search for an existing product | R-03 | TS-05 |
| TC-SRC-002 | Search with no matching product | R-03 | TS-05 |
| TC-SRC-003 | Search is case-insensitive | R-03 | TS-05 |
| TC-CRT-001 | Add a product to the cart | R-04 | TS-06 |
| TC-CRT-002 | Update the quantity of a cart item | R-04 | TS-06 |
| TC-CRT-003 | Remove an item from the cart | R-04 | TS-06 |
| TC-CRT-004 | Add quantity 0 (invalid, boundary below minimum) | R-04 | TS-07 |
| TC-CRT-005 | Add quantity 10 (valid, boundary maximum) | R-04 | TS-07 |
| TC-CRT-006 | Add quantity 11 (invalid, boundary above maximum) | R-04 | TS-07 |
| TC-CRT-007 | Add an out-of-stock product | R-04 | TS-08 |
| TC-CAL-001 | Cart subtotal with two products | R-05 | TS-09 |
| TC-CAL-002 | Free-shipping boundary at 50.00 | R-06 | TS-09 |
| TC-CHK-001 | Successful checkout with simulated payment | R-07 | TS-10 |
| TC-CHK-002 | Checkout with an empty cart | R-07 | TS-11 |
| TC-CHK-003 | Checkout with missing shipping address | R-07 | TS-11 |
| TC-ORD-001 | Order history shows only my orders | R-08 | TS-12 |
| TC-ORD-002 | Cancel a PLACED order and restock | R-09 | TS-13 |

## TC-REG-001 - Register with valid details

**Requirement:** R-01 | **Scenario:** TS-01 | **Type:** Positive

**Preconditions:** Application running; DB freshly initialised; username `qa_tester1` does not exist.

**Test data:** username `qa_tester1`, email `qa_tester1@example.test`, password `Passw0rd1`

**Steps:**

1. Open http://127.0.0.1:5000/
2. In the Register form enter the test data
3. Click **Register**
4. Open DevTools > Network and check the `register` request
5. Run SQL A4 (`sql/qa-validation-queries.sql`) for `qa_tester1`

**Expected result:** Message 'Registration successful'. API returns **201** with id, username, email, role `customer` and **no** password fields. Exactly 1 row in `users`; `password_hash` differs from the typed password.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-REG-002 - Register with an already used username (case variation)

**Requirement:** R-01 | **Scenario:** TS-02 | **Type:** Negative

**Preconditions:** Seed data loaded (user `alice` exists).

**Test data:** username `ALICE`, email `other@example.test`, password `Passw0rd1`

**Steps:**

1. Open the app
2. Enter the test data in the Register form
3. Click **Register**
4. Count rows in `users` before and after (SQL A16)

**Expected result:** Error message shown; API returns **409**; no new row in `users`.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-REG-003 - Register with a 7-character password (boundary - below minimum)

**Requirement:** R-01 | **Scenario:** TS-02 | **Type:** Negative

**Preconditions:** App running.

**Test data:** username `qa_tester2`, email `qa_tester2@example.test`, password `Abcdef1` (7 chars)

**Steps:**

1. Open the app
2. Enter the test data
3. Click **Register**

**Expected result:** Registration rejected; API **400** `validation_error` with a `password` field message; no row created for `qa_tester2`.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-REG-004 - Register with an 8-character password (boundary - minimum)

**Requirement:** R-01 | **Scenario:** TS-02 | **Type:** Positive

**Preconditions:** App running; `qa_tester3` does not exist.

**Test data:** username `qa_tester3`, email `qa_tester3@example.test`, password `Abcdef12` (8 chars)

**Steps:**

1. Open the app
2. Enter the test data
3. Click **Register**

**Expected result:** Registration succeeds (**201**).

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-LOG-001 - Log in with valid credentials

**Requirement:** R-02 | **Scenario:** TS-03 | **Type:** Positive

**Preconditions:** Seed data loaded.

**Test data:** username `alice`, password `AlicePass123`

**Steps:**

1. Open the app
2. Enter credentials in the Login form and click **Login**
3. Observe the header text
4. DevTools > Application > Cookies: inspect `shopease_session`

**Expected result:** Header shows 'Logged in as alice'. Login returns **200**. Cookie `shopease_session` exists with HttpOnly and SameSite=Lax. Cart and order history load.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-LOG-002 - Log in with a wrong password

**Requirement:** R-02 | **Scenario:** TS-04 | **Type:** Negative

**Preconditions:** Seed data loaded; logged out.

**Test data:** username `alice`, password `WrongPass123`

**Steps:**

1. Enter the data in the Login form
2. Click **Login**
3. Check cookies

**Expected result:** Message 'Invalid username or password'; API **401**; no session cookie set; header still says 'Not logged in'.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-LOG-003 - Log out and confirm the session is closed

**Requirement:** R-02 | **Scenario:** TS-03 | **Type:** Positive

**Preconditions:** Logged in as `alice`.

**Test data:** n/a

**Steps:**

1. Click **Logout**
2. Refresh the page
3. In DevTools Network note the `me` request status
4. Run SQL A17 to check the `sessions` table

**Expected result:** Header shows 'Not logged in'; `GET /api/auth/me` returns **401**; the session row is gone from `sessions`; cart/orders are not shown.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-SRC-001 - Search for an existing product

**Requirement:** R-03 | **Scenario:** TS-05 | **Type:** Positive

**Preconditions:** App running.

**Test data:** search text `mouse`

**Steps:**

1. Type `mouse` in the search box
2. Click **Search**

**Expected result:** Only 'Wireless Mouse' (19.99) is listed.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-SRC-002 - Search with no matching product

**Requirement:** R-03 | **Scenario:** TS-05 | **Type:** Negative

**Preconditions:** App running.

**Test data:** search text `zzzz-nothing`

**Steps:**

1. Type the text
2. Click **Search**

**Expected result:** 'No products found.' is shown; API returns **200** with `count` 0 (not an error).

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-SRC-003 - Search is case-insensitive

**Requirement:** R-03 | **Scenario:** TS-05 | **Type:** Positive

**Preconditions:** App running.

**Test data:** search text `LAPTOP`

**Steps:**

1. Type the text
2. Click **Search**

**Expected result:** 'Laptop Stand' is listed.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-001 - Add a product to the cart

**Requirement:** R-04 | **Scenario:** TS-06 | **Type:** Positive

**Preconditions:** Logged in as `alice`; cart empty.

**Test data:** product Wireless Mouse (19.99), quantity 2

**Steps:**

1. Search or list products
2. Set the quantity field of Wireless Mouse to 2
3. Click **Add to cart**

**Expected result:** Cart shows Wireless Mouse x2, line total 39.98, subtotal 39.98.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-002 - Update the quantity of a cart item

**Requirement:** R-04 | **Scenario:** TS-06 | **Type:** Positive

**Preconditions:** Cart contains Wireless Mouse x2.

**Test data:** new quantity 5

**Steps:**

1. In the cart change the quantity of Wireless Mouse to 5 and press Tab/Enter

**Expected result:** Line total 99.95, subtotal 99.95; message 'Cart updated.'

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-003 - Remove an item from the cart

**Requirement:** R-04 | **Scenario:** TS-06 | **Type:** Positive

**Preconditions:** Cart contains at least one item.

**Test data:** n/a

**Steps:**

1. Click **Remove** on one line

**Expected result:** The line disappears and the subtotal is recalculated; API returns 200.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-004 - Add quantity 0 (invalid, boundary below minimum)

**Requirement:** R-04 | **Scenario:** TS-07 | **Type:** Negative

**Preconditions:** Logged in; cart empty.

**Test data:** product 1, quantity 0

**Steps:**

1. Set quantity 0 on Wireless Mouse
2. Click **Add to cart**
3. Run SQL A15 for the user

**Expected result:** Error message; API **400** `validation_error`; cart still empty.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-005 - Add quantity 10 (valid, boundary maximum)

**Requirement:** R-04 | **Scenario:** TS-07 | **Type:** Positive

**Preconditions:** Logged in; cart empty.

**Test data:** product 1, quantity 10

**Steps:**

1. Set quantity 10
2. Click **Add to cart**

**Expected result:** Item added (201), subtotal 199.90.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-006 - Add quantity 11 (invalid, boundary above maximum)

**Requirement:** R-04 | **Scenario:** TS-07 | **Type:** Negative

**Preconditions:** Logged in; cart empty.

**Test data:** product 1, quantity 11

**Steps:**

1. Set quantity 11 (type the value; the spinner limit is only a UI hint)
2. Click **Add to cart**

**Expected result:** Error message; API **400**; cart unchanged. (The server must enforce this even if the browser input is bypassed.)

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CRT-007 - Add an out-of-stock product

**Requirement:** R-04 | **Scenario:** TS-08 | **Type:** Negative

**Preconditions:** Logged in; Desk Lamp has stock 0.

**Test data:** product 7 (Desk Lamp), quantity 1

**Steps:**

1. Find 'Desk Lamp' (listed as out of stock)
2. Click **Add to cart**

**Expected result:** Error message 'Not enough stock available.'; API **409** `insufficient_stock`; cart unchanged.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CAL-001 - Cart subtotal with two products

**Requirement:** R-05 | **Scenario:** TS-09 | **Type:** Positive

**Preconditions:** Logged in; cart empty.

**Test data:** 2 x Wireless Mouse (19.99), 3 x USB-C Cable (9.99)

**Steps:**

1. Add both items
2. Read the cart subtotal

**Expected result:** Subtotal = 39.98 + 29.97 = **69.95**.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CAL-002 - Free-shipping boundary at 50.00

**Requirement:** R-06 | **Scenario:** TS-09 | **Type:** Positive

**Preconditions:** Logged in; cart empty; seeded stock.

**Test data:** Case A: 9 x Notebook A5 (5.00) = 45.00. Case B: 10 x Notebook A5 = 50.00

**Steps:**

1. Case A: add 9 notebooks and check out with valid details
2. Note shipping and total
3. Case B: (new cart) add 10 notebooks and check out
4. Note shipping and total

**Expected result:** Case A: shipping **5.00**, total **50.00**. Case B: shipping **0.00**, total **50.00**.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CHK-001 - Successful checkout with simulated payment

**Requirement:** R-07 | **Scenario:** TS-10 | **Type:** Positive

**Preconditions:** Logged in as `alice`; cart has 2 x Wireless Mouse.

**Test data:** name `Test Buyer`, address `1 Test Street, Testville`

**Steps:**

1. Enter shipping name and address
2. Click **Place order (simulated payment)**
3. Run SQL A9, A10, A11 and check stock of product 1

**Expected result:** Message with order number; total 44.98 (39.98 + 5.00 shipping); order appears in history as PLACED; cart empty; stock of product 1 reduced by 2; stored totals consistent (A11 returns 0 rows).

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CHK-002 - Checkout with an empty cart

**Requirement:** R-07 | **Scenario:** TS-11 | **Type:** Negative

**Preconditions:** Logged in; cart empty.

**Test data:** valid shipping details

**Steps:**

1. Enter details and click **Place order**
2. Run SQL A16 before/after

**Expected result:** Error 'Your cart is empty.'; API **400** `empty_cart`; no order created.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-CHK-003 - Checkout with missing shipping address

**Requirement:** R-07 | **Scenario:** TS-11 | **Type:** Negative

**Preconditions:** Cart has one item.

**Test data:** name `Test Buyer`, address empty

**Steps:**

1. Leave the address blank (remove the browser `required` attribute via DevTools Elements to reach the server check)
2. Submit
3. Check the response in Network

**Expected result:** API **400** with a `shipping_address` field message; no order; cart preserved.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-ORD-001 - Order history shows only my orders

**Requirement:** R-08 | **Scenario:** TS-12 | **Type:** Positive

**Preconditions:** Seed data loaded.

**Test data:** users `alice` and `bob`

**Steps:**

1. Log in as alice and read Order history
2. Log out; log in as bob and read Order history

**Expected result:** alice sees orders #3 and #1 only; bob sees order #2 only.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---

## TC-ORD-002 - Cancel a PLACED order and restock

**Requirement:** R-09 | **Scenario:** TS-13 | **Type:** Positive

**Preconditions:** Logged in; one PLACED order exists (from TC-CHK-001).

**Test data:** the order id

**Steps:**

1. Click **Cancel** next to the order
2. Check status and stock of product 1
3. Try cancelling again via Postman 'Cancel my order again'

**Expected result:** Status becomes CANCELLED, stock restored; the second cancel returns **409** `invalid_state`.

**Actual result:** *Not executed yet*

**Status:** Not Run

**Remarks:**

---
