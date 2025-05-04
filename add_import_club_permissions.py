import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# تعريف الصلاحيات الجديدة
import_club_permissions = [
    {
        "name": "استيراد النوادي من إكسل",
        "code": "import_clubs_excel",
        "description": "صلاحية استيراد النوادي من ملف إكسل"
    }
]

# إضافة الصلاحيات الجديدة
for perm_data in import_club_permissions:
    # التحقق من وجود الصلاحية
    cursor.execute("SELECT id FROM permission WHERE code = ?", (perm_data["code"],))
    existing_perm = cursor.fetchone()
    
    if not existing_perm:
        # إنشاء صلاحية جديدة
        cursor.execute(
            "INSERT INTO permission (name, code, description) VALUES (?, ?, ?)",
            (perm_data["name"], perm_data["code"], perm_data["description"])
        )
        permission_id = cursor.lastrowid
        print(f"تمت إضافة صلاحية جديدة: {perm_data['name']} (ID: {permission_id})")
        
        # إضافة الصلاحية لدور المدير
        cursor.execute(
            "INSERT INTO role_permission (role, permission_id) VALUES (?, ?)",
            ("manager", permission_id)
        )
        print(f"تمت إضافة الصلاحية لدور المدير: {perm_data['name']}")
    else:
        print(f"الصلاحية موجودة بالفعل: {perm_data['name']} (ID: {existing_perm[0]})")

# حفظ التغييرات
conn.commit()
print("تم حفظ جميع التغييرات بنجاح")

# إغلاق الاتصال
conn.close()
