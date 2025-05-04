import sqlite3

# الاتصال بقاعدة البيانات المحلية
sqlite_conn = sqlite3.connect('app.db')
cursor = sqlite_conn.cursor()

# استعلام لاستخراج أسماء جميع الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# عرض أسماء الجداول
print("الجداول الموجودة في قاعدة البيانات:")
for table in tables:
    print(table[0])

# إغلاق الاتصال
cursor.close()
sqlite_conn.close()