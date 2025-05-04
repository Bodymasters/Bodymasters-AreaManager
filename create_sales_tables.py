import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# إنشاء جدول sales_target
cursor.execute('''
CREATE TABLE IF NOT EXISTS sales_target (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    month VARCHAR(7) NOT NULL,
    target_amount FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (club_id) REFERENCES club (id)
)
''')

# إنشاء جدول daily_sales
cursor.execute('''
CREATE TABLE IF NOT EXISTS daily_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    amount FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (target_id) REFERENCES sales_target (id)
)
''')

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم إنشاء جداول المبيعات بنجاح!")
