import os
import sqlite3
from datetime import date

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app_new.db')

# حذف قاعدة البيانات القديمة إذا كانت موجودة
if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print("تم حذف قاعدة البيانات القديمة بنجاح.")
    except Exception as e:
        print(f"خطأ في حذف قاعدة البيانات القديمة: {str(e)}")
        print("سنحاول إنشاء قاعدة بيانات جديدة على أي حال.")

# إنشاء اتصال بقاعدة البيانات الجديدة
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# إنشاء جدول المستخدمين
cursor.execute('''
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    is_admin BOOLEAN DEFAULT 0
)
''')

# إنشاء جدول النوادي
cursor.execute('''
CREATE TABLE club (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    manager_name VARCHAR(100),
    phone VARCHAR(20)
)
''')

# إنشاء جدول المرافق
cursor.execute('''
CREATE TABLE facility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT 1
)
''')

# إنشاء جدول بنود المرافق
cursor.execute('''
CREATE TABLE facility_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    facility_id INTEGER NOT NULL,
    FOREIGN KEY (facility_id) REFERENCES facility (id)
)
''')

# إنشاء جدول الموظفين
cursor.execute('''
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
''')

# إنشاء جدول فحوصات الكاميرات
cursor.execute('''
CREATE TABLE camera_check (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    check_date DATE NOT NULL,
    club_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    notes TEXT,
    FOREIGN KEY (club_id) REFERENCES club (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
)
''')

# إضافة مستخدم مسؤول
cursor.execute('''
INSERT INTO user (username, password, is_admin)
VALUES (?, ?, ?)
''', ('admin', 'admin123', 1))

# إضافة بيانات تجريبية للنوادي
clubs = [
    ('نادي الرياض', 'الرياض - حي النزهة', 'أحمد محمد', '0501234567'),
    ('نادي جدة', 'جدة - حي الروضة', 'خالد عبدالله', '0551234567')
]

for club in clubs:
    cursor.execute('''
    INSERT INTO club (name, location, manager_name, phone)
    VALUES (?, ?, ?, ?)
    ''', club)

# إضافة بيانات تجريبية للمرافق
facilities_data = [
    "مسبح",
    "ملعب كرة قدم",
    "صالة رياضية",
    "ملعب تنس",
    "ساونا",
    "جاكوزي"
]

for facility_name in facilities_data:
    cursor.execute('''
    INSERT INTO facility (name, is_active)
    VALUES (?, ?)
    ''', (facility_name, 1))

# الحصول على معرفات المرافق
cursor.execute('SELECT id, name FROM facility')
facilities = cursor.fetchall()

# إضافة بنود للمرافق
facility_items = {
    "مسبح": ['منشفة', 'كرسي استرخاء', 'نظارات سباحة', 'عوامة'],
    "ملعب كرة قدم": ['كرة', 'مرمى', 'سترة تمييز', 'صافرة'],
    "صالة رياضية": ['دمبل', 'بساط', 'جهاز جري', 'حبل قفز'],
    "ملعب تنس": ['مضرب', 'كرة تنس', 'شبكة'],
    "ساونا": ['منشفة', 'مقعد خشبي', 'ميزان حرارة'],
    "جاكوزي": ['منشفة', 'فلتر', 'مضخة']
}

for facility_id, facility_name in facilities:
    if facility_name in facility_items:
        for item_name in facility_items[facility_name]:
            cursor.execute('''
            INSERT INTO facility_item (name, is_active, facility_id)
            VALUES (?, ?, ?)
            ''', (item_name, 1, facility_id))

# حفظ التغييرات وإغلاق الاتصال
conn.commit()
conn.close()

print('تم إنشاء قاعدة البيانات وإضافة البيانات الأولية بنجاح!')
