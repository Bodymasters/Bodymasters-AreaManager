import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# صلاحية تعطيل الموظف
disable_employee_permission = {
    "name": "تعطيل الموظف", 
    "code": "disable_employee"
}

# التحقق من وجود الصلاحية
cursor.execute("SELECT id FROM permission WHERE code = ?", (disable_employee_permission["code"],))
existing_perm = cursor.fetchone()

if not existing_perm:
    # إنشاء صلاحية جديدة
    cursor.execute(
        "INSERT INTO permission (name, code) VALUES (?, ?)",
        (disable_employee_permission["name"], disable_employee_permission["code"])
    )
    permission_id = cursor.lastrowid
    print(f"تمت إضافة صلاحية جديدة: {disable_employee_permission['name']} (ID: {permission_id})")
    
    # إضافة الصلاحية لدور المدير
    cursor.execute(
        "INSERT INTO role_permission (role, permission_id) VALUES (?, ?)",
        ("manager", permission_id)
    )
    print(f"تمت إضافة الصلاحية لدور المدير: {disable_employee_permission['name']}")
else:
    print(f"الصلاحية موجودة بالفعل: {disable_employee_permission['name']} (ID: {existing_perm[0]})")

# حفظ التغييرات
conn.commit()
print("تم حفظ جميع التغييرات بنجاح")

# إغلاق الاتصال
conn.close()
