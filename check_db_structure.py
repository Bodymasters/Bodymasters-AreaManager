import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# عرض قائمة الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("قائمة الجداول في قاعدة البيانات:")
for table in tables:
    print(f"- {table[0]}")

# عرض هيكل جدول check_item
cursor.execute("PRAGMA table_info(check_item)")
columns = cursor.fetchall()
print("\nهيكل جدول check_item:")
for column in columns:
    print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# إغلاق الاتصال
conn.close()
