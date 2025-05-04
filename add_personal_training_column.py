import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود العمود
cursor.execute("PRAGMA table_info(sales_target)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'personal_training_sales' not in column_names:
    # إضافة العمود personal_training_sales إلى جدول sales_target
    cursor.execute("ALTER TABLE sales_target ADD COLUMN personal_training_sales FLOAT DEFAULT 0")
    print("تم إضافة عمود 'personal_training_sales' إلى جدول 'sales_target'")
else:
    print("العمود 'personal_training_sales' موجود بالفعل في جدول 'sales_target'")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تمت عملية التحديث بنجاح")
