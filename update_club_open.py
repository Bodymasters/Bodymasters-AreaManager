import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود عمود club_open في جدول camera_check
cursor.execute("PRAGMA table_info(camera_check)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'club_open' not in column_names:
    # إضافة عمود club_open إلى جدول camera_check
    cursor.execute("ALTER TABLE camera_check ADD COLUMN club_open BOOLEAN DEFAULT 0")
    print("تم إضافة عمود club_open إلى جدول camera_check")
else:
    print("عمود club_open موجود بالفعل في جدول camera_check")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم تحديث قاعدة البيانات بنجاح!")
