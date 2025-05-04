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
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', password='admin123', is_admin=True)
        db.session.add(admin)
    
    # إضافة بيانات تجريبية للنوادي
    if Club.query.count() == 0:
        club1 = Club(name='نادي الرياض', location='الرياض - حي النزهة', manager_name='أحمد محمد', phone='0501234567')
        club2 = Club(name='نادي جدة', location='جدة - حي الروضة', manager_name='خالد عبدالله', phone='0551234567')
        
        db.session.add(club1)
        db.session.add(club2)
    
    # إضافة بيانات تجريبية للمرافق
    if Facility.query.count() == 0:
        facilities = [
            "مسبح",
            "ملعب كرة قدم",
            "صالة رياضية",
            "ملعب تنس",
            "ساونا",
            "جاكوزي"
        ]
        
        for facility_name in facilities:
            facility = Facility(name=facility_name)
            db.session.add(facility)
    
    # حفظ التغييرات
    db.session.commit()
    
    print('تم إنشاء قاعدة البيانات وإضافة البيانات الأولية بنجاح!')
