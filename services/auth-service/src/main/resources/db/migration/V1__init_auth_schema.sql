-- Mini Prism Auth Service — Initial Schema

CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    email         VARCHAR(200) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'CASHIER',
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_username ON users (username);
CREATE INDEX idx_users_email    ON users (email);

-- Seed an initial admin account (password: Admin1234!)
-- In production, remove this and create via the API
INSERT INTO users (username, email, password_hash, role)
VALUES (
    'admin',
    'admin@prism.local',
    '$2b$12$7zxhTctY4Ly/etjD6b6XMuGAv4oJSTV1X3J8rCrvHJXVW0dNbAeKy',
    'ADMIN'
);
