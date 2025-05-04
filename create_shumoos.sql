-- إنشاء جدول شموس
CREATE TABLE IF NOT EXISTS shumoos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    registered_count INTEGER NOT NULL,
    registration_date DATE NOT NULL,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (created_by) REFERENCES user (id)
);
