import sqlite3

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# إنشاء جدول الصلاحيات
cursor.execute('''
CREATE TABLE IF NOT EXISTS permission (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    code TEXT NOT NULL UNIQUE
)
''')

# إنشاء جدول العلاقة بين المستخدمين والصلاحيات
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_permission (
    user_id INTEGER,
    permission_id INTEGER,
    PRIMARY KEY (user_id, permission_id),
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE
)
''')

# إنشاء جدول العلاقة بين الأدوار والصلاحيات
cursor.execute('''
CREATE TABLE IF NOT EXISTS role_permission (
    role TEXT,
    permission_id INTEGER,
    PRIMARY KEY (role, permission_id),
    FOREIGN KEY (permission_id) REFERENCES permission(id) ON DELETE CASCADE
)
''')

# إضافة الصلاحيات الأساسية
permissions = [
    # إدارة المستخدمين
    ('إدارة المستخدمين - عرض', 'عرض قائمة المستخدمين', 'view_users'),
    ('إدارة المستخدمين - إضافة', 'إضافة مستخدم جديد', 'add_user'),
    ('إدارة المستخدمين - تعديل', 'تعديل بيانات المستخدم', 'edit_user'),
    ('إدارة المستخدمين - حذف', 'حذف المستخدم', 'delete_user'),
    ('إدارة المستخدمين - صلاحيات', 'تعيين صلاحيات للمستخدم', 'manage_user_permissions'),
    
    # إدارة النوادي
    ('إدارة النوادي - عرض', 'عرض قائمة النوادي', 'view_clubs'),
    ('إدارة النوادي - إضافة', 'إضافة نادي جديد', 'add_club'),
    ('إدارة النوادي - تعديل', 'تعديل بيانات النادي', 'edit_club'),
    ('إدارة النوادي - حذف', 'حذف النادي', 'delete_club'),
    ('إدارة النوادي - مرافق', 'تعيين مرافق للنادي', 'manage_club_facilities'),
    
    # إدارة المرافق
    ('إدارة المرافق - عرض', 'عرض قائمة المرافق', 'view_facilities'),
    ('إدارة المرافق - إضافة', 'إضافة مرفق جديد', 'add_facility'),
    ('إدارة المرافق - تعديل', 'تعديل بيانات المرفق', 'edit_facility'),
    ('إدارة المرافق - حذف', 'حذف المرفق', 'delete_facility'),
    ('إدارة المرافق - بنود', 'إضافة بنود للمرفق', 'manage_facility_items'),
    
    # إدارة الموظفين
    ('إدارة الموظفين - عرض', 'عرض قائمة الموظفين', 'view_employees'),
    ('إدارة الموظفين - إضافة', 'إضافة موظف جديد', 'add_employee'),
    ('إدارة الموظفين - تعديل', 'تعديل بيانات الموظف', 'edit_employee'),
    ('إدارة الموظفين - حذف', 'حذف الموظف', 'delete_employee'),
    ('إدارة الموظفين - جدول', 'تعيين جدول للموظف', 'manage_employee_schedule'),
    
    # إدارة جداول الموظفين
    ('إدارة الجداول - عرض', 'عرض جداول الموظفين', 'view_schedules'),
    ('إدارة الجداول - إضافة', 'إضافة جدول جديد', 'add_schedule'),
    ('إدارة الجداول - تعديل', 'تعديل الجدول', 'edit_schedule'),
    ('إدارة الجداول - حذف', 'حذف الجدول', 'delete_schedule'),
    
    # إدارة التشيك
    ('إدارة التشيك - عرض', 'عرض قائمة التشيكات', 'view_checks'),
    ('إدارة التشيك - إضافة', 'إضافة تشيك جديد', 'add_check'),
    ('إدارة التشيك - تعديل', 'تعديل التشيك', 'edit_check'),
    ('إدارة التشيك - حذف', 'حذف التشيك', 'delete_check'),
    ('إدارة التشيك - تفاصيل', 'عرض تفاصيل التشيك', 'view_check_details'),
    
    # إدارة متابعة الكاميرات
    ('إدارة الكاميرات - عرض', 'عرض قائمة متابعة الكاميرات', 'view_camera_checks'),
    ('إدارة الكاميرات - إضافة', 'إضافة متابعة جديدة', 'add_camera_check'),
    ('إدارة الكاميرات - تعديل', 'تعديل المتابعة', 'edit_camera_check'),
    ('إدارة الكاميرات - حذف', 'حذف المتابعة', 'delete_camera_check'),
    ('إدارة الكاميرات - تفاصيل', 'عرض تفاصيل المتابعة', 'view_camera_check_details'),
    
    # إدارة الأعطال الحرجة
    ('إدارة الأعطال - عرض', 'عرض قائمة الأعطال الحرجة', 'view_critical_issues'),
    ('إدارة الأعطال - إضافة', 'إضافة عطل جديد', 'add_critical_issue'),
    ('إدارة الأعطال - تعديل', 'تعديل العطل', 'edit_critical_issue'),
    ('إدارة الأعطال - حذف', 'حذف العطل', 'delete_critical_issue'),
    ('إدارة الأعطال - إغلاق', 'إغلاق العطل', 'close_critical_issue'),
    ('إدارة الأعطال - تفاصيل', 'عرض تفاصيل العطل', 'view_critical_issue_details'),
    
    # إدارة المبيعات
    ('إدارة المبيعات - عرض', 'عرض قائمة المبيعات', 'view_sales'),
    ('إدارة المبيعات - إضافة تارجيت', 'إضافة تارجيت جديد', 'add_sales_target'),
    ('إدارة المبيعات - تعديل تارجيت', 'تعديل التارجيت', 'edit_sales_target'),
    ('إدارة المبيعات - حذف تارجيت', 'حذف التارجيت', 'delete_sales_target'),
    ('إدارة المبيعات - إضافة مبيعات', 'إضافة مبيعات يومية', 'add_daily_sales'),
    ('إدارة المبيعات - تفاصيل', 'عرض تفاصيل التارجيت', 'view_sales_details'),
    
    # الإجراءات النظامية (للتنفيذ لاحقًا)
    ('الإجراءات النظامية - عرض', 'عرض قائمة الإجراءات', 'view_procedures'),
    ('الإجراءات النظامية - إضافة', 'إضافة إجراء جديد', 'add_procedure'),
    ('الإجراءات النظامية - تعديل', 'تعديل الإجراء', 'edit_procedure'),
    ('الإجراءات النظامية - حذف', 'حذف الإجراء', 'delete_procedure'),
    ('الإجراءات النظامية - تفاصيل', 'عرض تفاصيل الإجراء', 'view_procedure_details'),
    
    # التقارير الشاملة (للتنفيذ لاحقًا)
    ('التقارير - عرض تقرير التشيك', 'عرض تقرير التشيك', 'view_check_report'),
    ('التقارير - عرض تقرير المرافق', 'عرض تقرير المرافق', 'view_facility_report'),
    ('التقارير - عرض تقرير المبيعات', 'عرض تقرير المبيعات', 'view_sales_report'),
    ('التقارير - طباعة', 'طباعة التقارير', 'print_reports'),
    ('التقارير - تصدير', 'تصدير التقارير', 'export_reports')
]

# إضافة الصلاحيات إلى الجدول
for permission in permissions:
    try:
        cursor.execute('INSERT INTO permission (name, description, code) VALUES (?, ?, ?)', permission)
    except sqlite3.IntegrityError:
        # تجاهل الخطأ إذا كانت الصلاحية موجودة بالفعل
        pass

# تعيين الصلاحيات الافتراضية للأدوار
role_permissions = {
    'admin': [code for _, _, code in permissions],  # المسؤول لديه جميع الصلاحيات
    'manager': [
        # صلاحيات عرض
        'view_users', 'view_clubs', 'view_facilities', 'view_employees', 'view_schedules',
        'view_checks', 'view_camera_checks', 'view_critical_issues', 'view_sales',
        'view_check_details', 'view_camera_check_details', 'view_critical_issue_details', 'view_sales_details',
        'view_check_report', 'view_facility_report', 'view_sales_report',
        
        # صلاحيات إدارة الموظفين والجداول
        'add_employee', 'edit_employee', 'delete_employee', 'manage_employee_schedule',
        'add_schedule', 'edit_schedule', 'delete_schedule',
        
        # صلاحيات إدارة التشيك والكاميرات والأعطال
        'add_check', 'edit_check', 'delete_check',
        'add_camera_check', 'edit_camera_check', 'delete_camera_check',
        'add_critical_issue', 'edit_critical_issue', 'delete_critical_issue', 'close_critical_issue',
        
        # صلاحيات إدارة المبيعات
        'add_sales_target', 'edit_sales_target', 'delete_sales_target', 'add_daily_sales',
        
        # صلاحيات التقارير
        'print_reports', 'export_reports'
    ],
    'supervisor': [
        # صلاحيات عرض
        'view_clubs', 'view_facilities', 'view_employees', 'view_schedules',
        'view_checks', 'view_camera_checks', 'view_critical_issues', 'view_sales',
        'view_check_details', 'view_camera_check_details', 'view_critical_issue_details', 'view_sales_details',
        
        # صلاحيات إدارة التشيك والكاميرات والأعطال
        'add_check', 'edit_check',
        'add_camera_check', 'edit_camera_check',
        'add_critical_issue', 'edit_critical_issue', 'close_critical_issue',
        
        # صلاحيات التقارير
        'print_reports'
    ],
    'user': [
        # صلاحيات عرض
        'view_clubs', 'view_facilities', 'view_employees', 'view_schedules',
        'view_checks', 'view_camera_checks', 'view_critical_issues', 'view_sales',
        'view_check_details', 'view_camera_check_details', 'view_critical_issue_details',
        
        # صلاحيات إدارة التشيك والكاميرات
        'add_check',
        'add_camera_check'
    ]
}

# إضافة الصلاحيات الافتراضية للأدوار
for role, permission_codes in role_permissions.items():
    # حذف الصلاحيات الحالية للدور
    cursor.execute('DELETE FROM role_permission WHERE role = ?', (role,))
    
    # إضافة الصلاحيات الجديدة للدور
    for code in permission_codes:
        cursor.execute('SELECT id FROM permission WHERE code = ?', (code,))
        permission_id = cursor.fetchone()
        if permission_id:
            try:
                cursor.execute('INSERT INTO role_permission (role, permission_id) VALUES (?, ?)', (role, permission_id[0]))
            except sqlite3.IntegrityError:
                # تجاهل الخطأ إذا كانت العلاقة موجودة بالفعل
                pass

# حفظ التغييرات
conn.commit()

# إغلاق الاتصال
conn.close()

print("تم إنشاء جداول الصلاحيات وإضافة الصلاحيات الأساسية بنجاح!")
