-- Joins, aggregates, CTEs and window functions.
--
-- Written in the portable SQL subset, so it runs on PostgreSQL AND SQLite:
--   Postgres:  psql postgresql://postgres:pw@localhost:5432/postgres -f joins.sql
--   SQLite:    py -3.11 -c "import sqlite3;c=sqlite3.connect(':memory:');c.executescript(open('joins.sql').read())"
-- (the "-- >>" comments describe what each query should return)

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS employees;

CREATE TABLE customers (id integer PRIMARY KEY, name text NOT NULL, country text NOT NULL);
CREATE TABLE orders    (id integer PRIMARY KEY, customer_id integer REFERENCES customers(id), placed_on text NOT NULL, total integer NOT NULL);
CREATE TABLE order_items (order_id integer REFERENCES orders(id), sku text NOT NULL, qty integer NOT NULL);
CREATE TABLE employees (id integer PRIMARY KEY, name text NOT NULL, manager_id integer REFERENCES employees(id));

INSERT INTO customers VALUES (1, 'Ana', 'PT'), (2, 'Bo', 'US'), (3, 'Cy', 'US'), (4, 'Di', 'IN');   -- Di never ordered
INSERT INTO orders VALUES (10, 1, '2026-11-01', 100), (11, 1, '2026-11-05', 250), (12, 2, '2026-11-02', 80),
                          (13, 3, '2026-11-03', 500), (14, NULL, '2026-11-04', 40);                -- order 14: no customer
INSERT INTO order_items VALUES (10, 'pen', 2), (10, 'book', 1), (11, 'book', 5), (12, 'pen', 1);
INSERT INTO employees VALUES (1, 'Boss', NULL), (2, 'Mia', 1), (3, 'Ravi', 1), (4, 'Zoe', 2);

-- INNER JOIN: only rows that match on BOTH sides (customers with orders; order 14 and Di vanish)
SELECT c.name, o.id AS order_id, o.total
FROM customers c JOIN orders o ON o.customer_id = c.id
ORDER BY o.id;
-- >> Ana 10 100 | Ana 11 250 | Bo 12 80 | Cy 13 500

-- LEFT JOIN: keep ALL left rows, NULLs where nothing matches. Classic use: "who has NO orders?"
SELECT c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.id WHERE o.id IS NULL;
-- >> Di

-- LEFT JOIN gotcha: a filter on the RIGHT table in WHERE turns it back into an inner join. Put it in ON.
SELECT c.name, count(o.id) AS big_orders
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id AND o.total >= 200     -- filter in ON keeps Di, Bo (0)
GROUP BY c.name ORDER BY c.name;
-- >> Ana 1 | Bo 0 | Cy 1 | Di 0

-- FULL OUTER JOIN: everything from both sides, matched where possible (orphans on either side show up).
-- (SQLite supports FULL JOIN from 3.39+.) Handy for reconciling two datasets.
SELECT c.name, o.id AS order_id
FROM customers c FULL OUTER JOIN orders o ON o.customer_id = c.id
ORDER BY o.id, c.name;
-- >> includes Di with NULL order and order 14 with NULL customer

-- CROSS JOIN: every combination (rows = a x b). Use for generating grids, rarely otherwise.
SELECT c.country, i.sku FROM (SELECT DISTINCT country FROM customers) c CROSS JOIN (SELECT DISTINCT sku FROM order_items) i
ORDER BY 1, 2;

-- SELF JOIN: a table joined to itself (employee -> manager)
SELECT e.name AS employee, m.name AS manager
FROM employees e LEFT JOIN employees m ON m.id = e.manager_id ORDER BY e.id;
-- >> Boss NULL | Mia Boss | Ravi Boss | Zoe Mia

-- JOIN FAN-OUT: joining a 1:N table multiplies rows. SUM(total) over orders x items double counts order 10!
SELECT sum(o.total) AS wrong_total FROM orders o JOIN order_items i ON i.order_id = o.id;                   -- >> 530 (wrong)
SELECT sum(total) AS right_total FROM orders WHERE id IN (SELECT order_id FROM order_items);                -- >> 430 (right)
-- Fix pattern: aggregate the many-side in a subquery/CTE FIRST, then join the result.

-- GROUP BY / HAVING: WHERE filters rows before grouping, HAVING filters groups after.
SELECT c.country, count(*) AS orders, sum(o.total) AS revenue
FROM orders o JOIN customers c ON c.id = o.customer_id
GROUP BY c.country HAVING sum(o.total) > 100 ORDER BY revenue DESC;
-- >> PT 2 350 | US 2 580  (ordered by revenue: US first)

-- CTE (WITH): name a step so a big query reads top to bottom
WITH per_customer AS (
    SELECT customer_id, sum(total) AS spent FROM orders WHERE customer_id IS NOT NULL GROUP BY customer_id
)
SELECT c.name, p.spent FROM per_customer p JOIN customers c ON c.id = p.customer_id WHERE p.spent > 200 ORDER BY p.spent DESC;
-- >> Cy 500 | Ana 350

-- Correlated subquery / EXISTS: "customers that bought a book". EXISTS stops at the first match.
SELECT c.name FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o JOIN order_items i ON i.order_id = o.id WHERE o.customer_id = c.id AND i.sku = 'book')
ORDER BY c.name;
-- >> Ana

-- WINDOW FUNCTIONS: compute across related rows WITHOUT collapsing them like GROUP BY does.
SELECT customer_id, id AS order_id, total,
       sum(total) OVER (PARTITION BY customer_id)                            AS customer_total,   -- per-customer sum on every row
       row_number() OVER (PARTITION BY customer_id ORDER BY placed_on DESC)  AS recency,          -- 1 = latest order
       sum(total) OVER (ORDER BY placed_on)                                  AS running_total     -- running sum by date
FROM orders WHERE customer_id IS NOT NULL ORDER BY customer_id, recency;

-- Top-N per group (latest order per customer): the most useful window pattern
SELECT customer_id, id AS latest_order, total FROM (
    SELECT o.*, row_number() OVER (PARTITION BY customer_id ORDER BY placed_on DESC) AS rn
    FROM orders o WHERE customer_id IS NOT NULL
) t WHERE rn = 1 ORDER BY customer_id;
-- >> 1:11 | 2:12 | 3:13
