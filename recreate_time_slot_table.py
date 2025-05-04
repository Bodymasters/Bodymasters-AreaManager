import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# تفعيل دعم Foreign Keys
cursor.execute("PRAGMA foreign_keys = ON")

# حذف الجدول الحالي
print("جاري حذف جدول camera_time_slot الحالي...")
cursor.execute("DROP TABLE IF EXISTS camera_time_slot")

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

# التحقق من إنشاء الجدول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camera_time_slot'")
table_exists = cursor.fetchone()

if table_exists:
    print("تم إنشاء جدول camera_time_slot بنجاح!")
else:
    print("حدث خطأ أثناء إنشاء جدول camera_time_slot!")

# عرض هيكل الجدول
cursor.execute("PRAGMA table_info(camera_time_slot)")
columns = cursor.fetchall()
print("\nهيكل جدول camera_time_slot:")
for column in columns:
    print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("\nتم إعادة إنشاء جدول camera_time_slot بنجاح!")
