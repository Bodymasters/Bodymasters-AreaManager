import sqlite3
import os

# حذف قاعدة البيانات الحالية
db_path = 'app.db'
if os.path.exists(db_path):
    # نسخ قاعدة البيانات احتياطياً
    backup_path = 'app.db.bak'
    if os.path.exists(backup_path):
        os.remove(backup_path)
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"تم نسخ قاعدة البيانات احتياطياً إلى: {backup_path}")

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# حفظ بيانات جدول camera_check الحالي
cursor.execute("SELECT id, check_date, club_id, user_id, status, notes, club_open FROM camera_check")
camera_checks = cursor.fetchall()
print(f"تم العثور على {len(camera_checks)} سجل في جدول camera_check")

# حفظ بيانات جدول camera_time_slot الحالي
cursor.execute("SELECT id, camera_check_id, time_slot, is_working FROM camera_time_slot")
time_slots = cursor.fetchall()
print(f"تم العثور على {len(time_slots)} سجل في جدول camera_time_slot")

# حذف الجداول
cursor.execute("DROP TABLE IF EXISTS camera_time_slot")
cursor.execute("DROP TABLE IF EXISTS camera_check")
print("تم حذف الجداول القديمة")

# إنشاء جدول camera_check الجديد
cursor.execute("""
CREATE TABLE camera_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20),
    notes TEXT,
    violations_count INTEGER DEFAULT 0,
    club_open BOOLEAN DEFAULT 0,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")
print("تم إنشاء جدول camera_check الجديد")

# إنشاء جدول camera_time_slot الجديد
cursor.execute("""
CREATE TABLE camera_time_slot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_check_id INTEGER NOT NULL,
    time_slot VARCHAR(10) NOT NULL,
    is_working BOOLEAN DEFAULT 0,
    FOREIGN KEY (camera_check_id) REFERENCES camera_check (id) ON DELETE CASCADE
)
""")
print("تم إنشاء جدول camera_time_slot الجديد")

# إعادة إدخال بيانات camera_check
for check in camera_checks:
    cursor.execute("""
    INSERT INTO camera_check (id, check_date, club_id, user_id, status, notes, club_open, violations_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (check[0], check[1], check[2], check[3], check[4], check[5], check[6]))
print(f"تم إعادة إدخال {len(camera_checks)} سجل في جدول camera_check")

# إعادة إدخال بيانات camera_time_slot
for slot in time_slots:
    cursor.execute("""
    INSERT INTO camera_time_slot (id, camera_check_id, time_slot, is_working)
    VALUES (?, ?, ?, ?)
    """, slot)
print(f"تم إعادة إدخال {len(time_slots)} سجل في جدول camera_time_slot")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم إصلاح جداول متابعة الكاميرات بنجاح!")
