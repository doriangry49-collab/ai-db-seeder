CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE support_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    priority VARCHAR(20) NOT NULL,       -- 'low', 'medium', 'high', 'urgent'
    resolution_status VARCHAR(20) NOT NULL, -- 'open', 'resolved', 'escalated'
    resolved_at TIMESTAMP NULL,
    escalation_note VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);
