-- Mini Prism POS Service — Initial Schema
-- V1__init_pos_schema.sql

CREATE TABLE sales (
    id               BIGSERIAL PRIMARY KEY,
    reference_number VARCHAR(30)    NOT NULL UNIQUE,
    cashier_username VARCHAR(100)   NOT NULL,
    status           VARCHAR(20)    NOT NULL DEFAULT 'PENDING',
    subtotal         NUMERIC(10, 2) NOT NULL,
    tax_amount       NUMERIC(10, 2) NOT NULL,
    total            NUMERIC(10, 2) NOT NULL,
    payment_method   VARCHAR(20),
    created_at       TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE TABLE sale_line_items (
    id           BIGSERIAL PRIMARY KEY,
    sale_id      BIGINT         NOT NULL REFERENCES sales (id) ON DELETE CASCADE,
    product_id   BIGINT         NOT NULL,
    product_name VARCHAR(200)   NOT NULL,
    sku          VARCHAR(100)   NOT NULL,
    quantity     INT            NOT NULL CHECK (quantity > 0),
    unit_price   NUMERIC(10, 2) NOT NULL,
    line_total   NUMERIC(10, 2) NOT NULL
);

-- Indexes for common queries
CREATE INDEX idx_sales_cashier    ON sales (cashier_username);
CREATE INDEX idx_sales_status     ON sales (status);
CREATE INDEX idx_sales_created_at ON sales (created_at DESC);
CREATE INDEX idx_line_items_sale  ON sale_line_items (sale_id);
