CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name VARCHAR(100) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    industry VARCHAR(50) NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    email VARCHAR(100) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    plan_name VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'active', 'canceled'
    monthly_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    canceled_at TIMESTAMP NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL,
    invoice_number VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'paid', 'unpaid'
    amount DECIMAL(10, 2) NOT NULL,
    due_date TIMESTAMP NOT NULL,
    paid_at TIMESTAMP NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);
