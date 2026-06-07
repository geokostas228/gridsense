CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tariffs (
    tariff_id SERIAL PRIMARY KEY,
    tariff_name TEXT NOT NULL,
    price_per_kwh NUMERIC(10,4) NOT NULL
);

CREATE TABLE billing_accounts (
    account_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    tariff_id INTEGER REFERENCES tariffs(tariff_id),
    meter_id TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES billing_accounts(account_id),
    billing_period_start DATE,
    billing_period_end DATE,
    total_kwh NUMERIC(12,2),
    amount_due NUMERIC(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id),
    amount NUMERIC(12,2),
    payment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);