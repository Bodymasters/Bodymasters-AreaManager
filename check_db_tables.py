import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# الحصول على قائمة الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("الجداول الموجودة في قاعدة البيانات:")
for table in tables:
    print(f"- {table[0]}")

# إغلاق الاتصال
conn.close()
