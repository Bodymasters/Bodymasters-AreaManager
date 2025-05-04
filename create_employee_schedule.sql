-- إنشاء جدول جدول دوام الموظف
CREATE TABLE IF NOT EXISTS employee_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    shift1_start TEXT,
    shift1_end TEXT,
    shift2_start TEXT,
    shift2_end TEXT,
    mobile_number TEXT,
    work_days TEXT,
    off_days TEXT,
    allocation_from TEXT,
    allocation_to TEXT,
    allocation_day TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employee (id),
    FOREIGN KEY (club_id) REFERENCES club (id)
);
