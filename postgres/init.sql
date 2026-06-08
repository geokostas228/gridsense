CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tariffs (
    tariff_id SERIAL PRIMARY KEY,
    tariff_name TEXT NOT NULL,
    price_per_kwh NUMERIC(10,4) NOT NULL
);

CREATE TABLE IF NOT EXISTS billing_accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    tariff_id INTEGER REFERENCES tariffs(tariff_id),
    meter_id TEXT NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES billing_accounts(account_id),
    billing_period_start DATE,
    billing_period_end DATE,
    total_kwh NUMERIC(12,2),
    amount_due NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id),
    amount NUMERIC(12,2),
    payment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO tariffs (tariff_name, price_per_kwh)
VALUES
    ('Residential Standard', 0.1800),
    ('Commercial Standard', 0.2400),
    ('Time of Use Peak', 0.3100)
ON CONFLICT DO NOTHING;

INSERT INTO customers (full_name, email, address)
VALUES
    ('Maria Papadopoulou', 'maria@example.com', 'Volos, Greece'),
    ('Nikos Ioannou', 'nikos@example.com', 'Larissa, Greece')
ON CONFLICT (email) DO NOTHING;

INSERT INTO billing_accounts (customer_id, tariff_id, meter_id)
SELECT c.customer_id, t.tariff_id, 'MTR-1001'
FROM customers c, tariffs t
WHERE c.email = 'maria@example.com'
AND t.tariff_name = 'Residential Standard'
ON CONFLICT (meter_id) DO NOTHING;