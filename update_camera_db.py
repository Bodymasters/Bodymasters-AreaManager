import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود عمود violations_count في جدول camera_check
cursor.execute("PRAGMA table_info(camera_check)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'violations_count' not in column_names:
    # إضافة عمود violations_count إلى جدول camera_check
    cursor.execute("ALTER TABLE camera_check ADD COLUMN violations_count INTEGER DEFAULT 0")
    print("تم إضافة عمود violations_count إلى جدول camera_check")
else:
    print("عمود violations_count موجود بالفعل في جدول camera_check")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم تحديث قاعدة البيانات بنجاح!")
