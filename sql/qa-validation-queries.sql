-- =====================================================================
-- ShopEase QA validation queries  (SQLite)
-- Run against a LOCAL TEST database only:
--     sqlite3 instance/shopease.db < sql/qa-validation-queries.sql   (not recommended: run section by section)
--     sqlite3 -header -column instance/shopease.db      (then paste one query at a time)
-- Section A and B are READ-ONLY.  Section C CHANGES DATA - test database only.
-- Seeded reference data: users alice(1), bob(2), qa_admin(3); orders 1 (alice), 2 (bob), 3 (alice, CANCELLED).
-- =====================================================================

-- ############################ SECTION A: READ-ONLY ############################

-- A1. SELECT + WHERE: find one product
SELECT id, name, price_cents, stock FROM products WHERE name = 'Wireless Mouse';

-- A2. ORDER BY: cheapest products first
SELECT name, price_cents / 100.0 AS price FROM products ORDER BY price_cents ASC, name;

-- A3. COUNT: how many products, and how many are out of stock?
SELECT COUNT(*) AS total_products, SUM(CASE WHEN stock = 0 THEN 1 ELSE 0 END) AS out_of_stock FROM products;

-- A4. Validate a registration (replace 'new_user1' with the username you registered).
--     Expect exactly 1 row, role = 'customer', password_hash NOT equal to the password you typed.
SELECT id, username, email, role, substr(password_hash, 1, 20) AS hash_prefix, created_at
FROM users WHERE username = 'new_user1';

-- A5. Duplicate check: usernames or emails that appear more than once (expect 0 rows)
SELECT lower(username) AS name, COUNT(*) AS n FROM users GROUP BY lower(username) HAVING COUNT(*) > 1;
SELECT lower(email)    AS mail, COUNT(*) AS n FROM users GROUP BY lower(email)    HAVING COUNT(*) > 1;

-- A6. INNER JOIN: orders with their owner (only orders that have a matching user)
SELECT o.id AS order_id, u.username, o.status, o.total_cents / 100.0 AS total
FROM orders o INNER JOIN users u ON u.id = o.user_id ORDER BY o.id;

-- A7. LEFT JOIN: every user, including users with NO orders (order_id will be NULL for them)
SELECT u.username, o.id AS order_id, o.status
FROM users u LEFT JOIN orders o ON o.user_id = u.id ORDER BY u.id, o.id;

-- A8. LEFT JOIN + IS NULL: users who have never placed an order
SELECT u.username FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL;

-- A9. Order ownership and status: did the order land on the right account?
--     Replace 1 with the order id returned by the API. Compare user_id with the id of the user who placed it.
SELECT o.id, o.user_id, u.username, o.status FROM orders o JOIN users u ON u.id = o.user_id WHERE o.id = 1;

-- A10. Order lines for one order, with price at time of purchase
SELECT oi.order_id, oi.product_name, oi.unit_price_cents / 100.0 AS unit_price, oi.quantity,
       oi.line_total_cents / 100.0 AS line_total
FROM order_items oi WHERE oi.order_id = 2 ORDER BY oi.id;

-- A11. Stored order totals must equal the sum of their lines + shipping (expect 0 rows = no mismatch)
SELECT o.id, o.subtotal_cents, SUM(oi.line_total_cents) AS lines_sum, o.shipping_cents, o.total_cents
FROM orders o JOIN order_items oi ON oi.order_id = o.id
GROUP BY o.id
HAVING o.subtotal_cents <> SUM(oi.line_total_cents) OR o.total_cents <> o.subtotal_cents + o.shipping_cents;

-- A12. Stored line price vs CURRENT catalog price (differences are expected if the catalog price changed
--      after purchase; a difference on a brand-new order would deserve investigation)
SELECT oi.order_id, oi.product_name, oi.unit_price_cents AS paid, p.price_cents AS current_price
FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.unit_price_cents <> p.price_cents;

-- A13. Line total = unit price x quantity (expect 0 rows)
SELECT id, unit_price_cents, quantity, line_total_cents FROM order_items
WHERE line_total_cents <> unit_price_cents * quantity;

-- A14. Orphan check: order lines whose order does not exist (expect 0 rows)
SELECT oi.id FROM order_items oi LEFT JOIN orders o ON o.id = oi.order_id WHERE o.id IS NULL;

-- A15. Cart contents with live prices for one user (replace 1 with the user id)
SELECT p.name, c.quantity, p.price_cents / 100.0 AS unit_price, c.quantity * p.price_cents / 100.0 AS line_total
FROM cart_items c JOIN products p ON p.id = c.product_id WHERE c.user_id = 1;

-- A16. "Nothing unexpected was created" pattern: take counts BEFORE the action, run the invalid request,
--      take counts AFTER, compare. Run this block before and after and compare the numbers by hand.
SELECT (SELECT COUNT(*) FROM users) AS users, (SELECT COUNT(*) FROM orders) AS orders,
       (SELECT COUNT(*) FROM order_items) AS order_items, (SELECT COUNT(*) FROM cart_items) AS cart_items,
       (SELECT COUNT(*) FROM sessions) AS sessions;

-- A17. Sessions: is the session of a logged-out user gone? (count should drop by 1 after logout)
SELECT s.user_id, u.username, datetime(s.expires_at, 'unixepoch') AS expires FROM sessions s JOIN users u ON u.id = s.user_id;

-- A18. Stock sanity: no negative stock (the CHECK constraint should make this impossible; expect 0 rows)
SELECT id, name, stock FROM products WHERE stock < 0;

-- ############################ SECTION B: SCHEMA INSPECTION (READ-ONLY) ############################
-- .tables            (sqlite3 shell command)
-- .schema orders     (sqlite3 shell command)
PRAGMA table_info(orders);
PRAGMA foreign_key_list(order_items);

-- ############################ SECTION C: DATA-CHANGING (TEST DATABASE ONLY) ############################
-- WARNING: INSERT/UPDATE/DELETE modify data. Run ONLY on a local, disposable, authorised test database
-- (e.g. a copy:  cp instance/shopease.db /tmp/practice.db).  ALWAYS include a WHERE clause on UPDATE/DELETE
-- and run the matching SELECT first to see which rows you are about to change.
-- Re-create a clean database any time with:  python -m app.init_db --reset

-- C1. INSERT a test product, then verify
INSERT INTO products (id, sku, name, description, category, price_cents, stock)
VALUES (900, 'TST-900', 'QA Test Item', 'Row created by a QA exercise', 'Test', 100, 5);
SELECT * FROM products WHERE id = 900;

-- C2. UPDATE: preview first, then change exactly one row
SELECT id, stock FROM products WHERE id = 900;
UPDATE products SET stock = 0 WHERE id = 900;
SELECT id, stock FROM products WHERE id = 900;   -- now an out-of-stock test case: try adding it to a cart (expect 409)

-- C3. DELETE: preview first, then delete exactly one row
SELECT id, name FROM products WHERE id = 900;
DELETE FROM products WHERE id = 900;
SELECT COUNT(*) FROM products WHERE id = 900;   -- expect 0

-- C4. Foreign keys protect data: deleting a user who has orders should FAIL (orders.user_id references users).
--     Needs: PRAGMA foreign_keys = ON;  (sqlite3 shell does not enable it by default)
PRAGMA foreign_keys = ON;
-- DELETE FROM users WHERE username = 'bob';     -- uncomment to try; expect "FOREIGN KEY constraint failed"

-- C5. Simulate a price change after purchase, then confirm the old order keeps its price snapshot
-- UPDATE products SET price_cents = 2999 WHERE id = 1;
-- SELECT unit_price_cents FROM order_items WHERE product_id = 1;    -- old orders must be unchanged
