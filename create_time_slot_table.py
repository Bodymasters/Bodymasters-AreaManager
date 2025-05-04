import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود جدول camera_time_slot
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='camera_time_slot'")
table_exists = cursor.fetchone()

if not table_exists:
    # إنشاء جدول camera_time_slot
    cursor.execute("""
    CREATE TABLE camera_time_slot (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        camera_check_id INTEGER NOT NULL,
        time_slot VARCHAR(10) NOT NULL,
        is_working BOOLEAN DEFAULT 0,
        FOREIGN KEY (camera_check_id) REFERENCES camera_check (id) ON DELETE CASCADE
    )
    """)
    print("تم إنشاء جدول camera_time_slot بنجاح!")
else:
    print("جدول camera_time_slot موجود بالفعل.")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم الانتهاء من العملية بنجاح!")
