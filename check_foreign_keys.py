import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من تفعيل دعم Foreign Keys
cursor.execute("PRAGMA foreign_keys = ON")
cursor.execute("PRAGMA foreign_keys")
foreign_keys_enabled = cursor.fetchone()[0]
print(f"دعم Foreign Keys: {'مفعل' if foreign_keys_enabled else 'غير مفعل'}")

# عرض قيود Foreign Key لجدول camera_time_slot
cursor.execute("PRAGMA foreign_key_list(camera_time_slot)")
foreign_keys = cursor.fetchall()

print("قيود Foreign Key لجدول camera_time_slot:")
for fk in foreign_keys:
    print(f"- {fk}")

# إغلاق الاتصال
conn.close()
