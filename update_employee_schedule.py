import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود الأعمدة الجديدة
cursor.execute("PRAGMA table_info(employee_schedule)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# إضافة عمود shift_type إذا لم يكن موجوداً
if 'shift_type' not in column_names:
    cursor.execute("ALTER TABLE employee_schedule ADD COLUMN shift_type TEXT DEFAULT 'one_shift'")
    print("تم إضافة عمود shift_type بنجاح")

# إضافة عمود work_hours إذا لم يكن موجوداً
if 'work_hours' not in column_names:
    cursor.execute("ALTER TABLE employee_schedule ADD COLUMN work_hours INTEGER DEFAULT 8")
    print("تم إضافة عمود work_hours بنجاح")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم تحديث جدول employee_schedule بنجاح!")
