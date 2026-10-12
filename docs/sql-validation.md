# SQL and Database Validation

Why QA uses SQL: the UI or API can *say* something worked while the database tells a different story (duplicate rows, wrong ownership, totals that don't add up, records created by failed requests). All queries are in `sql/qa-validation-queries.sql`; labels A1-A18 below match that file.

## Safety first
- Use a **local, disposable, authorised test database**. Never run these against a real or shared database.
- **SELECT is read-only. INSERT/UPDATE/DELETE change data.** For UPDATE and DELETE, always (1) write the matching `SELECT ... WHERE` first, (2) check the rows, (3) then run the change with the **same** `WHERE`. Without `WHERE`, *every row* changes.
- Work on a copy: `cp instance/shopease.db /tmp/practice.db` and `sqlite3 -header -column /tmp/practice.db`. Re-create a clean DB with `python -m app.init_db --reset`.
- SQLite does not enforce foreign keys unless you run `PRAGMA foreign_keys = ON;`.

## Schema in one minute
`users` -> `sessions`, `cart_items`, `orders` -> `order_items`; `products` referenced by cart and order lines. Money is stored in **cents** (integers) to avoid rounding errors: 1999 = 19.99.

## Read-only examples (explained)
| ID | Query idea | What it validates |
|---|---|---|
| A1 | `SELECT ... WHERE name = '...'` | Filter rows |
| A2 | `ORDER BY price_cents` | Sorting |
| A3 | `COUNT(*)`, conditional `SUM` | Counts, out-of-stock products |
| A4 | Registration record | Exactly 1 row, role `customer`, password stored as a hash |
| A5 | `GROUP BY ... HAVING COUNT(*) > 1` | Duplicate usernames/emails (expect none) |
| A6 | `INNER JOIN` orders-users | Only orders that have a matching user |
| A7 | `LEFT JOIN` users-orders | *All* users, even those without orders (NULL order) |
| A8 | `LEFT JOIN ... WHERE o.id IS NULL` | Users with no orders |
| A9 | Order ownership and status | `orders.user_id` equals the user who placed it |
| A10 | Order lines | Price snapshot and quantity per product |
| A11 | Totals vs lines | `subtotal = SUM(lines)` and `total = subtotal + shipping` (expect 0 mismatch rows) |
| A12 | Order price vs current catalog price | Differences are normal if the catalog changed later |
| A13 | `line_total = unit_price x quantity` | Arithmetic integrity |
| A14 | Orphan check | Order lines without an order |
| A15 | Cart with live prices | Compare with the cart shown in the UI |
| A16 | Row counts of key tables | "Failed or invalid requests created nothing" pattern |
| A17 | Sessions | Logout removes the row |
| A18 | Negative stock | Should be impossible (CHECK constraint) |

### Example workflow: "Did a failed checkout create anything?"
1. Log in as `alice`, make sure the cart is empty.
2. Run **A16** and write down the counts (`orders`, `order_items`, `cart_items`).
3. In the UI/Postman perform `POST /api/checkout` with an empty cart (expect **400** `empty_cart`).
4. Run **A16** again. Expected: counts unchanged. Record both outputs as evidence.

### Example workflow: "Does the stored total match the cart I saw?"
1. Add 2 x Wireless Mouse and 3 x USB-C Cable (subtotal 69.95 on screen).
2. Checkout; note the order id.
3. Run **A10** for that id and **A11**. Expected: lines 3998 + 2997 = 6995 cents; total 6995 (free shipping); A11 returns no rows.

## Data-changing examples (test database only)
Section C of the SQL file shows INSERT, UPDATE and DELETE on a clearly labelled test product (`id 900`): each with a preview SELECT and a verification SELECT. A QA use: set `stock = 0` to create an out-of-stock scenario; delete the test row afterwards. Also shown: deleting a user who owns orders is blocked by a foreign key (needs `PRAGMA foreign_keys = ON`).

## What was actually executed
The author ran all 30 statements of the file against a temporary seeded database with Python's `sqlite3` module: **30 executed, 0 SQL errors**. Query *results* on your own data are **Not Run** until you execute them; record them in `test-execution-report.md`.

## Interpreting results
A database check can confirm *what is stored*, not *why*. A wrong value could come from the UI, API or database layer: investigate before assigning blame.
