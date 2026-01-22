-- V001__create_base_tables.sql
-- Crea las tablas base del proyecto

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT GENERATED ALWAYS AS IDENTITY,
    customer_name STRING NOT NULL,
    email STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
) USING DELTA
COMMENT 'Tabla de clientes';

-- Tabla de productos
CREATE TABLE IF NOT EXISTS products (
    product_id BIGINT GENERATED ALWAYS AS IDENTITY,
    product_name STRING NOT NULL,
    category STRING,
    price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_products PRIMARY KEY (product_id)
) USING DELTA
COMMENT 'Catálogo de productos';

-- Tabla de órdenes
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT GENERATED ALWAYS AS IDENTITY,
    customer_id BIGINT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    total_amount DECIMAL(10, 2),
    status STRING DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_orders PRIMARY KEY (order_id)
) USING DELTA
COMMENT 'Órdenes de compra';

-- Tabla de items de orden
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id BIGINT GENERATED ALWAYS AS IDENTITY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT pk_order_items PRIMARY KEY (order_item_id)
) USING DELTA
COMMENT 'Items de cada orden';

-- Comentarios en columnas
COMMENT ON TABLE customers IS 'Clientes registrados';
COMMENT ON TABLE products IS 'Catálogo de productos disponibles';
COMMENT ON TABLE orders IS 'Órdenes realizadas por clientes';
COMMENT ON TABLE order_items IS 'Detalle de productos en cada orden';
