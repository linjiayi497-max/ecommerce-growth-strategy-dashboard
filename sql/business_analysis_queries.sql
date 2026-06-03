-- SQL examples for interviews and analyst case discussion.
-- The demo CSV files can be loaded into a warehouse with tables:
-- demo_orders, demo_events, demo_ab_test.

-- 1. Monthly revenue and gross margin trend.
SELECT
    DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS orders,
    COUNT(DISTINCT customer_id) AS customers,
    SUM(net_revenue) AS net_revenue,
    SUM(gross_margin) / NULLIF(SUM(net_revenue), 0) AS gross_margin_rate
FROM demo_orders
GROUP BY 1
ORDER BY 1;

-- 2. Funnel conversion by session.
WITH session_steps AS (
    SELECT
        session_id,
        MAX(CASE WHEN event_type = 'visit' THEN 1 ELSE 0 END) AS visit,
        MAX(CASE WHEN event_type = 'product_view' THEN 1 ELSE 0 END) AS product_view,
        MAX(CASE WHEN event_type = 'add_to_cart' THEN 1 ELSE 0 END) AS add_to_cart,
        MAX(CASE WHEN event_type = 'checkout' THEN 1 ELSE 0 END) AS checkout,
        MAX(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase
    FROM demo_events
    GROUP BY 1
)
SELECT
    SUM(visit) AS visits,
    SUM(product_view) AS product_views,
    SUM(add_to_cart) AS add_to_carts,
    SUM(checkout) AS checkouts,
    SUM(purchase) AS purchases,
    SUM(purchase) * 1.0 / NULLIF(SUM(visit), 0) AS visit_to_purchase_rate
FROM session_steps;

-- 3. A/B test conversion and revenue per session.
SELECT
    variant,
    COUNT(DISTINCT session_id) AS sessions,
    SUM(converted) AS conversions,
    SUM(converted) * 1.0 / COUNT(DISTINCT session_id) AS conversion_rate,
    SUM(net_revenue) / COUNT(DISTINCT session_id) AS revenue_per_session,
    SUM(coupon_spend) / NULLIF(SUM(net_revenue), 0) AS coupon_to_revenue
FROM demo_ab_test
GROUP BY 1;

-- 4. First-purchase cohort retention base table.
WITH first_order AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM demo_orders
    GROUP BY 1
),
orders_with_cohort AS (
    SELECT
        o.customer_id,
        f.cohort_month,
        DATE_TRUNC('month', o.order_date) AS order_month
    FROM demo_orders o
    JOIN first_order f ON o.customer_id = f.customer_id
)
SELECT
    cohort_month,
    order_month,
    COUNT(DISTINCT customer_id) AS retained_customers
FROM orders_with_cohort
GROUP BY 1, 2
ORDER BY 1, 2;

