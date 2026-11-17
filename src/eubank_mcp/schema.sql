CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    full_name   TEXT NOT NULL,
    name_search TEXT NOT NULL,
    nif         TEXT NOT NULL UNIQUE,
    birth_date  TEXT NOT NULL,
    address     TEXT NOT NULL,
    country     TEXT NOT NULL,
    iban        TEXT NOT NULL UNIQUE
);

CREATE INDEX idx_customers_name_search ON customers (name_search);

CREATE TABLE credit (
    customer_id           TEXT PRIMARY KEY REFERENCES customers (customer_id),
    credit_score          INTEGER NOT NULL,
    preapproved_limit_eur INTEGER NOT NULL,
    updated_at            TEXT NOT NULL
);

CREATE TABLE risk (
    customer_id  TEXT PRIMARY KEY REFERENCES customers (customer_id),
    risk_profile TEXT NOT NULL CHECK (risk_profile IN ('low', 'medium', 'high')),
    kyc_status   TEXT NOT NULL CHECK (kyc_status IN ('verified', 'pending', 'expired')),
    is_pep       INTEGER NOT NULL CHECK (is_pep IN (0, 1))
);

-- Present for realism. No tool reads this table.
CREATE TABLE aml_alerts (
    alert_id    INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (customer_id),
    alert_type  TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE service_notes (
    note_id     INTEGER PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (customer_id),
    created_at  TEXT NOT NULL,
    author      TEXT NOT NULL,
    body        TEXT NOT NULL
);
