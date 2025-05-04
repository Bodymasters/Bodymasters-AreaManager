import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# الحصول على قائمة المتابعات
cursor.execute("SELECT id, check_date, club_id, user_id, status, notes FROM camera_check")
checks = cursor.fetchall()

print("المتابعات الموجودة في قاعدة البيانات:")
for check in checks:
    print(f"- المتابعة رقم {check[0]} لنادي {check[2]} بتاريخ {check[1]}")

# إغلاق الاتصال
conn.close()
