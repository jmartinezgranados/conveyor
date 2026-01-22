-- V002__create_analytics_views.sql
-- Crea vistas para análisis y reporting

-- Vista de ventas por producto
CREATE OR REPLACE VIEW vw_sales_by_product AS
SELECT
    p.product_id,
    p.product_name,
    p.category,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.quantity * oi.unit_price) AS total_revenue,
    AVG(oi.unit_price) AS avg_selling_price,
    MAX(o.order_date) AS last_order_date
FROM products p
INNER JOIN order_items oi ON p.product_id = oi.product_id
INNER JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY
    p.product_id,
    p.product_name,
    p.category;

-- Vista de ventas por cliente
CREATE OR REPLACE VIEW vw_sales_by_customer AS
SELECT
    c.customer_id,
    c.customer_name,
    c.email,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_spent,
    AVG(o.total_amount) AS avg_order_value,
    MIN(o.order_date) AS first_order_date,
    MAX(o.order_date) AS last_order_date,
    DATEDIFF(CURRENT_DATE(), MAX(o.order_date)) AS days_since_last_order
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status IN ('completed', 'shipped')
GROUP BY
    c.customer_id,
    c.customer_name,
    c.email;

-- Vista de órdenes pendientes
CREATE OR REPLACE VIEW vw_pending_orders AS
SELECT
    o.order_id,
    c.customer_name,
    c.email,
    o.order_date,
    o.total_amount,
    o.status,
    COUNT(oi.order_item_id) AS total_items,
    DATEDIFF(CURRENT_DATE(), o.order_date) AS days_pending
FROM orders o
INNER JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status IN ('pending', 'processing')
GROUP BY
    o.order_id,
    c.customer_name,
    c.email,
    o.order_date,
    o.total_amount,
    o.status;

-- Comentarios en vistas
COMMENT ON VIEW vw_sales_by_product IS 'Métricas de ventas agregadas por producto';
COMMENT ON VIEW vw_sales_by_customer IS 'Métricas de ventas agregadas por cliente';
COMMENT ON VIEW vw_pending_orders IS 'Órdenes que están pendientes o en proceso';
