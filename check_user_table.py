import sqlite3

# اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# الحصول على معلومات عن جدول المستخدمين
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()

print("أعمدة جدول المستخدمين:")
for column in columns:
    print(f"- {column[1]} ({column[2]})")

# إغلاق الاتصال
conn.close()
