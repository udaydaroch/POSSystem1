-- Mini Prism Inventory Service — Initial Schema

CREATE TABLE products (
    id                   BIGSERIAL PRIMARY KEY,
    name                 VARCHAR(200)   NOT NULL,
    description          VARCHAR(1000),
    sku                  VARCHAR(100)   NOT NULL UNIQUE,
    price                NUMERIC(10, 2) NOT NULL,
    stock_level          INT            NOT NULL DEFAULT 0,
    low_stock_threshold  INT            NOT NULL DEFAULT 5,
    category             VARCHAR(50)    NOT NULL,
    active               BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP      NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_sku      ON products (sku);
CREATE INDEX idx_products_category ON products (category);
CREATE INDEX idx_products_active   ON products (active);

-- Seed some realistic NZ electronics retail products
INSERT INTO products (name, description, sku, price, stock_level, category) VALUES
  ('Samsung 65" QLED TV',       '4K Smart TV with Quantum Dot display', 'SAM-TV-65Q', 1999.00, 12, 'TV_AUDIO'),
  ('Apple iPhone 15 128GB',     'Latest iPhone with A16 chip',          'APL-IP15-128', 1499.00, 8, 'PHONES'),
  ('Sony WH-1000XM5 Headphones','Industry-leading noise cancellation',  'SNY-WH1000XM5', 499.00, 20, 'TV_AUDIO'),
  ('LG 27" 4K Monitor',         'UHD IPS display for professionals',    'LG-MON-27-4K', 699.00, 15, 'COMPUTERS'),
  ('Dyson V15 Detect Vacuum',   'Laser dust detection vacuum cleaner',  'DYS-V15-DET', 1099.00, 6, 'APPLIANCES'),
  ('Nintendo Switch OLED',      'Portable gaming console with OLED',    'NIN-SW-OLED', 549.00, 3, 'GAMING'),
  ('Logitech MX Master 3S',     'Advanced wireless mouse',              'LOG-MXM3S', 149.00, 25, 'ACCESSORIES'),
  ('MacBook Air M3 13"',        '13-inch MacBook Air with M3 chip',     'APL-MBA-M3-13', 2199.00, 5, 'COMPUTERS');
