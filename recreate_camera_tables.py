import sqlite3
import os

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# تفعيل دعم Foreign Keys
cursor.execute("PRAGMA foreign_keys = ON")

# حذف الجداول الحالية
print("جاري حذف الجداول الحالية...")
cursor.execute("DROP TABLE IF EXISTS camera_time_slot")
cursor.execute("DROP TABLE IF EXISTS camera_check")

# إنشاء جدول camera_check
print("جاري إنشاء جدول camera_check...")
cursor.execute("""
CREATE TABLE camera_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    notes TEXT,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")

# إنشاء جدول camera_time_slot
print("جاري إنشاء جدول camera_time_slot...")
cursor.execute("""
CREATE TABLE camera_time_slot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_check_id INTEGER NOT NULL,
    time_slot VARCHAR(10) NOT NULL,
    is_working BOOLEAN DEFAULT 0,
    FOREIGN KEY (camera_check_id) REFERENCES camera_check (id) ON DELETE CASCADE
)
""")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم إعادة إنشاء الجداول بنجاح!")
