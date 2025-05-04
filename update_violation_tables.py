import sqlite3

# الاتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود جدول violation_type
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='violation_type'")
if not cursor.fetchone():
    print("إنشاء جدول violation_type...")
    cursor.execute("""
    CREATE TABLE violation_type (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        is_imported BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("تم إنشاء جدول violation_type بنجاح!")
else:
    print("جدول violation_type موجود بالفعل.")

# التحقق من وجود جدول violation
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='violation'")
if not cursor.fetchone():
    print("إنشاء جدول violation...")
    cursor.execute("""
    CREATE TABLE violation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        violation_type_id INTEGER NOT NULL,
        violation_number INTEGER NOT NULL,
        violation_date DATE NOT NULL,
        violation_source VARCHAR(50) NOT NULL,
        is_signed BOOLEAN DEFAULT 0,
        image_path VARCHAR(255),
        notes TEXT,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employee (id),
        FOREIGN KEY (violation_type_id) REFERENCES violation_type (id),
        FOREIGN KEY (created_by) REFERENCES user (id)
    )
    """)
    print("تم إنشاء جدول violation بنجاح!")
else:
    print("جدول violation موجود بالفعل.")

# إضافة بعض أنواع المخالفات الافتراضية
default_violation_types = [
    ('التأخر عن الدوام', 'التأخر عن موعد بدء الدوام لمدة تزيد عن 15 دقيقة', 1, 0),
    ('الغياب بدون إذن', 'الغياب عن العمل بدون إذن مسبق أو عذر مقبول', 1, 0),
    ('عدم الالتزام بالزي الرسمي', 'عدم ارتداء الزي الرسمي المخصص للعمل', 1, 0)
]

# التحقق من وجود أنواع المخالفات
cursor.execute("SELECT COUNT(*) FROM violation_type")
count = cursor.fetchone()[0]
if count == 0:
    print("إضافة أنواع المخالفات الافتراضية...")
    for vt in default_violation_types:
        cursor.execute("""
        INSERT INTO violation_type (name, description, is_active, is_imported)
        VALUES (?, ?, ?, ?)
        """, vt)
    print(f"تم إضافة {len(default_violation_types)} نوع مخالفة افتراضي بنجاح!")
else:
    print(f"يوجد بالفعل {count} نوع مخالفة في قاعدة البيانات.")

# إضافة صلاحيات المخالفات
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='permission'")
if cursor.fetchone():
    # التحقق من وجود صلاحيات المخالفات
    cursor.execute("SELECT COUNT(*) FROM permission WHERE code IN ('add_violation', 'edit_violation', 'import_violation_types')")
    perm_count = cursor.fetchone()[0]
    
    if perm_count < 3:
        print("إضافة صلاحيات المخالفات...")
        permissions = [
            ('إضافة مخالفة', 'add_violation', 'صلاحية إضافة مخالفة جديدة'),
            ('تعديل مخالفة', 'edit_violation', 'صلاحية تعديل المخالفات'),
            ('استيراد أنواع المخالفات', 'import_violation_types', 'صلاحية استيراد أنواع المخالفات من ملف إكسل')
        ]
        
        for perm in permissions:
            # التحقق من وجود الصلاحية
            cursor.execute("SELECT id FROM permission WHERE code = ?", (perm[1],))
            if not cursor.fetchone():
                cursor.execute("""
                INSERT INTO permission (name, code, description)
                VALUES (?, ?, ?)
                """, perm)
                print(f"تم إضافة صلاحية: {perm[0]}")
    else:
        print("صلاحيات المخالفات موجودة بالفعل.")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم تحديث قاعدة البيانات بنجاح!")
