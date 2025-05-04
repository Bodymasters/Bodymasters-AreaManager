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

# التحقق من إنشاء الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camera_check'")
camera_check_exists = cursor.fetchone()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camera_time_slot'")
camera_time_slot_exists = cursor.fetchone()

if camera_check_exists and camera_time_slot_exists:
    print("تم إنشاء الجداول بنجاح!")
else:
    print("حدث خطأ أثناء إنشاء الجداول!")

# عرض هيكل جدول camera_check
cursor.execute("PRAGMA table_info(camera_check)")
columns = cursor.fetchall()
print("\nهيكل جدول camera_check:")
for column in columns:
    print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# عرض هيكل جدول camera_time_slot
cursor.execute("PRAGMA table_info(camera_time_slot)")
columns = cursor.fetchall()
print("\nهيكل جدول camera_time_slot:")
for column in columns:
    print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("\nتم إعادة إنشاء الجداول بنجاح!")
