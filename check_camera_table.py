import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# عرض هيكل جدول camera_check
cursor.execute("PRAGMA table_info(camera_check)")
columns = cursor.fetchall()

print("هيكل جدول camera_check:")
for column in columns:
    print(f"- {column[1]} ({column[2]})")

# إغلاق الاتصال
conn.close()
