import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# الحصول على عدد التشيكات
cursor.execute("SELECT COUNT(*) FROM 'check'")
check_count = cursor.fetchone()[0]
print(f"عدد التشيكات: {check_count}")

# الحصول على عدد الأندية
cursor.execute("SELECT COUNT(*) FROM club")
club_count = cursor.fetchone()[0]
print(f"عدد الأندية: {club_count}")

# الحصول على عدد المرافق
cursor.execute("SELECT COUNT(*) FROM facility")
facility_count = cursor.fetchone()[0]
print(f"عدد المرافق: {facility_count}")

# الحصول على عدد بنود المرافق
cursor.execute("SELECT COUNT(*) FROM facility_item")
facility_item_count = cursor.fetchone()[0]
print(f"عدد بنود المرافق: {facility_item_count}")

# الحصول على عدد بنود التشيك
cursor.execute("SELECT COUNT(*) FROM check_item")
check_item_count = cursor.fetchone()[0]
print(f"عدد بنود التشيك: {check_item_count}")

# الحصول على قائمة التشيكات
print("\nقائمة التشيكات:")
cursor.execute("SELECT c.id, c.check_date, cl.name FROM 'check' c JOIN club cl ON c.club_id = cl.id")
checks = cursor.fetchall()
for check in checks:
    print(f"- {check[0]}: نادي {check[2]} - تاريخ {check[1]}")

# إغلاق الاتصال
conn.close()
