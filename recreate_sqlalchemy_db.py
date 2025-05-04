import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

# حذف قاعدة البيانات الحالية إذا كانت موجودة
db_path = 'app.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"تم حذف قاعدة البيانات القديمة: {db_path}")

# إنشاء تطبيق Flask وإعداد قاعدة البيانات
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# جدول العلاقة بين النوادي والمرافق
club_facilities = db.Table('club_facilities',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('facility_id', db.Integer, db.ForeignKey('facility.id'), primary_key=True)
)

# جدول العلاقة بين المستخدمين والنوادي
user_clubs = db.Table('user_clubs',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True)
)

# تعريف النماذج (Models)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)  # الرقم الوظيفي
    name = db.Column(db.String(100), nullable=False, default='مستخدم')  # الاسم
    phone = db.Column(db.String(20))  # رقم الهاتف
    password = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

    # العلاقة مع النوادي
    clubs = db.relationship('Club', secondary=user_clubs, lazy='subquery',
                          backref=db.backref('users', lazy=True))

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # العلاقة مع المرافق
    facilities = db.relationship('Facility', secondary=club_facilities, lazy='subquery',
                               backref=db.backref('clubs', lazy=True))

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_imported = db.Column(db.Boolean, default=False)  # حقل يشير إلى أن المرفق تم استيراده من ملف إكسل

class FacilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)

    # العلاقات
    facility = db.relationship('Facility', backref='items')

class ClubFacilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    facility_item_id = db.Column(db.Integer, db.ForeignKey('facility_item.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # العلاقات
    club = db.relationship('Club', backref='club_facility_items')
    facility = db.relationship('Facility')
    facility_item = db.relationship('FacilityItem')

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)  # الرقم الوظيفي
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)  # الوظيفة
    role = db.Column(db.String(100), nullable=False)  # الدور الوظيفي
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)  # الحالة
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # العلاقات
    club = db.relationship('Club', backref='employees')

class CameraCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    notes = db.Column(db.Text)

    # العلاقات
    club = db.relationship('Club', backref='camera_checks')
    user = db.relationship('User', backref='camera_checks')
    time_slots = db.relationship('CameraTimeSlot', backref='camera_check', cascade='all, delete-orphan')

class CameraTimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    camera_check_id = db.Column(db.Integer, db.ForeignKey('camera_check.id'), nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)  # مثل "05:00", "08:00", إلخ
    is_working = db.Column(db.Boolean, default=False)  # تعمل أم لا

class Check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)

    # العلاقات
    club = db.relationship('Club', backref='checks')
    user = db.relationship('User', backref='checks')
    items = db.relationship('CheckItem', backref='check', cascade='all, delete-orphan')

class CheckItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_id = db.Column(db.Integer, db.ForeignKey('check.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    facility_item_id = db.Column(db.Integer, db.ForeignKey('facility_item.id'), nullable=False)
    is_compliant = db.Column(db.Boolean, default=False)  # مطابق أو غير مطابق
    notes = db.Column(db.Text)

    # العلاقات
    facility = db.relationship('Facility')
    facility_item = db.relationship('FacilityItem')
    images = db.relationship('CheckItemImage', backref='check_item', cascade='all, delete-orphan')

class CheckItemImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_item_id = db.Column(db.Integer, db.ForeignKey('check_item.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)

# إنشاء قاعدة البيانات
with app.app_context():
    # إنشاء الجداول
    db.create_all()

    # إضافة مستخدم افتراضي
    admin = User(username='admin', name='مدير النظام', password='admin', is_admin=True)
    db.session.add(admin)

    # إضافة نادي افتراضي
    club = Club(name='نادي افتراضي', location='موقع افتراضي', manager_name='مدير افتراضي', phone='123456789')
    db.session.add(club)

    # إضافة مرفق افتراضي
    facility = Facility(name='مرفق افتراضي', is_active=True, is_imported=True)
    db.session.add(facility)

    # حفظ التغييرات لإنشاء النادي والمرفق أولاً
    db.session.commit()

    # إضافة بند مرفق افتراضي
    facility_item = FacilityItem(name='بند افتراضي', is_active=True, facility_id=facility.id)
    db.session.add(facility_item)

    # ربط المستخدم الافتراضي بالنادي الافتراضي
    admin.clubs.append(club)

    # حفظ التغييرات
    db.session.commit()

    print('تم إنشاء قاعدة البيانات وإضافة البيانات الأولية بنجاح!')
