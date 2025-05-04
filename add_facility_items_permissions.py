import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# قائمة بصلاحيات بنود المرفق الجديدة
facility_items_permissions = [
    {"name": "تعديل بند المرفق", "code": "edit_facility_item"},
    {"name": "حذف بند المرفق", "code": "delete_facility_item"},
    {"name": "تفعيل/تعطيل بند المرفق", "code": "toggle_facility_item"}
]

# إضافة الصلاحيات الجديدة
for perm_data in facility_items_permissions:
    # التحقق من وجود الصلاحية
    cursor.execute("SELECT id FROM permission WHERE code = ?", (perm_data["code"],))
    existing_perm = cursor.fetchone()
    
    if not existing_perm:
        # إنشاء صلاحية جديدة
        cursor.execute(
            "INSERT INTO permission (name, code) VALUES (?, ?)",
            (perm_data["name"], perm_data["code"])
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
