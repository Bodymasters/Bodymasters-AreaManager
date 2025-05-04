import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# عرض هيكل جدول check_item
cursor.execute("PRAGMA table_info(check_item)")
columns = cursor.fetchall()

print("هيكل جدول check_item:")
for column in columns:
    print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# إضافة عمود facility_id إذا لم يكن موجودًا
cursor.execute("SELECT name FROM pragma_table_info('check_item') WHERE name = 'facility_id'")
if not cursor.fetchone():
    print("\nإضافة عمود facility_id إلى جدول check_item...")
    cursor.execute("ALTER TABLE check_item ADD COLUMN facility_id INTEGER REFERENCES facility(id)")
    conn.commit()
    print("تمت إضافة العمود بنجاح!")

    # عرض هيكل الجدول بعد التعديل
    cursor.execute("PRAGMA table_info(check_item)")
    columns = cursor.fetchall()
    print("\nهيكل جدول check_item بعد التعديل:")
    for column in columns:
        print(f"- {column[1]} ({column[2]}) {'NOT NULL' if column[3] else 'NULL'}")

# إغلاق الاتصال
conn.close()
