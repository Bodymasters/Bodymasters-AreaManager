import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# إعداد التطبيق وقاعدة البيانات
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# تعريف النماذج
class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    facilities = db.relationship('Facility', secondary='club_facilities', backref='clubs')

class Facility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_imported = db.Column(db.Boolean, default=False)

class FacilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    facility = db.relationship('Facility', backref='items')

class ClubFacilityItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    facility_item_id = db.Column(db.Integer, db.ForeignKey('facility_item.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    club = db.relationship('Club')
    facility = db.relationship('Facility')
    facility_item = db.relationship('FacilityItem')

# جدول العلاقة بين النوادي والمرافق
club_facilities = db.Table('club_facilities',
    db.Column('club_id', db.Integer, db.ForeignKey('club.id'), primary_key=True),
    db.Column('facility_id', db.Integer, db.ForeignKey('facility.id'), primary_key=True)
)

# إضافة بيانات اختبار
with app.app_context():
    # الحصول على النادي الافتراضي
    club = Club.query.first()
    if not club:
        print("لا يوجد نادي في قاعدة البيانات")
        exit()

    # إضافة مرفق جديد
    facility = Facility(name="مرفق جديد", is_active=True, is_imported=True)
    db.session.add(facility)
    db.session.commit()

    # إضافة بند للمرفق
    facility_item = FacilityItem(name="بند جديد", is_active=True, facility_id=facility.id)
    db.session.add(facility_item)
    db.session.commit()

    # ربط المرفق بالنادي
    club.facilities.append(facility)
    db.session.commit()

    # إضافة بند المرفق للنادي
    club_facility_item = ClubFacilityItem(
        club_id=club.id,
        facility_id=facility.id,
        facility_item_id=facility_item.id,
        is_active=True
    )
    db.session.add(club_facility_item)
    db.session.commit()

    print(f"تم إضافة المرفق '{facility.name}' والبند '{facility_item.name}' للنادي '{club.name}' بنجاح!")
