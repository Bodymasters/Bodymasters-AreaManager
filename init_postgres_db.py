import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import get_database_uri, SECRET_KEY, SQLALCHEMY_TRACK_MODIFICATIONS
from app import db, User, Club, Facility, FacilityItem, Permission

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# إنشاء قاعدة البيانات
with app.app_context():
    try:
        # إنشاء جميع الجداول
        print("جاري إنشاء جداول قاعدة البيانات...")
        db.create_all()
        print("تم إنشاء جميع الجداول بنجاح!")

        # إضافة مستخدم مسؤول افتراضي
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("إضافة مستخدم مسؤول افتراضي...")
            admin = User(username='admin', name='مدير النظام', password='admin123', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("تم إضافة المستخدم المسؤول بنجاح!")
        else:
            print("المستخدم المسؤول موجود بالفعل.")

        # إضافة بيانات تجريبية للنوادي
        if Club.query.count() == 0:
            print("إضافة بيانات تجريبية للنوادي...")
            club1 = Club(name='نادي الرياض', location='الرياض - حي النزهة', manager_name='أحمد محمد', phone='0501234567')
            club2 = Club(name='نادي جدة', location='جدة - حي الروضة', manager_name='خالد عبدالله', phone='0551234567')
            
            db.session.add(club1)
            db.session.add(club2)
            db.session.commit()
            print("تم إضافة بيانات النوادي التجريبية بنجاح!")
        else:
            print("توجد بيانات نوادي بالفعل.")

        # إضافة بيانات تجريبية للمرافق
        if Facility.query.count() == 0:
            print("إضافة بيانات تجريبية للمرافق...")
            facility1 = Facility(name='مرفق الاستقبال', is_active=True)
            facility2 = Facility(name='مرفق الصالة الرياضية', is_active=True)
            
            db.session.add(facility1)
            db.session.add(facility2)
            db.session.commit()
            
            # إضافة بنود المرافق
            item1 = FacilityItem(name='نظافة منطقة الاستقبال', is_active=True, facility_id=facility1.id)
            item2 = FacilityItem(name='عمل موظفي الاستقبال', is_active=True, facility_id=facility1.id)
            item3 = FacilityItem(name='نظافة الصالة الرياضية', is_active=True, facility_id=facility2.id)
            item4 = FacilityItem(name='صيانة الأجهزة الرياضية', is_active=True, facility_id=facility2.id)
            
            db.session.add_all([item1, item2, item3, item4])
            db.session.commit()
            print("تم إضافة بيانات المرافق وبنودها التجريبية بنجاح!")
        else:
            print("توجد بيانات مرافق بالفعل.")

        # إضافة الصلاحيات الأساسية
        if Permission.query.count() == 0:
            print("إضافة الصلاحيات الأساسية...")
            permissions = [
                Permission(name='عرض لوحة التحكم', description='الوصول إلى لوحة التحكم', code='view_dashboard'),
                Permission(name='إدارة المستخدمين', description='إضافة وتعديل وحذف المستخدمين', code='manage_users'),
                Permission(name='إدارة النوادي', description='إضافة وتعديل وحذف النوادي', code='manage_clubs'),
                Permission(name='إدارة المرافق', description='إضافة وتعديل وحذف المرافق', code='manage_facilities'),
                Permission(name='إدارة الموظفين', description='إضافة وتعديل وحذف الموظفين', code='manage_employees'),
                Permission(name='إدارة التشيك', description='إضافة وتعديل وحذف التشيك', code='manage_checks'),
                Permission(name='إدارة المبيعات', description='إضافة وتعديل وحذف المبيعات', code='manage_sales'),
                Permission(name='عرض جميع النوادي', description='عرض بيانات جميع النوادي', code='view_all'),
                Permission(name='استيراد البيانات', description='استيراد البيانات من ملفات إكسل', code='import_data'),
                Permission(name='تصدير البيانات', description='تصدير البيانات إلى ملفات إكسل', code='export_data'),
            ]
            
            db.session.add_all(permissions)
            db.session.commit()
            
            # إعطاء جميع الصلاحيات للمستخدم المسؤول
            admin = User.query.filter_by(username='admin').first()
            if admin:
                for permission in Permission.query.all():
                    admin.permissions.append(permission)
                db.session.commit()
            
            print("تم إضافة الصلاحيات الأساسية بنجاح!")
        else:
            print("توجد صلاحيات بالفعل.")

        print("تم تهيئة قاعدة البيانات بنجاح!")

    except Exception as e:
        print(f"حدث خطأ أثناء تهيئة قاعدة البيانات: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
