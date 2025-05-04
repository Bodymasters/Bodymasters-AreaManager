import os
import sqlite3

# حذف قاعدة البيانات الحالية
db_path = 'app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"تم حذف قاعدة البيانات الحالية: {db_path}")

# إنشاء قاعدة بيانات جديدة
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# إنشاء جداول قاعدة البيانات
print("جاري إنشاء جداول قاعدة البيانات...")

# جدول المستخدمين
cursor.execute("""
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) NOT NULL,
    password VARCHAR(128) NOT NULL,
    is_admin BOOLEAN DEFAULT 0
)
""")
print("تم إنشاء جدول user")

# جدول النوادي
cursor.execute("""
CREATE TABLE club (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    manager_name VARCHAR(100),
    phone VARCHAR(20)
)
""")
print("تم إنشاء جدول club")

# جدول المرافق
cursor.execute("""
CREATE TABLE facility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    is_imported BOOLEAN DEFAULT 0
)
""")
print("تم إنشاء جدول facility")

# جدول بنود المرافق
cursor.execute("""
CREATE TABLE facility_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    facility_id INTEGER NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facility (id)
)
""")
print("تم إنشاء جدول facility_item")

# جدول الموظفين
cursor.execute("""
CREATE TABLE employee (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(120),
    hire_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    FOREIGN KEY (club_id) REFERENCES club (id)
)
""")
print("تم إنشاء جدول employee")

# جدول العلاقة بين النوادي والمرافق
cursor.execute("""
CREATE TABLE club_facility (
    club_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    PRIMARY KEY (club_id, facility_id),
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (facility_id) REFERENCES facility (id)
)
""")
print("تم إنشاء جدول club_facility")

# جدول بنود المرافق للنوادي
cursor.execute("""
CREATE TABLE club_facility_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    is_visible BOOLEAN DEFAULT 1,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (facility_id) REFERENCES facility (id),
    FOREIGN KEY (item_id) REFERENCES facility_item (id)
)
""")
print("تم إنشاء جدول club_facility_item")

# جدول التشيكات
cursor.execute("""
CREATE TABLE "check" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")
print("تم إنشاء جدول check")

# جدول بنود التشيك
cursor.execute("""
CREATE TABLE check_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    is_compliant BOOLEAN DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (check_id) REFERENCES "check" (id) ON DELETE CASCADE,
    FOREIGN KEY (facility_id) REFERENCES facility (id),
    FOREIGN KEY (item_id) REFERENCES facility_item (id)
)
""")
print("تم إنشاء جدول check_item")

# جدول صور بنود التشيك
cursor.execute("""
CREATE TABLE check_item_image (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_item_id INTEGER NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (check_item_id) REFERENCES check_item (id) ON DELETE CASCADE
)
""")
print("تم إنشاء جدول check_item_image")

# جدول متابعة الكاميرات
cursor.execute("""
CREATE TABLE camera_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    notes TEXT,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
)
""")
print("تم إنشاء جدول camera_check")

# جدول فترات متابعة الكاميرات
cursor.execute("""
CREATE TABLE camera_time_slot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_check_id INTEGER NOT NULL,
    time_slot VARCHAR(10) NOT NULL,
    is_working BOOLEAN DEFAULT 0,
    FOREIGN KEY (camera_check_id) REFERENCES camera_check (id) ON DELETE CASCADE
)
""")
print("تم إنشاء جدول camera_time_slot")

# إنشاء مستخدم افتراضي
cursor.execute("""
INSERT INTO user (username, password, is_admin)
VALUES ('admin', 'admin', 1)
""")
print("تم إنشاء مستخدم افتراضي: admin/admin")

# إنشاء نادي افتراضي
cursor.execute("""
INSERT INTO club (name, location, manager_name, phone)
VALUES ('نادي افتراضي', 'موقع افتراضي', 'مدير افتراضي', '123456789')
""")
print("تم إنشاء نادي افتراضي")

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print("تم إعادة إنشاء قاعدة البيانات بنجاح!")
