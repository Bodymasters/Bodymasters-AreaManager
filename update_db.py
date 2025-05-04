import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# تعريف النماذج (Models)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class FacilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)

    # العلاقات
    facility = db.relationship('Facility', backref='items')

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    hire_date = db.Column(db.Date, nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # العلاقات
    club = db.relationship('Club', backref='employees')

class CameraCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=True)  # 'working', 'not_working', 'maintenance'
    notes = db.Column(db.Text)
    violations_count = db.Column(db.Integer, default=0)  # إضافة عمود عدد المخالفات

    # العلاقات
    club = db.relationship('Club', backref='camera_checks')
    user = db.relationship('User', backref='camera_checks')

# تحديث قاعدة البيانات
with app.app_context():
    # إنشاء الجداول الجديدة
    db.create_all()

    # تحديث المرافق الموجودة لإضافة حقل is_active
    facilities = Facility.query.all()
    for facility in facilities:
        facility.is_active = True

    # إضافة بعض بنود المرافق للاختبار
    if FacilityItem.query.count() == 0:
        # الحصول على المرافق
        facilities = Facility.query.all()

        # إضافة بنود لكل مرفق
        for facility in facilities:
            if facility.name == 'مسبح':
                items = ['منشفة', 'كرسي استرخاء', 'نظارات سباحة', 'عوامة']
            elif facility.name == 'ملعب كرة قدم':
                items = ['كرة', 'مرمى', 'سترة تمييز', 'صافرة']
            elif facility.name == 'صالة رياضية':
                items = ['دمبل', 'بساط', 'جهاز جري', 'حبل قفز']
            else:
                items = ['كرسي', 'طاولة', 'مصباح']

            for item_name in items:
                item = FacilityItem(name=item_name, facility_id=facility.id)
                db.session.add(item)

    # حفظ التغييرات
    db.session.commit()

    print('تم تحديث قاعدة البيانات وإضافة البنود بنجاح!')
