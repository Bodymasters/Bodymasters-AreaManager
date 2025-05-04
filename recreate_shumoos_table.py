import os
from app import app, db, Shumoos

# المسار الكامل لملف قاعدة البيانات
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

# طباعة مسار قاعدة البيانات للتأكد
print(f"مسار قاعدة البيانات: {db_path}")

# إنشاء جدول شموس في قاعدة البيانات
with app.app_context():
    # التحقق من وجود الجدول
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"الجداول الموجودة في قاعدة البيانات: {tables}")
    
    if 'shumoos' not in tables:
        # إنشاء جدول شموس فقط
        Shumoos.__table__.create(db.engine, checkfirst=True)
        print("تم إنشاء جدول شموس بنجاح!")
    else:
        print("جدول شموس موجود بالفعل!")
        
    # التحقق مرة أخرى
    tables = inspector.get_table_names()
    print(f"الجداول بعد الإنشاء: {tables}")
