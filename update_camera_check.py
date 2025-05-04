import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود العمود
cursor.execute("PRAGMA table_info(camera_check)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# إضافة العمود إذا لم يكن موجوداً
if 'violations_count' not in column_names:
    print("إضافة عمود 'violations_count' إلى جدول 'camera_check'...")
    cursor.execute("ALTER TABLE camera_check ADD COLUMN violations_count TEXT")
    conn.commit()
    print("تم إضافة العمود بنجاح!")
else:
    print("العمود 'violations_count' موجود بالفعل في جدول 'camera_check'")

# إغلاق الاتصال
conn.close()
