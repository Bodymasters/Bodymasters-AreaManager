import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# صلاحية استيراد بنود المرفق من الإكسل
facility_items_import_permission = {
    "name": "استيراد بنود المرافق من الإكسل", 
    "code": "import_facility_items_excel"
}

# التحقق من وجود الصلاحية
cursor.execute("SELECT id FROM permission WHERE code = ?", (facility_items_import_permission["code"],))
existing_perm = cursor.fetchone()

if not existing_perm:
    # إنشاء صلاحية جديدة
    cursor.execute(
        "INSERT INTO permission (name, code) VALUES (?, ?)",
        (facility_items_import_permission["name"], facility_items_import_permission["code"])
    )
    permission_id = cursor.lastrowid
    print(f"تمت إضافة صلاحية جديدة: {facility_items_import_permission['name']} (ID: {permission_id})")
    
    # إضافة الصلاحية لدور المدير
    cursor.execute(
        "INSERT INTO role_permission (role, permission_id) VALUES (?, ?)",
        ("manager", permission_id)
    )
    print(f"تمت إضافة الصلاحية لدور المدير: {facility_items_import_permission['name']}")
else:
    print(f"الصلاحية موجودة بالفعل: {facility_items_import_permission['name']} (ID: {existing_perm[0]})")

# حفظ التغييرات
conn.commit()
print("تم حفظ جميع التغييرات بنجاح")

# إغلاق الاتصال
conn.close()
