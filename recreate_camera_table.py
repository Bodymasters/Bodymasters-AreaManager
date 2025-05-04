import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# حفظ البيانات الموجودة
cursor.execute("SELECT id, check_date, club_id, user_id, status, notes, club_open FROM camera_check")
existing_data = cursor.fetchall()
print(f"تم العثور على {len(existing_data)} سجل في الجدول الحالي")

# حذف الجداول المرتبطة أولاً
cursor.execute("DROP TABLE IF EXISTS camera_time_slot")
print("تم حذف جدول camera_time_slot")

# حذف الجدول الحالي
cursor.execute("DROP TABLE IF EXISTS camera_check")
print("تم حذف جدول camera_check")

# إنشاء جدول جديد بالهيكل الصحيح
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

# إعادة إنشاء جدول camera_time_slot
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

# إعادة إدخال البيانات القديمة
for record in existing_data:
    # إضافة قيمة افتراضية لعمود violations_count
    record_with_violations = record + (0,)  # إضافة 0 كقيمة افتراضية لعمود violations_count
    cursor.execute("""
    INSERT INTO camera_check (id, check_date, club_id, user_id, status, notes, club_open, violations_count)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, record_with_violations)

print(f"تم إعادة إدخال {len(existing_data)} سجل في الجدول الجديد")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم إعادة إنشاء جداول متابعة الكاميرات بنجاح!")
