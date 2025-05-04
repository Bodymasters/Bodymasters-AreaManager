import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود جدول role_permission
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='role_permission'")
table_exists = cursor.fetchone()

if not table_exists:
    # إنشاء جدول role_permission إذا لم يكن موجوداً
    cursor.execute('''
    CREATE TABLE role_permission (
        role TEXT,
        permission_id INTEGER,
        PRIMARY KEY (role, permission_id),
        FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE
    )
    ''')
    print("تم إنشاء جدول role_permission بنجاح!")
else:
    print("جدول role_permission موجود بالفعل.")

# إغلاق الاتصال
conn.close()
