import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'employee_db_updated.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# جدول العلاقة بين النوادي والمرافق
club_facilities = db.Table('club_facilities',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('facility_id', db.Integer, db.ForeignKey('facility.id'), primary_key=True)
)

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
    
    # العلاقة مع المرافق
    facilities = db.relationship('Facility', secondary=club_facilities, lazy='subquery',
                               backref=db.backref('clubs', lazy=True))

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_imported = db.Column(db.Boolean, default=False)  # حقل يشير إلى أن المرفق تم استيراده من ملف إكسل

    def __repr__(self):
        return f'<Facility {self.name}>'

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

    def __repr__(self):
        return f'<ClubFacilityItem {self.id}>'

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

    def __repr__(self):
        return f'<Employee {self.name}>'

class CameraCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'working', 'not_working', 'maintenance'
    notes = db.Column(db.Text)
    
    # العلاقات
    club = db.relationship('Club', backref='camera_checks')
    user = db.relationship('User', backref='camera_checks')

# إنشاء قاعدة البيانات
with app.app_context():
    # إنشاء الجداول
    db.create_all()
    
    # إضافة مستخدم مسؤول
    admin = User(username='admin', password='admin123', is_admin=True)
    db.session.add(admin)
    
    # إضافة بيانات تجريبية للمرافق
    facilities_data = [
        "مسبح",
        "ملعب كرة قدم",
        "صالة رياضية",
        "ملعب تنس",
        "ساونا",
        "جاكوزي"
    ]
    
    facilities = []
    for facility_name in facilities_data:
        facility = Facility(name=facility_name, is_active=True, is_imported=True)  # تعيين قيمة الحقل الجديد
        db.session.add(facility)
        facilities.append(facility)
    
    # حفظ التغييرات لإنشاء المرافق أولاً
    db.session.commit()
    
    # إضافة بيانات تجريبية للنوادي مع المرافق
    club1 = Club(name='نادي الرياض', location='الرياض - حي النزهة', manager_name='أحمد محمد', phone='0501234567')
    club2 = Club(name='نادي جدة', location='جدة - حي الروضة', manager_name='خالد عبدالله', phone='0551234567')
    
    # إضافة المرافق للنوادي
    club1.facilities = facilities[:3]  # المسبح، ملعب كرة قدم، صالة رياضية
    club2.facilities = facilities[3:]  # ملعب تنس، ساونا، جاكوزي
    
    db.session.add(club1)
    db.session.add(club2)
    
    # إضافة بنود للمرافق
    facility_items = {
        "مسبح": ['منشفة', 'كرسي استرخاء', 'نظارات سباحة', 'عوامة'],
        "ملعب كرة قدم": ['كرة', 'مرمى', 'سترة تمييز', 'صافرة'],
        "صالة رياضية": ['دمبل', 'بساط', 'جهاز جري', 'حبل قفز'],
        "ملعب تنس": ['مضرب', 'كرة تنس', 'شبكة'],
        "ساونا": ['منشفة', 'مقعد خشبي', 'ميزان حرارة'],
        "جاكوزي": ['منشفة', 'فلتر', 'مضخة']
    }
    
    # قاموس لتخزين بنود المرافق
    all_facility_items = {}
    
    for facility in facilities:
        if facility.name in facility_items:
            for item_name in facility_items[facility.name]:
                item = FacilityItem(name=item_name, facility_id=facility.id, is_active=True)
                db.session.add(item)
                
                # تخزين البند في القاموس
                if facility.name not in all_facility_items:
                    all_facility_items[facility.name] = []
                all_facility_items[facility.name].append(item)
    
    # حفظ التغييرات لإنشاء بنود المرافق
    db.session.commit()
    
    # إضافة بنود المرافق للنوادي
    for facility in club1.facilities:
        if facility.name in all_facility_items:
            for item in all_facility_items[facility.name]:
                club_facility_item = ClubFacilityItem(
                    club_id=club1.id,
                    facility_id=facility.id,
                    facility_item_id=item.id,
                    is_active=True
                )
                db.session.add(club_facility_item)
    
    for facility in club2.facilities:
        if facility.name in all_facility_items:
            for item in all_facility_items[facility.name]:
                club_facility_item = ClubFacilityItem(
                    club_id=club2.id,
                    facility_id=facility.id,
                    facility_item_id=item.id,
                    is_active=True
                )
                db.session.add(club_facility_item)
    
    # إضافة بيانات تجريبية للموظفين
    employees_data = [
        {
            "employee_id": "EMP001",
            "name": "محمد أحمد",
            "position": "مدرب سباحة",
            "role": "مدرب",
            "phone": "0501111111",
            "is_active": True,
            "club_id": club1.id
        },
        {
            "employee_id": "EMP002",
            "name": "خالد محمد",
            "position": "مدرب لياقة",
            "role": "مدرب",
            "phone": "0502222222",
            "is_active": True,
            "club_id": club1.id
        },
        {
            "employee_id": "EMP003",
            "name": "فاطمة علي",
            "position": "مديرة مبيعات",
            "role": "إداري",
            "phone": "0503333333",
            "is_active": True,
            "club_id": club2.id
        },
        {
            "employee_id": "EMP004",
            "name": "سارة محمد",
            "position": "مدربة لياقة",
            "role": "مدرب",
            "phone": "0504444444",
            "is_active": False,
            "club_id": club2.id
        }
    ]
    
    for emp_data in employees_data:
        employee = Employee(**emp_data)
        db.session.add(employee)
    
    # حفظ التغييرات
    db.session.commit()
    
    print('تم إنشاء قاعدة البيانات وإضافة البيانات الأولية بنجاح!')
