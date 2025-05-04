import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود العمود
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# إضافة العمود إذا لم يكن موجوداً
if 'role' not in column_names:
    print("إضافة عمود 'role' إلى جدول 'user'...")
    cursor.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user'")
    conn.commit()
    print("تم إضافة العمود بنجاح!")
else:
    print("العمود 'role' موجود بالفعل في جدول 'user'")

# تحديث قيم العمود الجديد بناءً على قيمة is_admin
cursor.execute("UPDATE user SET role = 'admin' WHERE is_admin = 1")
cursor.execute("UPDATE user SET role = 'user' WHERE is_admin = 0")
conn.commit()
print("تم تحديث قيم العمود 'role' بنجاح!")

# إغلاق الاتصال
conn.close()
