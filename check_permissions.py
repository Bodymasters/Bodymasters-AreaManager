import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# البحث عن صلاحيات الاستيراد
print("=== صلاحيات الاستيراد ===")
cursor.execute("SELECT id, name, code FROM permission WHERE code LIKE '%import%' OR name LIKE '%استيراد%' ORDER BY id")
import_permissions = cursor.fetchall()
for permission in import_permissions:
    print(f"ID: {permission[0]}, الاسم: {permission[1]}, الكود: {permission[2]}")

# التحقق من صلاحيات دور المدير
print("\n=== صلاحيات الاستيراد لدور المدير ===")
cursor.execute("""
    SELECT p.id, p.name, p.code
    FROM permission p
    JOIN role_permission rp ON p.id = rp.permission_id
    WHERE (p.code LIKE '%import%' OR p.name LIKE '%استيراد%') AND rp.role = 'manager'
    ORDER BY p.id
""")
manager_import_permissions = cursor.fetchall()
for permission in manager_import_permissions:
    print(f"ID: {permission[0]}, الاسم: {permission[1]}, الكود: {permission[2]}")

# إغلاق الاتصال
conn.close()
