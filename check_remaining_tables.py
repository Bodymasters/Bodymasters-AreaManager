import sqlite3

# الاتصال بقاعدة البيانات المحلية
sqlite_conn = sqlite3.connect('app.db')
cursor = sqlite_conn.cursor()

# استعلام لاستخراج أسماء جميع الجداول
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [table[0] for table in cursor.fetchall()]

# قائمة الجداول التي تم نقلها بنجاح
migrated_tables = [
    'user_clubs', 'employee', 'camera_check', 'critical_issue', 'shumoos',
    'facility', 'camera_time_slot', 'club_facilities', 'facility_item',
    'club_facility_item', 'sales_target', 'daily_sales', 'violation_type',
    'violation', 'role_permission', 'user_permission', 'permission',
    'employee_schedule'
]

# استبعاد الجداول التي تم نقلها بالفعل
remaining_tables = [table for table in tables if table not in migrated_tables]

print("الجداول المتبقية التي لم يتم نقلها بعد:")
for table in remaining_tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} سجل")
    except Exception as e:
        print(f"  {table}: حدث خطأ أثناء عد السجلات: {e}")

# إغلاق الاتصال
cursor.close()
sqlite_conn.close()