import sqlite3

# اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# التحقق من وجود الأعمدة الجديدة في جدول المستخدمين
cursor.execute("PRAGMA table_info(user)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# إضافة الأعمدة الجديدة إذا لم تكن موجودة
if 'name' not in column_names:
    print("إضافة عمود 'name' إلى جدول المستخدمين...")
    cursor.execute("ALTER TABLE user ADD COLUMN name TEXT DEFAULT 'مستخدم'")

if 'phone' not in column_names:
    print("إضافة عمود 'phone' إلى جدول المستخدمين...")
    cursor.execute("ALTER TABLE user ADD COLUMN phone TEXT")

# إنشاء جدول العلاقة بين المستخدمين والنوادي إذا لم يكن موجوداً
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_clubs (
    user_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, club_id),
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (club_id) REFERENCES club (id)
)
""")
print("تم إنشاء جدول العلاقة بين المستخدمين والنوادي")

# حفظ التغييرات
conn.commit()

# إغلاق الاتصال
conn.close()

print("تم تحديث قاعدة البيانات بنجاح!")
