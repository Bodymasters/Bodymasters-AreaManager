import os
import pandas as pd
import traceback
import time
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify, session, g
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
import uuid
import calendar
from config import get_database_uri, SECRET_KEY, SQLALCHEMY_TRACK_MODIFICATIONS

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

# إضافة فلتر fromjson لتحويل النص JSON إلى كائن Python
import json
@app.template_filter('fromjson')
def fromjson(value):
    try:
        # طباعة القيمة للتشخيص
        print(f"محاولة تحليل JSON: {value}")
        result = json.loads(value)
        print(f"نتيجة التحليل: {result}")
        return result
    except Exception as e:
        print(f"خطأ في تحليل JSON: {e}")
        return {}

# إعدادات تحميل الملفات
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# إنشاء مجلد التحميلات إذا لم يكن موجوداً
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'
login.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'

# تتبع استعلامات قاعدة البيانات
if app.debug:
    # تتبع وقت تنفيذ الاستعلامات
    @event.listens_for(db.engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
        if not hasattr(g, '_query_count'):
            g._query_count = 0
        g._query_count += 1
        app.logger.debug(f"Query #{g._query_count}: {statement}")

    @event.listens_for(db.engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop()
        app.logger.debug(f"Query execution time: {total:.4f}s")

        # تسجيل الاستعلامات البطيئة
        if total > 0.1:  # أكثر من 100 مللي ثانية
            app.logger.warning(f"Slow query detected: {statement} ({total:.4f}s)")

# تحسين جلسة قاعدة البيانات
db.session.expire_on_commit = False

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

# تعريف جدول العلاقة بين المستخدمين والصلاحيات
user_permission = db.Table('user_permission',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'), primary_key=True)
)

# تعريف النماذج (Models)
# تعريف نموذج الصلاحيات
class Permission(db.Model):
    __tablename__ = 'permission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    code = db.Column(db.String(50), unique=True, nullable=False)

# تعريف نموذج المستخدم
class User(UserMixin, db.Model):
    __table__ = db.Table('user', db.metadata,
        db.Column('id', db.Integer, primary_key=True),
        db.Column('username', db.String(64), index=True, unique=True),
        db.Column('name', db.String(100)),
        db.Column('phone', db.String(20)),
        db.Column('password', db.String(128)),
        db.Column('is_admin', db.Boolean, default=False),
        db.Column('role', db.String(50), default='user'),  # الدور: admin, manager, supervisor, user
        extend_existing=True
    )

    # العلاقة مع الصلاحيات
    permissions = db.relationship('Permission', secondary='user_permission', lazy='subquery',
                               backref=db.backref('users', lazy=True))

    # العلاقة مع النوادي
    clubs = db.relationship('Club', secondary=user_clubs, lazy='subquery',
                          backref=db.backref('users', lazy=True))

    def has_permission(self, permission_code):
        """التحقق من امتلاك المستخدم لصلاحية معينة"""
        try:
            # المسؤول لديه جميع الصلاحيات
            if self.is_admin:
                return True

            # التحقق من وجود الصلاحية في قائمة صلاحيات المستخدم
            # استخدام استعلام مباشر بدلاً من العلاقة
            user_permission_codes = db.session.query(Permission.code).join(
                user_permission,
                (user_permission.c.permission_id == Permission.id) & (user_permission.c.user_id == self.id)
            ).all()

            # تحويل النتائج إلى قائمة
            user_permission_codes = [p[0] for p in user_permission_codes]

            if permission_code in user_permission_codes:
                return True

            # التحقق من وجود الصلاحية في قائمة صلاحيات الدور
            role = self.role or 'user'  # استخدام دور المستخدم العادي إذا لم يكن هناك دور محدد

            # الحصول على صلاحيات الدور من قاعدة البيانات
            role_permissions = db.session.query(Permission.code).join(
                db.Table('role_permission', db.metadata,
                    db.Column('role', db.String(50)),
                    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')),
                    extend_existing=True
                )
            ).filter_by(role=role).all()

            # تحويل النتائج إلى قائمة
            role_permission_codes = [p[0] for p in role_permissions]

            return permission_code in role_permission_codes
        except Exception as e:
            print(f"خطأ في التحقق من الصلاحيات: {str(e)}")
            return False

    def can_access_club(self, club):
        """التحقق من إمكانية وصول المستخدم إلى نادي معين"""
        try:
            # المسؤول يمكنه الوصول إلى جميع النوادي
            if self.is_admin or self.has_permission('view_all'):
                return True

            # التحقق من وجود النادي في قائمة النوادي المخصصة للمستخدم
            # استخدام استعلام مباشر بدلاً من العلاقة
            club_count = db.session.query(user_clubs).filter(
                (user_clubs.c.user_id == self.id) & (user_clubs.c.club_id == club.id)
            ).count()

            return club_count > 0
        except Exception as e:
            print(f"خطأ في التحقق من إمكانية الوصول إلى النادي: {str(e)}")
            return False

@login.user_loader
def load_user(id):
    # استخدام الطريقة البسيطة لتجنب مشاكل تحميل العلاقات
    return User.query.get(int(id))

class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    manager_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))

    # العلاقة مع المرافق
    facilities = db.relationship('Facility', secondary=club_facilities, lazy='subquery',
                               backref=db.backref('clubs', lazy=True))

    def __repr__(self):
        return f'<Club {self.name}>'

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

    def __repr__(self):
        return f'<CameraCheck {self.id} - {self.check_date}>'



# نموذج متابعة الكاميرات
class CameraCheck(db.Model):
    __tablename__ = 'camera_check'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='active')
    violations_count = db.Column(db.String(50), nullable=True)  # عدد المخالفات
    notes = db.Column(db.Text)

    # العلاقات
    club = db.relationship('Club', backref='camera_checks')
    user = db.relationship('User', backref='camera_checks')
    time_slots = db.relationship('CameraTimeSlot', backref='camera_check', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<CameraCheck {self.id} for Club {self.club_id} on {self.check_date}>'

# نموذج فترات المتابعة للكاميرات
class CameraTimeSlot(db.Model):
    __tablename__ = 'camera_time_slot'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    camera_check_id = db.Column(db.Integer, db.ForeignKey('camera_check.id'), nullable=False)
    time_slot = db.Column(db.String(10), nullable=False)  # مثل "05:00", "08:00", إلخ
    is_working = db.Column(db.Boolean, default=False)  # تعمل أم لا

    def __repr__(self):
        return f'<CameraTimeSlot {self.id} for CameraCheck {self.camera_check_id} at {self.time_slot}>'

# نموذج التشيك
class Check(db.Model):
    __tablename__ = 'check'
    id = db.Column(db.Integer, primary_key=True)
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.Column(db.Text)

    # العلاقات
    club = db.relationship('Club', backref='checks')
    user = db.relationship('User', backref='checks')
    items = db.relationship('CheckItem', backref='check', cascade='all, delete-orphan')

    def get_compliance_percentage(self):
        """ حساب نسبة المطابقة للتشيك """
        # الحصول على جميع المرافق والبنود المتاحة للنادي
        club = self.club
        club_facilities = list(club.facilities)

        # قاموس لتخزين البنود الحالية للتشيك
        check_items_dict = {}
        for check_item in self.items:
            check_items_dict[check_item.facility_item_id] = check_item

        # حساب إحصائيات التشيك
        total_items = 0
        compliant_items = 0

        # معالجة كل مرفق
        for facility in club_facilities:
            # الحصول على بنود المرفق النشطة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

            # إضافة عدد البنود إلى الإجمالي
            total_items += len(facility_items)

            # حساب عدد البنود المطابقة
            for facility_item in facility_items:
                if facility_item.id in check_items_dict and check_items_dict[facility_item.id].is_compliant:
                    compliant_items += 1

        # حساب النسبة المئوية
        if total_items == 0:
            return 0
        return round((compliant_items / total_items * 100), 1)

    def get_compliant_items_count(self):
        """ حساب عدد البنود المطابقة """
        # الحصول على جميع المرافق والبنود المتاحة للنادي
        club = self.club
        club_facilities = list(club.facilities)

        # قاموس لتخزين البنود الحالية للتشيك
        check_items_dict = {}
        for check_item in self.items:
            check_items_dict[check_item.facility_item_id] = check_item

        # حساب عدد البنود المطابقة
        compliant_items = 0

        # معالجة كل مرفق
        for facility in club_facilities:
            # الحصول على بنود المرفق النشطة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

            # حساب عدد البنود المطابقة
            for facility_item in facility_items:
                if facility_item.id in check_items_dict and check_items_dict[facility_item.id].is_compliant:
                    compliant_items += 1

        return compliant_items

    def get_total_items_count(self):
        """ حساب إجمالي عدد البنود """
        # الحصول على جميع المرافق والبنود المتاحة للنادي
        club = self.club
        club_facilities = list(club.facilities)

        # حساب إجمالي عدد البنود
        total_items = 0

        # معالجة كل مرفق
        for facility in club_facilities:
            # الحصول على بنود المرفق النشطة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

            # إضافة عدد البنود إلى الإجمالي
            total_items += len(facility_items)

        return total_items

    def __repr__(self):
        return f'<Check {self.id} for Club {self.club_id} on {self.check_date}>'

# نموذج بنود التشيك
class CheckItem(db.Model):
    __tablename__ = 'check_item'
    id = db.Column(db.Integer, primary_key=True)
    check_id = db.Column(db.Integer, db.ForeignKey('check.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=False)
    facility_item_id = db.Column(db.Integer, db.ForeignKey('facility_item.id'), nullable=False)
    is_compliant = db.Column(db.Boolean, default=False)  # مطابق أو غير مطابق
    notes = db.Column(db.Text)

    # العلاقات
    facility = db.relationship('Facility')
    facility_item = db.relationship('FacilityItem')

    def __repr__(self):
        return f'<CheckItem {self.id} for Check {self.check_id}>'

# نموذج صور بنود التشيك
class CheckItemImage(db.Model):
    __tablename__ = 'check_item_image'
    id = db.Column(db.Integer, primary_key=True)
    check_item_id = db.Column(db.Integer, db.ForeignKey('check_item.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)

    # العلاقات
    check_item = db.relationship('CheckItem', backref='images')

    def __repr__(self):
        return f'<CheckItemImage {self.id} for CheckItem {self.check_item_id}>'

# نموذج المبيعات الشهرية
class SalesTarget(db.Model):
    __tablename__ = 'sales_target'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # بتنسيق YYYY-MM
    target_amount = db.Column(db.Float, nullable=False)
    online_sales = db.Column(db.Float, default=0)  # مبيعات الأونلاين
    personal_training_sales = db.Column(db.Float, default=0)  # مبيعات التدريب الشخصي
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    club = db.relationship('Club', backref='sales_targets')
    daily_sales = db.relationship('DailySales', backref='target', cascade='all, delete-orphan')

    def get_days_in_month(self):
        """ حساب عدد أيام الشهر """
        year, month = map(int, self.month.split('-'))
        return calendar.monthrange(year, month)[1]

    def get_daily_target(self):
        """ حساب التارجيت اليومي """
        return self.target_amount / self.get_days_in_month()

    def get_achieved_amount(self):
        """ حساب المبلغ المحقق """
        # جمع مبيعات الأيام مع مبيعات الأونلاين ومبيعات التدريب الشخصي
        daily_total = sum(sale.amount for sale in self.daily_sales)
        return daily_total + self.online_sales + self.personal_training_sales

    def get_remaining_amount(self):
        """ حساب المبلغ المتبقي """
        return self.target_amount - self.get_achieved_amount()

    def get_achievement_percentage(self):
        """ حساب نسبة الإنجاز """
        if self.target_amount == 0:
            return 0
        return round((self.get_achieved_amount() / self.target_amount * 100), 1)

    def __repr__(self):
        return f'<SalesTarget {self.id} for Club {self.club_id} on {self.month}>'

# نموذج جدول دوام الموظف
class EmployeeSchedule(db.Model):
    __tablename__ = 'employee_schedule'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)

    # نوع الدوام (فترة واحدة أو فترتين)
    shift_type = db.Column(db.String(20), default="one_shift")  # one_shift أو two_shifts

    # ساعات العمل
    work_hours = db.Column(db.Integer, default=8)  # 7 أو 8 ساعات

    # معلومات الدوام الأول
    shift1_start = db.Column(db.String(10))  # وقت بداية الدوام الأول
    shift1_end = db.Column(db.String(10))    # وقت نهاية الدوام الأول

    # معلومات الدوام الثاني
    shift2_start = db.Column(db.String(10))  # وقت بداية الدوام الثاني
    shift2_end = db.Column(db.String(10))    # وقت نهاية الدوام الثاني

    # رقم الجوال
    mobile_number = db.Column(db.String(20))

    # أيام الدوام
    work_days = db.Column(db.String(100))  # سيتم تخزينها كسلسلة مفصولة بفواصل

    # أيام الإجازة
    off_days = db.Column(db.String(100))   # سيتم تخزينها كسلسلة مفصولة بفواصل

    # معلومات التخصيص
    allocation_from = db.Column(db.String(10))  # من تاريخ
    allocation_to = db.Column(db.String(10))    # إلى تاريخ
    allocation_day = db.Column(db.String(20))   # يوم التخصيص

    # العلاقات
    employee = db.relationship('Employee', backref='schedules')
    club = db.relationship('Club', backref='employee_schedules')

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<EmployeeSchedule {self.id} for Employee {self.employee_id} at Club {self.club_id}>'

# نموذج المبيعات اليومية
class DailySales(db.Model):
    __tablename__ = 'daily_sales'
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('sales_target.id'), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f'<DailySales {self.id} for Target {self.target_id} on {self.sale_date}>'

# نموذج الأعطال الحرجة
class CriticalIssue(db.Model):
    __tablename__ = 'critical_issue'
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(50), nullable=False)  # رقم الطلب
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)
    # facility_id = db.Column(db.Integer, db.ForeignKey('facility.id'), nullable=True)  # المرفق - معطل مؤقتا
    creation_date = db.Column(db.Date, nullable=False, default=date.today)  # تاريخ إنشاء الطلب
    due_date = db.Column(db.Date, nullable=False)  # تاريخ الاستحقاق
    status = db.Column(db.String(50), nullable=False)  # الحالة (اغلاق الطلب بدون صيانة - تخطت تاريخ الاستحقاق - معلقة - تمت الصيانة)
    notes = db.Column(db.Text)  # ملاحظات
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    club = db.relationship('Club', backref='critical_issues')
    # facility = db.relationship('Facility', backref='critical_issues')  # معطل مؤقتا

    def __repr__(self):
        return f'<CriticalIssue {self.id} - Ticket: {self.ticket_number} for Club {self.club_id}>'

# نموذج أنواع المخالفات
class ViolationType(db.Model):
    __tablename__ = 'violation_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # اسم نوع المخالفة
    description = db.Column(db.Text)  # وصف المخالفة
    is_active = db.Column(db.Boolean, default=True)  # حالة المخالفة (نشطة أم لا)
    is_imported = db.Column(db.Boolean, default=False)  # تم استيرادها من ملف إكسل
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    violations = db.relationship('Violation', backref='violation_type')

    def __repr__(self):
        return f'<ViolationType {self.id} - {self.name}>'

# نموذج المخالفات
class Violation(db.Model):
    __tablename__ = 'violation'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)  # الموظف
    violation_type_id = db.Column(db.Integer, db.ForeignKey('violation_type.id'), nullable=False)  # نوع المخالفة
    violation_number = db.Column(db.Integer, nullable=False)  # رقم المخالفة
    violation_date = db.Column(db.Date, nullable=False, default=date.today)  # تاريخ المخالفة
    violation_source = db.Column(db.String(50), nullable=False)  # مصدر المخالفة (مدبر المنطقه - مدير النادي - مراقبه الكاميرات - مدير الانديه)
    is_signed = db.Column(db.Boolean, default=False)  # تم التوقيع عليها أم لا
    image_path = db.Column(db.String(255))  # مسار صورة المخالفة
    notes = db.Column(db.Text)  # ملاحظات
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # المستخدم الذي أضاف المخالفة
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    employee = db.relationship('Employee', backref='violations')
    user = db.relationship('User', backref='created_violations')

    def __repr__(self):
        return f'<Violation {self.id} - Employee: {self.employee_id} - Type: {self.violation_type_id}>'

# نموذج شموس
class Shumoos(db.Model):
    __tablename__ = 'shumoos'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('club.id'), nullable=False)  # النادي
    registered_count = db.Column(db.Integer, nullable=False)  # العدد المسجل في النظام
    registration_date = db.Column(db.Date, nullable=False, default=date.today)  # تاريخ التسجيل
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # المستخدم الذي أضاف السجل
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # العلاقات
    club = db.relationship('Club', backref='shumoos_records')
    user = db.relationship('User', backref='created_shumoos')

    def get_difference(self):
        """ حساب الفارق بين العدد الحالي والعدد السابق """
        # البحث عن آخر سجل للنادي قبل هذا السجل
        previous_record = Shumoos.query.filter(
            Shumoos.club_id == self.club_id,
            Shumoos.registration_date < self.registration_date
        ).order_by(Shumoos.registration_date.desc()).first()

        if previous_record:
            return self.registered_count - previous_record.registered_count
        else:
            return 0  # لا يوجد سجل سابق

    def __repr__(self):
        return f'<Shumoos {self.id} - Club: {self.club_id} - Count: {self.registered_count}>'

# استيراد محسن قاعدة البيانات
from utils.db_optimizer import cached_query, optimize_query

# المسارات (Routes)
@app.route('/')
@app.route('/index')
@login_required
def index():
    # قياس وقت تحميل الصفحة
    start_time = time.time()

    # استخدام التخزين المؤقت للاستعلامات المتكررة
    @cached_query(expiry=60)  # تخزين مؤقت لمدة دقيقة واحدة
    def get_dashboard_counts(user_id, is_admin):
        counts = {}

        if is_admin:
            # المسؤول يرى جميع النوادي والموظفين
            counts['clubs_count'] = Club.query.count()
            counts['critical_issues_count'] = 0  # سيتم استبدالها بعدد الأعطال الحرجة
            counts['employees_count'] = Employee.query.count()
        else:
            # المستخدم العادي يرى فقط النوادي والموظفين التابعين له
            user = User.query.get(user_id)

            # استخدام استعلام مباشر للحصول على النوادي المرتبطة بالمستخدم
            user_clubs_query = db.session.query(Club).join(
                user_clubs,
                (user_clubs.c.club_id == Club.id) & (user_clubs.c.user_id == user_id)
            ).all()

            counts['clubs_count'] = len(user_clubs_query)
            counts['critical_issues_count'] = 0  # سيتم استبدالها بعدد الأعطال الحرجة

            # الحصول على معرفات النوادي التابعة للمستخدم
            user_club_ids = [club.id for club in user_clubs_query]
            # التحقق من وجود نوادي مرتبطة بالمستخدم
            if user_club_ids:
                counts['employees_count'] = Employee.query.filter(Employee.club_id.in_(user_club_ids)).count()
            else:
                counts['employees_count'] = 0

        return counts

    # الحصول على الإحصائيات من التخزين المؤقت
    counts = get_dashboard_counts(current_user.id, current_user.is_admin)
    clubs_count = counts['clubs_count']
    critical_issues_count = counts['critical_issues_count']
    employees_count = counts['employees_count']

    # طباعة معلومات للتشخيص
    print(f"User: {current_user.name}, Clubs Count: {clubs_count}, Employees Count: {employees_count}")

    # قياس وقت التحميل
    load_time = time.time() - start_time
    print(f"Dashboard loaded in {load_time:.4f} seconds")

    # الحصول على الشهر الحالي بالعربية
    from datetime import datetime

    # قائمة بأسماء الأشهر بالعربية
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

    # الحصول على رقم الشهر الحالي (1-12)
    current_date = datetime.now()
    current_month_index = current_date.month - 1  # نقص 1 لأن الفهرس يبدأ من 0
    current_month_name = arabic_months[current_month_index]
    current_day = current_date.day  # اليوم الحالي من الشهر

    # مبيعات الشهر الحالي
    current_month = datetime.now().strftime('%Y-%m')
    monthly_sales = 0
    monthly_target = 0  # إضافة متغير لتخزين إجمالي التارجيت
    daily_sales_data = []
    target_daily_amount = 0

    try:
        # الحصول على جميع التارجت للشهر الحالي
        if current_user.is_admin:
            targets = SalesTarget.query.filter_by(month=current_month).all()
        else:
            # المستخدم العادي يرى فقط النوادي التابعة له
            user_club_ids = [club.id for club in current_user.clubs]
            targets = SalesTarget.query.filter(
                SalesTarget.month == current_month,
                SalesTarget.club_id.in_(user_club_ids)
            ).all() if user_club_ids else []

        # حساب إجمالي المبيعات والتارجيت للشهر الحالي
        for target in targets:
            monthly_sales += target.get_achieved_amount()
            monthly_target += target.target_amount  # إضافة قيمة التارجيت للمجموع
            target_daily_amount += target.get_daily_target()

        # الحصول على بيانات المبيعات اليومية للشهر الحالي
        # تهيئة مصفوفة لتخزين مجموع المبيعات لكل يوم
        daily_sales_data = [0] * current_day

        # الحصول على جميع المبيعات اليومية للشهر الحالي للنوادي المحددة
        year = current_date.year
        month = current_date.month
        for target in targets:
            for sale in target.daily_sales:
                sale_date = sale.sale_date
                if sale_date.year == year and sale_date.month == month and sale_date.day <= current_day:
                    # إضافة قيمة المبيعات لليوم المناسب في المصفوفة
                    daily_sales_data[sale_date.day - 1] += sale.amount

    except Exception as e:
        print(f"Error calculating sales data: {str(e)}")
        monthly_sales = 0
        monthly_target = 2000000  # قيمة افتراضية للتارجيت الشهري
        daily_sales_data = [0] * current_day
        target_daily_amount = 70000  # قيمة افتراضية للهدف اليومي

    # تنسيق المبلغ المالي بإضافة فواصل للآلاف
    formatted_sales = "{:,.0f}".format(monthly_sales)  # تنسيق المبلغ بفواصل للآلاف
    formatted_target = "{:,.0f}".format(monthly_target)  # تنسيق مبلغ التارجيت بفواصل للآلاف

    # حساب نسبة المبيعات من الهدف (للعرض في شريط التقدم)
    sales_percentage = min(100, int((monthly_sales / monthly_target) * 100)) if monthly_target > 0 else 0

    # إرسال البيانات إلى القالب
    camera_checks_count = {
        'amount': formatted_sales,
        'target_amount': formatted_target,
        'percentage': sales_percentage,
        'daily_sales': daily_sales_data,
        'target_daily_amount': target_daily_amount
    }

    # الحصول على عدد الأعطال الحرجة التي لم يتم إغلاقها
    # التحقق من وجود جدول الأعطال الحرجة
    try:
        # قائمة الحالات التي تعتبر مفتوحة (لم يتم إغلاقها)
        open_statuses = ['\u062a\u062e\u0637\u062a \u062a\u0627\u0631\u064a\u062e \u0627\u0644\u0627\u0633\u062a\u062d\u0642\u0627\u0642', '\u0645\u0639\u0644\u0642\u0629']

        if current_user.is_admin:
            # المسؤول يرى جميع الأعطال المفتوحة
            critical_issues_count = CriticalIssue.query.filter(CriticalIssue.status.in_(open_statuses)).count()
        else:
            # المستخدم العادي يرى فقط الأعطال المفتوحة المتعلقة بالنوادي التابعة له
            user_club_ids = [club.id for club in current_user.clubs]
            critical_issues_count = CriticalIssue.query.filter(
                CriticalIssue.club_id.in_(user_club_ids),
                CriticalIssue.status.in_(open_statuses)
            ).count() if user_club_ids else 0

        # طباعة معلومات للتشخيص
        print(f"User: {current_user.name}, Open Critical Issues Count: {critical_issues_count}")
    except Exception as e:
        # في حالة وجود خطأ (مثل عدم وجود الجدول)
        print(f"Error getting critical issues: {str(e)}")
        critical_issues_count = 0

    # الحصول على عدد المخالفات للشهر الحالي
    violations_count = 0
    camera_violations_count = 0
    try:
        # تحديد بداية ونهاية الشهر الحالي
        month_start = date(current_date.year, current_date.month, 1)
        month_end = date(current_date.year, current_date.month + 1, 1) if current_date.month < 12 else date(current_date.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        if current_user.is_admin:
            # المسؤول يرى جميع المخالفات
            violations_count = Violation.query.filter(
                Violation.violation_date >= month_start,
                Violation.violation_date <= month_end
            ).count()

            # حساب عدد مخالفات الكاميرات للشهر الحالي
            clubs = Club.query.all()
        else:
            # المستخدم العادي يرى فقط المخالفات المتعلقة بالنوادي التابعة له
            user_club_ids = [club.id for club in current_user.clubs]
            if user_club_ids:
                # الحصول على معرفات الموظفين في النوادي المتاحة للمستخدم
                employee_ids = [emp.id for club_id in user_club_ids for emp in Employee.query.filter_by(club_id=club_id).all()]
                if employee_ids:
                    violations_count = Violation.query.filter(
                        Violation.employee_id.in_(employee_ids),
                        Violation.violation_date >= month_start,
                        Violation.violation_date <= month_end
                    ).count()

            # حساب عدد مخالفات الكاميرات للشهر الحالي
            clubs = current_user.clubs

        # حساب عدد مخالفات الكاميرات للشهر الحالي
        for club in clubs:
            current_month_checks = CameraCheck.query.filter(
                CameraCheck.club_id == club.id,
                CameraCheck.check_date >= month_start,
                CameraCheck.check_date <= month_end
            ).all()

            for check in current_month_checks:
                if hasattr(check, 'violations_count'):
                    if check.violations_count and isinstance(check.violations_count, int):
                        camera_violations_count += check.violations_count
                    elif check.violations_count and check.violations_count.isdigit():
                        camera_violations_count += int(check.violations_count)

        # طباعة معلومات للتشخيص
        print(f"User: {current_user.name}, Violations Count for Current Month: {violations_count}")
        print(f"User: {current_user.name}, Camera Violations Count for Current Month: {camera_violations_count}")
    except Exception as e:
        # في حالة وجود خطأ
        print(f"Error getting violations count: {str(e)}")
        violations_count = 0
        camera_violations_count = 0

    return render_template('index.html',
                          title='لوحة التحكم',
                          clubs_count=clubs_count,
                          facilities_count=critical_issues_count,  # استخدام نفس المتغير للتوافق مع القالب
                          camera_checks_count=camera_checks_count,
                          employees_count=employees_count,
                          violations_count=violations_count,
                          camera_violations_count=camera_violations_count,
                          current_month_name=current_month_name,
                          current_day=current_day)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']  # الرقم الوظيفي
        password = request.form['password']

        try:
            # استخدام استعلام بسيط للتحقق من وجود المستخدم
            user = User.query.filter_by(username=username).first()

            if user is None or user.password != password:
                flash('الرقم الوظيفي أو كلمة المرور غير صحيحة')
                return redirect(url_for('login'))

            # تسجيل دخول المستخدم
            login_user(user)

            # توجيه المستخدم إلى الصفحة التالية
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)

        except Exception as e:
            print(f"خطأ في تسجيل الدخول: {str(e)}")
            flash('حدث خطأ أثناء تسجيل الدخول. الرجاء المحاولة مرة أخرى.')
            return redirect(url_for('login'))

    return render_template('login.html', title='تسجيل الدخول')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/user-profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    # إنشاء نموذج لتغيير كلمة المرور
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # التحقق من صحة كلمة المرور الحالية
        if current_user.password != current_password:
            flash('كلمة المرور الحالية غير صحيحة')
            return redirect(url_for('user_profile'))

        # التحقق من تطابق كلمة المرور الجديدة مع تأكيدها
        if new_password != confirm_password:
            flash('كلمة المرور الجديدة وتأكيدها غير متطابقين')
            return redirect(url_for('user_profile'))

        # تحديث كلمة المرور
        current_user.password = new_password
        db.session.commit()

        flash('تم تغيير كلمة المرور بنجاح')
        return redirect(url_for('user_profile'))

    return render_template('user_profile.html', title='بطاقة المستخدم')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']  # الرقم الوظيفي
        name = request.form['name']  # الاسم
        phone = request.form['phone']  # رقم الهاتف
        password = request.form['password']

        # التحقق من وجود الرقم الوظيفي مسبقاً
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('الرقم الوظيفي موجود بالفعل')
            return redirect(url_for('register'))

        # الحصول على النوادي المحددة
        club_ids = request.form.getlist('clubs')
        selected_clubs = []
        if club_ids:
            selected_clubs = Club.query.filter(Club.id.in_(club_ids)).all()

        # إنشاء مستخدم جديد
        user = User(username=username, name=name, phone=phone, password=password, is_admin=False)
        user.clubs = selected_clubs

        db.session.add(user)
        db.session.commit()

        flash('تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول')
        return redirect(url_for('login'))

    # الحصول على جميع النوادي
    clubs = Club.query.all()
    return render_template('register.html', title='إنشاء حساب جديد', clubs=clubs)

# مسارات إدارة المستخدمين
@app.route('/users')
@login_required
def users():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('manage_users'):
        flash('ليس لديك صلاحية لإدارة المستخدمين')
        return redirect(url_for('index'))

    # البحث والتصفية
    search_query = request.args.get('search', '')

    # البحث في المستخدمين
    if search_query:
        users = User.query.filter(
            User.username.contains(search_query) |
            User.name.contains(search_query) |
            User.phone.contains(search_query)
        ).all()
    else:
        users = User.query.all()

    return render_template('users/index.html',
                          title='المستخدمين',
                          users=users,
                          search_query=search_query)

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('manage_users'):
        flash('ليس لديك صلاحية لإدارة المستخدمين')
        return redirect(url_for('index'))

    # الحصول على جميع النوادي
    clubs = Club.query.all()

    if request.method == 'POST':
        username = request.form['username']  # الرقم الوظيفي
        name = request.form['name']  # الاسم
        phone = request.form['phone']  # رقم الهاتف
        password = request.form['password']
        role = request.form['role']  # الدور

        # التحقق من وجود الرقم الوظيفي مسبقاً
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('الرقم الوظيفي موجود بالفعل')
            return redirect(url_for('new_user'))

        # الحصول على النوادي المحددة
        club_ids = request.form.getlist('clubs')
        selected_clubs = []
        if club_ids:
            selected_clubs = Club.query.filter(Club.id.in_(club_ids)).all()

        # إنشاء مستخدم جديد
        is_admin = (role == 'admin')  # تعيين is_admin بناءً على الدور
        user = User(username=username, name=name, phone=phone, password=password, is_admin=is_admin, role=role)
        user.clubs = selected_clubs

        db.session.add(user)
        db.session.commit()

        flash('تم إضافة المستخدم بنجاح!')
        return redirect(url_for('users'))

    return render_template('users/new.html', title='إضافة مستخدم جديد', clubs=clubs)

@app.route('/users/<int:id>')
@login_required
def user_detail(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('view_users'):
        flash('ليس لديك صلاحية لعرض المستخدمين')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)
    return render_template('users/detail.html', title='تفاصيل المستخدم', user=user)

@app.route('/users/<int:id>/permissions', methods=['GET', 'POST'])
@login_required
def user_permissions(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('manage_user_permissions'):
        flash('ليس لديك صلاحية لإدارة صلاحيات المستخدمين')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    # الحصول على جميع الصلاحيات
    permissions = Permission.query.order_by(Permission.name).all()

    # الحصول على صلاحيات المستخدم الحالية
    user_permissions = user.permissions

    if request.method == 'POST':
        # الحصول على الصلاحيات المحددة
        permission_ids = request.form.getlist('permissions')

        # تحويل المعرفات إلى أرقام صحيحة
        permission_ids = [int(pid) for pid in permission_ids]

        # الحصول على الصلاحيات المحددة
        selected_permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()

        # تحديث صلاحيات المستخدم
        user.permissions = selected_permissions
        db.session.commit()

        flash('تم تحديث صلاحيات المستخدم بنجاح!')
        return redirect(url_for('user_detail', id=user.id))

    return render_template('users/permissions.html',
                          title='إدارة صلاحيات المستخدم',
                          user=user,
                          permissions=permissions,
                          user_permissions=user_permissions)

@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('manage_users'):
        flash('ليس لديك صلاحية لإدارة المستخدمين')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)
    clubs = Club.query.all()

    if request.method == 'POST':
        user.name = request.form['name']
        user.phone = request.form['phone']
        role = request.form['role']  # الدور

        # تحديث كلمة المرور إذا تم توفيرها
        password = request.form['password']
        if password:
            user.password = password

        # تحديث الدور وحالة المسؤول
        user.role = role
        user.is_admin = (role == 'admin')  # تعيين is_admin بناءً على الدور

        # تحديث النوادي المحددة
        club_ids = request.form.getlist('clubs')
        selected_clubs = []
        if club_ids:
            selected_clubs = Club.query.filter(Club.id.in_(club_ids)).all()
        user.clubs = selected_clubs

        db.session.commit()

        flash('تم تحديث بيانات المستخدم بنجاح!')
        return redirect(url_for('user_detail', id=user.id))

    return render_template('users/edit.html', title='تعديل بيانات المستخدم', user=user, clubs=clubs)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('manage_users'):
        flash('ليس لديك صلاحية لإدارة المستخدمين')
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    # لا يمكن حذف المستخدم الحالي
    if user.id == current_user.id:
        flash('لا يمكنك حذف حسابك الحالي')
        return redirect(url_for('user_detail', id=user.id))

    db.session.delete(user)
    db.session.commit()

    flash('تم حذف المستخدم بنجاح!')
    return redirect(url_for('users'))

# مسارات إدارة النوادي
@app.route('/clubs')
@login_required
def clubs():
    # لا نحتاج للتحقق من صلاحية العرض هنا - العرض متاح للجميع
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # التحقق مما إذا كان المستخدم مسؤولاً
    if current_user.is_admin:
        # المسؤول يرى جميع النوادي
        if search_query:
            clubs = Club.query.filter(
                Club.name.contains(search_query) |
                Club.location.contains(search_query) |
                Club.manager_name.contains(search_query)
            ).all()
        else:
            clubs = Club.query.all()
    else:
        # المستخدم العادي يرى فقط النوادي المحددة له
        if search_query:
            clubs = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id,
                (Club.name.contains(search_query) |
                Club.location.contains(search_query) |
                Club.manager_name.contains(search_query))
            ).all()
        else:
            clubs = current_user.clubs

    # طباعة معلومات للتشخيص
    print(f"User: {current_user.name}, Clubs Count: {len(clubs)}")
    for club in clubs:
        print(f"  - {club.name} (ID: {club.id})")

    return render_template('clubs/index.html',
                          title='النوادي',
                          clubs=clubs,
                          search_query=search_query)

@app.route('/clubs/new', methods=['GET', 'POST'])
@login_required
def new_club():
    # التحقق من صلاحية المستخدم لإضافة نادي جديد
    if not current_user.has_permission('add_club'):
        flash('ليس لديك صلاحية لإضافة نادي جديد')
        return redirect(url_for('clubs'))

    # الحصول على المرافق المستوردة من ملف إكسل فقط
    facilities = Facility.query.filter_by(is_imported=True).all()

    if request.method == 'POST':
        name = request.form['name']
        manager_name = request.form['manager_name']
        phone = request.form['phone']

        # إضافة قيمة افتراضية للموقع
        location = "غير محدد"

        club = Club(name=name, location=location, manager_name=manager_name, phone=phone)

        # إضافة المرافق المحددة
        facility_ids = request.form.getlist('facilities')
        if facility_ids:
            selected_facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            club.facilities = selected_facilities

        db.session.add(club)
        db.session.commit()

        # إضافة بنود المرافق للنادي
        if facility_ids:
            for facility_id in facility_ids:
                # الحصول على بنود المرفق
                facility_items = FacilityItem.query.filter_by(facility_id=facility_id).all()

                # إضافة كل بند للنادي
                for item in facility_items:
                    club_facility_item = ClubFacilityItem(
                        club_id=club.id,
                        facility_id=facility_id,
                        facility_item_id=item.id,
                        is_active=True  # تفعيل البند افتراضيًا
                    )
                    db.session.add(club_facility_item)

            db.session.commit()

        flash('تم إضافة النادي بنجاح!')
        return redirect(url_for('clubs'))

    return render_template('clubs/new.html', title='إضافة نادي جديد', facilities=facilities)

@app.route('/clubs/<int:id>')
@login_required
def club_detail(id):
    club = Club.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    # الحصول على جداول دوام الموظفين
    employee_schedules = EmployeeSchedule.query.filter_by(club_id=id).all()

    # إنشاء قاموس لتخزين جدول الدوام لكل موظف
    schedules_by_employee = {}
    for schedule in employee_schedules:
        schedules_by_employee[schedule.employee_id] = schedule

    # إضافة جدول الدوام لكل موظف
    for employee in club.employees:
        employee.schedule = schedules_by_employee.get(employee.id)

    return render_template('clubs/detail.html', title='تفاصيل النادي', club=club)

@app.route('/clubs/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_club(id):
    club = Club.query.get_or_404(id)

    # التحقق من صلاحية الوصول والتعديل
    if not current_user.has_permission('edit_club'):
        flash('ليس لديك صلاحية لتعديل النادي')
        return redirect(url_for('club_detail', id=id))

    # التحقق من أن النادي متاح للمستخدم
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    # الحصول على المرافق المستوردة من ملف إكسل فقط
    facilities = Facility.query.filter_by(is_imported=True).all()

    if request.method == 'POST':
        club.name = request.form['name']
        # لا نقوم بتغيير الموقع
        club.manager_name = request.form['manager_name']
        club.phone = request.form['phone']

        # تحديث المرافق المحددة
        facility_ids = request.form.getlist('facilities')

        # الحصول على المرافق الحالية للنادي
        current_facility_ids = [facility.id for facility in club.facilities]

        # المرافق التي تمت إزالتها
        removed_facility_ids = [fid for fid in current_facility_ids if str(fid) not in facility_ids]

        # حذف بنود المرافق التي تمت إزالتها
        if removed_facility_ids:
            ClubFacilityItem.query.filter(
                ClubFacilityItem.club_id == club.id,
                ClubFacilityItem.facility_id.in_(removed_facility_ids)
            ).delete(synchronize_session=False)

        # تحديث المرافق
        if facility_ids:
            selected_facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
            club.facilities = selected_facilities

            # المرافق الجديدة التي تمت إضافتها
            new_facility_ids = [int(fid) for fid in facility_ids if int(fid) not in current_facility_ids]

            # إضافة بنود المرافق الجديدة للنادي
            for facility_id in new_facility_ids:
                # الحصول على بنود المرفق
                facility_items = FacilityItem.query.filter_by(facility_id=facility_id).all()

                # إضافة كل بند للنادي
                for item in facility_items:
                    # التحقق من عدم وجود البند مسبقًا
                    existing = ClubFacilityItem.query.filter_by(
                        club_id=club.id,
                        facility_id=facility_id,
                        facility_item_id=item.id
                    ).first()

                    if not existing:
                        club_facility_item = ClubFacilityItem(
                            club_id=club.id,
                            facility_id=facility_id,
                            facility_item_id=item.id,
                            is_active=True  # تفعيل البند افتراضيًا
                        )
                        db.session.add(club_facility_item)
        else:
            # حذف جميع بنود المرافق المرتبطة بالنادي
            ClubFacilityItem.query.filter_by(club_id=club.id).delete()
            club.facilities = []

        db.session.commit()

        flash('تم تحديث بيانات النادي بنجاح!')
        return redirect(url_for('club_detail', id=club.id))

    return render_template('clubs/edit.html', title='تعديل بيانات النادي', club=club, facilities=facilities)

@app.route('/clubs/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_club(id):
    try:
        club = Club.query.get_or_404(id)

        # التحقق من صلاحية الحذف
        if not current_user.has_permission('delete_club'):
            flash('ليس لديك صلاحية لحذف النادي')
            return redirect(url_for('club_detail', id=id))

        # التحقق من أن النادي متاح للمستخدم
        if not current_user.is_admin and club not in current_user.clubs:
            flash('ليس لديك صلاحية للوصول إلى هذا النادي')
            return redirect(url_for('clubs'))

        # التحقق من عدم وجود موظفين مرتبطين بالنادي
        if club.employees:
            flash('لا يمكن حذف النادي لأنه يحتوي على موظفين')
            return redirect(url_for('club_detail', id=club.id))

        # حذف بنود المرافق المرتبطة بالنادي أولاً
        ClubFacilityItem.query.filter_by(club_id=id).delete()

        # حذف النادي
        db.session.delete(club)
        db.session.commit()

        flash('تم حذف النادي بنجاح!')
        return redirect(url_for('clubs'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف النادي: {str(e)}')
        return redirect(url_for('clubs'))

# التحقق من امتداد الملف
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/clubs/import_excel', methods=['GET', 'POST'])
@login_required
def import_clubs_excel():
    # التحقق من صلاحية المستخدم (فقط المسؤول يمكنه استيراد النوادي)
    if not current_user.is_admin:
        flash('ليس لديك صلاحية لاستيراد النوادي')
        return redirect(url_for('clubs'))
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من اختيار ملف
        if file.filename == '':
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        # التحقق من صحة امتداد الملف
        if file and allowed_file(file.filename):
            # تأمين اسم الملف وحفظه
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            try:
                # قراءة ملف إكسل
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = ['name', 'manager_name', 'phone']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'العمود {col} غير موجود في الملف')
                        return redirect(request.url)

                # إضافة النوادي إلى قاعدة البيانات
                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # التحقق من وجود النادي مسبقاً
                        existing_club = Club.query.filter_by(name=row['name']).first()

                        if existing_club:
                            # تحديث النادي الموجود
                            existing_club.manager_name = row['manager_name']
                            existing_club.phone = row['phone']
                        else:
                            # إنشاء نادي جديد
                            club = Club(
                                name=row['name'],
                                location="غير محدد",  # قيمة افتراضية للموقع
                                manager_name=row['manager_name'],
                                phone=row['phone']
                            )
                            db.session.add(club)

                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row {index}: {str(e)}")

                db.session.commit()
                flash(f'تم استيراد {success_count} نادي بنجاح. فشل استيراد {error_count} نادي.')
                return redirect(url_for('clubs'))

            except Exception as e:
                flash(f'حدث خطأ أثناء معالجة الملف: {str(e)}')
                return redirect(request.url)
        else:
            flash('نوع الملف غير مسموح. يرجى استخدام ملفات Excel (.xlsx, .xls) أو CSV (.csv)')
            return redirect(request.url)

    return render_template('clubs/import_excel.html', title='استيراد بيانات النوادي من إكسل')

@app.route('/download/club_template')
@login_required
def download_club_template():
    # إنشاء قالب إكسل للنوادي
    template_data = {
        'name': ['نادي الرياض', 'نادي جدة'],
        'manager_name': ['أحمد محمد', 'خالد عبدالله'],
        'phone': ['0501234567', '0551234567']
    }

    df = pd.DataFrame(template_data)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'club_template.xlsx')
    df.to_excel(template_path, index=False)

    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path='club_template.xlsx', as_attachment=True)

# مسارات إدارة المرافق
@app.route('/facilities')
@login_required
def facilities():
    # لا نحتاج للتحقق من صلاحية العرض هنا - العرض متاح للجميع
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # البحث في المرافق
    if search_query:
        facilities = Facility.query.filter(
            Facility.name.contains(search_query)
        ).all()
    else:
        facilities = Facility.query.all()

    return render_template('facilities/index.html',
                          title='المرافق',
                          facilities=facilities,
                          search_query=search_query)

@app.route('/facilities/new', methods=['GET', 'POST'])
@login_required
def new_facility():
    # التحقق من صلاحية المستخدم لإضافة مرفق
    if not current_user.has_permission('add_facility'):
        flash('ليس لديك صلاحية لإضافة مرفق جديد')
        return redirect(url_for('facilities'))
    if request.method == 'POST':
        name = request.form['name']

        facility = Facility(name=name, is_imported=False)  # المرافق المضافة يدوياً ليست مستوردة
        db.session.add(facility)
        db.session.commit()

        flash('تم إضافة المرفق بنجاح!')
        return redirect(url_for('facilities'))

    return render_template('facilities/new.html', title='إضافة مرفق جديد')

@app.route('/facilities/<int:id>')
@login_required
def facility_detail(id):
    facility = Facility.query.get_or_404(id)
    return render_template('facilities/detail.html', title='تفاصيل المرفق', facility=facility)

@app.route('/facilities/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_facility(id):
    # التحقق من صلاحية المستخدم لتعديل المرفق
    if not current_user.has_permission('edit_facility'):
        flash('ليس لديك صلاحية لتعديل المرفق')
        return redirect(url_for('facility_detail', id=id))

    facility = Facility.query.get_or_404(id)

    if request.method == 'POST':
        facility.name = request.form['name']

        db.session.commit()

        flash('تم تحديث بيانات المرفق بنجاح!')
        return redirect(url_for('facility_detail', id=facility.id))

    return render_template('facilities/edit.html', title='تعديل بيانات المرفق', facility=facility)

@app.route('/facilities/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_facility(id):
    # التحقق من صلاحية المستخدم لحذف المرفق
    if not current_user.has_permission('delete_facility'):
        flash('ليس لديك صلاحية لحذف المرفق')
        return redirect(url_for('facility_detail', id=id))

    try:
        facility = Facility.query.get_or_404(id)

        # التحقق من عدم وجود بنود مرتبطة بالمرفق
        if facility.items:
            flash('لا يمكن حذف المرفق لأنه يحتوي على بنود')
            return redirect(url_for('facility_detail', id=facility.id))

        db.session.delete(facility)
        db.session.commit()

        flash('تم حذف المرفق بنجاح!')
        return redirect(url_for('facilities'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المرفق: {str(e)}')
        return redirect(url_for('facilities'))

@app.route('/facilities/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_facility(id):
    # التحقق من صلاحية المستخدم لتعديل المرفق
    if not current_user.has_permission('edit_facility'):
        flash('ليس لديك صلاحية لتعديل حالة المرفق')
        return redirect(url_for('facility_detail', id=id))

    facility = Facility.query.get_or_404(id)
    facility.is_active = not facility.is_active
    db.session.commit()

    status = 'تفعيل' if facility.is_active else 'تعطيل'
    flash(f'تم {status} المرفق بنجاح!')
    return redirect(url_for('facility_detail', id=facility.id))

@app.route('/facilities/import_excel', methods=['GET', 'POST'])
@login_required
def import_facilities_excel():
    # التحقق من صلاحية المستخدم لإضافة مرفق
    if not current_user.has_permission('add_facility'):
        flash('ليس لديك صلاحية لاستيراد المرافق')
        return redirect(url_for('facilities'))
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من اختيار ملف
        if file.filename == '':
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        # التحقق من صحة امتداد الملف
        if file and allowed_file(file.filename):
            # تأمين اسم الملف وحفظه
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            try:
                # قراءة ملف إكسل
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = ['name']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'العمود {col} غير موجود في الملف')
                        return redirect(request.url)

                # إضافة المرافق إلى قاعدة البيانات
                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # التحقق من وجود المرفق مسبقاً
                        existing_facility = Facility.query.filter_by(name=row['name']).first()

                        if existing_facility:
                            # تحديث المرفق الموجود وتعيين قيمة الحقل الجديد
                            existing_facility.is_imported = True
                        else:
                            # إنشاء مرفق جديد
                            facility = Facility(
                                name=row['name'],
                                is_imported=True  # تعيين قيمة الحقل الجديد
                            )
                            db.session.add(facility)

                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row {index}: {str(e)}")

                db.session.commit()
                flash(f'تم استيراد {success_count} مرفق بنجاح. فشل استيراد {error_count} مرفق.')
                return redirect(url_for('facilities'))

            except Exception as e:
                flash(f'حدث خطأ أثناء معالجة الملف: {str(e)}')
                return redirect(request.url)
        else:
            flash('نوع الملف غير مسموح. يرجى استخدام ملفات Excel (.xlsx, .xls) أو CSV (.csv)')
            return redirect(request.url)

    return render_template('facilities/import_excel.html', title='استيراد بيانات المرافق من إكسل')

@app.route('/download/facility_template')
@login_required
def download_facility_template():
    # إنشاء قالب إكسل للمرافق
    template_data = {
        'name': ['مسبح', 'ملعب كرة قدم', 'صالة رياضية']
    }

    df = pd.DataFrame(template_data)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'facility_template.xlsx')
    df.to_excel(template_path, index=False)

    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path='facility_template.xlsx', as_attachment=True)

# مسارات إدارة بنود المرافق
@app.route('/facilities/<int:facility_id>/items')
@login_required
def facility_items(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    search_query = request.args.get('search', '')

    if search_query:
        items = FacilityItem.query.filter(
            FacilityItem.facility_id == facility_id,
            FacilityItem.name.contains(search_query)
        ).all()
    else:
        items = FacilityItem.query.filter_by(facility_id=facility_id).all()

    return render_template('facilities/items/index.html',
                          title=f'بنود {facility.name}',
                          facility=facility,
                          items=items,
                          search_query=search_query)

@app.route('/facilities/<int:facility_id>/items/new', methods=['GET', 'POST'])
@login_required
def new_facility_item(facility_id):
    facility = Facility.query.get_or_404(facility_id)

    if request.method == 'POST':
        name = request.form['name']

        item = FacilityItem(name=name, facility_id=facility_id)
        db.session.add(item)
        db.session.commit()

        flash('تم إضافة البند بنجاح!')
        return redirect(url_for('facility_items', facility_id=facility_id))

    return render_template('facilities/items/new.html',
                          title=f'إضافة بند جديد لـ {facility.name}',
                          facility=facility)

@app.route('/facilities/<int:facility_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_facility_item(facility_id, item_id):
    facility = Facility.query.get_or_404(facility_id)
    item = FacilityItem.query.get_or_404(item_id)

    if item.facility_id != facility_id:
        flash('البند غير موجود في هذا المرفق')
        return redirect(url_for('facility_items', facility_id=facility_id))

    if request.method == 'POST':
        item.name = request.form['name']
        db.session.commit()

        flash('تم تحديث بيانات البند بنجاح!')
        return redirect(url_for('facility_items', facility_id=facility_id))

    return render_template('facilities/items/edit.html',
                          title=f'تعديل بند في {facility.name}',
                          facility=facility,
                          item=item)

@app.route('/facilities/<int:facility_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_facility_item(facility_id, item_id):
    try:
        # التحقق من وجود المرفق والبند
        Facility.query.get_or_404(facility_id)  # للتحقق من وجود المرفق
        item = FacilityItem.query.get_or_404(item_id)

        if item.facility_id != facility_id:
            flash('البند غير موجود في هذا المرفق')
            return redirect(url_for('facility_items', facility_id=facility_id))

        db.session.delete(item)
        db.session.commit()

        flash('تم حذف البند بنجاح!')
        return redirect(url_for('facility_items', facility_id=facility_id))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف البند: {str(e)}')
        return redirect(url_for('facility_items', facility_id=facility_id))

@app.route('/facilities/<int:facility_id>/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_facility_item(facility_id, item_id):
    # التحقق من وجود المرفق والبند
    Facility.query.get_or_404(facility_id)  # للتحقق من وجود المرفق
    item = FacilityItem.query.get_or_404(item_id)

    if item.facility_id != facility_id:
        flash('البند غير موجود في هذا المرفق')
        return redirect(url_for('facility_items', facility_id=facility_id))

    item.is_active = not item.is_active
    db.session.commit()

    status = 'تفعيل' if item.is_active else 'تعطيل'
    flash(f'تم {status} البند بنجاح!')
    return redirect(url_for('facility_items', facility_id=facility_id))

@app.route('/facilities/<int:facility_id>/items/import_excel', methods=['GET', 'POST'])
@login_required
def import_facility_items_excel(facility_id):
    facility = Facility.query.get_or_404(facility_id)

    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من اختيار ملف
        if file.filename == '':
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        # التحقق من صحة امتداد الملف
        if file and allowed_file(file.filename):
            # تأمين اسم الملف وحفظه
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            try:
                # قراءة ملف إكسل
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = ['name']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'العمود {col} غير موجود في الملف')
                        return redirect(request.url)

                # إضافة بنود المرفق إلى قاعدة البيانات
                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # التحقق من وجود البند مسبقاً في نفس المرفق
                        existing_item = FacilityItem.query.filter_by(
                            name=row['name'],
                            facility_id=facility_id
                        ).first()

                        if not existing_item:
                            # إنشاء بند جديد
                            item = FacilityItem(
                                name=row['name'],
                                facility_id=facility_id
                            )
                            db.session.add(item)

                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row {index}: {str(e)}")

                db.session.commit()
                flash(f'تم استيراد {success_count} بند بنجاح. فشل استيراد {error_count} بند.')
                return redirect(url_for('facility_items', facility_id=facility_id))

            except Exception as e:
                flash(f'حدث خطأ أثناء معالجة الملف: {str(e)}')
                return redirect(request.url)
        else:
            flash('نوع الملف غير مسموح. يرجى استخدام ملفات Excel (.xlsx, .xls) أو CSV (.csv)')
            return redirect(request.url)

    return render_template('facilities/items/import_excel.html',
                          title=f'استيراد بنود {facility.name} من إكسل',
                          facility=facility)

@app.route('/download/facility_items_template')
@login_required
def download_facility_items_template():
    # إنشاء قالب إكسل لبنود المرافق
    template_data = {
        'name': ['كرسي', 'طاولة', 'منشفة']
    }

    df = pd.DataFrame(template_data)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'facility_items_template.xlsx')
    df.to_excel(template_path, index=False)

    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path='facility_items_template.xlsx', as_attachment=True)

# مسارات إدارة بنود المرافق الخاصة بالنادي
@app.route('/clubs/<int:club_id>/facilities')
@login_required
def club_facilities(club_id):
    club = Club.query.get_or_404(club_id)

    # الحصول على المرافق المرتبطة بالنادي
    facilities = club.facilities

    return render_template('clubs/facilities/index.html',
                          title=f'مرافق {club.name}',
                          club=club,
                          facilities=facilities)

@app.route('/clubs/<int:club_id>/facilities/<int:facility_id>/items')
@login_required
def club_facility_items(club_id, facility_id):
    club = Club.query.get_or_404(club_id)
    facility = Facility.query.get_or_404(facility_id)

    # التحقق من أن المرفق مرتبط بالنادي
    if facility not in club.facilities:
        flash('المرفق غير مرتبط بهذا النادي')
        return redirect(url_for('club_facilities', club_id=club_id))

    # الحصول على بنود المرفق الخاصة بالنادي
    club_facility_items = ClubFacilityItem.query.filter_by(
        club_id=club_id,
        facility_id=facility_id
    ).all()

    # الحصول على بنود المرفق التي لم يتم إضافتها بعد
    existing_item_ids = [item.facility_item_id for item in club_facility_items]
    available_items = FacilityItem.query.filter_by(facility_id=facility_id).filter(
        ~FacilityItem.id.in_(existing_item_ids) if existing_item_ids else True
    ).all()

    return render_template('clubs/facilities/items.html',
                          title=f'بنود {facility.name} في {club.name}',
                          club=club,
                          facility=facility,
                          club_facility_items=club_facility_items,
                          available_items=available_items)

@app.route('/clubs/<int:club_id>/facilities/<int:facility_id>/items/add', methods=['POST'])
@login_required
def add_club_facility_item(club_id, facility_id):
    club = Club.query.get_or_404(club_id)
    facility = Facility.query.get_or_404(facility_id)

    # التحقق من أن المرفق مرتبط بالنادي
    if facility not in club.facilities:
        flash('المرفق غير مرتبط بهذا النادي')
        return redirect(url_for('club_facilities', club_id=club_id))

    # الحصول على البنود المحددة
    item_ids = request.form.getlist('items')

    if not item_ids:
        flash('لم يتم تحديد أي بنود')
        return redirect(url_for('club_facility_items', club_id=club_id, facility_id=facility_id))

    # إضافة البنود المحددة للنادي
    for item_id in item_ids:
        item = FacilityItem.query.get(item_id)
        if item and item.facility_id == facility_id:
            # التحقق من عدم وجود البند مسبقاً
            existing = ClubFacilityItem.query.filter_by(
                club_id=club_id,
                facility_id=facility_id,
                facility_item_id=item_id
            ).first()

            if not existing:
                club_facility_item = ClubFacilityItem(
                    club_id=club_id,
                    facility_id=facility_id,
                    facility_item_id=item_id,
                    is_active=True
                )
                db.session.add(club_facility_item)

    db.session.commit()
    flash('تم إضافة البنود بنجاح!')
    return redirect(url_for('club_facility_items', club_id=club_id, facility_id=facility_id))

@app.route('/clubs/<int:club_id>/facilities/<int:facility_id>/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_club_facility_item(club_id, facility_id, item_id):
    club_facility_item = ClubFacilityItem.query.filter_by(
        club_id=club_id,
        facility_id=facility_id,
        facility_item_id=item_id
    ).first_or_404()

    club_facility_item.is_active = not club_facility_item.is_active
    db.session.commit()

    status = 'تفعيل' if club_facility_item.is_active else 'تعطيل'
    flash(f'تم {status} البند بنجاح!')
    return redirect(url_for('club_facility_items', club_id=club_id, facility_id=facility_id))

@app.route('/clubs/<int:club_id>/facilities/<int:facility_id>/items/<int:item_id>/remove', methods=['POST'])
@login_required
def remove_club_facility_item(club_id, facility_id, item_id):
    club_facility_item = ClubFacilityItem.query.filter_by(
        club_id=club_id,
        facility_id=facility_id,
        facility_item_id=item_id
    ).first_or_404()

    db.session.delete(club_facility_item)
    db.session.commit()

    flash('تم إزالة البند بنجاح!')
    return redirect(url_for('club_facility_items', club_id=club_id, facility_id=facility_id))

# مسارات إدارة الموظفين
@app.route('/employees')
@login_required
def employees():
    # لا نحتاج للتحقق من صلاحية العرض هنا - العرض متاح للجميع
    # البحث والتصفية
    search_query = request.args.get('search', '')
    club_filter = request.args.get('club', '')
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')

    # بناء الاستعلام
    query = Employee.query

    # التحقق مما إذا كان المستخدم مسؤولاً
    if not current_user.is_admin:
        # المستخدم العادي يرى فقط الموظفين التابعين للأندية المحددة له
        user_club_ids = [club.id for club in current_user.clubs]
        query = query.filter(Employee.club_id.in_(user_club_ids))

    # تطبيق البحث
    if search_query:
        query = query.filter(
            Employee.name.contains(search_query) |
            Employee.employee_id.contains(search_query) |
            Employee.position.contains(search_query) |
            Employee.role.contains(search_query)
        )

    # تطبيق فلتر النادي
    if club_filter and club_filter.isdigit():
        club_id = int(club_filter)
        # التحقق من أن النادي المحدد من ضمن النوادي المتاحة للمستخدم
        if current_user.is_admin or club_id in [club.id for club in current_user.clubs]:
            query = query.filter(Employee.club_id == club_id)

    # تطبيق فلتر الدور الوظيفي
    if role_filter:
        query = query.filter(Employee.role == role_filter)

    # تطبيق فلتر الحالة
    if status_filter:
        is_active = status_filter == 'active'
        query = query.filter(Employee.is_active == is_active)

    # الحصول على النتائج
    employees = query.all()

    # الحصول على قائمة النوادي للفلترة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # الحصول على قائمة الأدوار الوظيفية الفريدة
    roles = db.session.query(Employee.role).distinct().all()
    roles = [role[0] for role in roles]

    # طباعة معلومات للتشخيص
    print(f"User: {current_user.name}, Employees Count: {len(employees)}")
    if not current_user.is_admin:
        user_club_ids = [club.id for club in current_user.clubs]
        print(f"User Club IDs: {user_club_ids}")
        for employee in employees[:5]:  # عرض أول 5 موظفين فقط للتشخيص
            print(f"  - {employee.name} (ID: {employee.id}, Club ID: {employee.club_id})")

    return render_template('employees/index.html',
                          title='الموظفين',
                          employees=employees,
                          clubs=clubs,
                          roles=roles,
                          search_query=search_query,
                          club_filter=club_filter,
                          role_filter=role_filter,
                          status_filter=status_filter)

@app.route('/employees/<int:id>')
@login_required
def employee_detail(id):
    employee = Employee.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        # التحقق من أن الموظف ينتمي إلى نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
            return redirect(url_for('employees'))

    return render_template('employees/detail.html', title='تفاصيل الموظف', employee=employee)

@app.route('/employees/new', methods=['GET', 'POST'])
@login_required
def new_employee():
    # الحصول على قائمة النوادي المتاحة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # التحقق من وجود نوادي متاحة
    if not clubs:
        flash('لا يوجد لديك نوادي متاحة لإضافة موظفين')
        return redirect(url_for('employees'))

    if request.method == 'POST':
        # الحصول على بيانات النموذج
        employee_id = request.form['employee_id']
        name = request.form['name']
        position = request.form['position']
        role = request.form['role']
        phone = request.form['phone']
        club_id = request.form['club_id']
        is_active = 'is_active' in request.form

        # التحقق من عدم وجود رقم وظيفي مكرر
        existing_employee = Employee.query.filter_by(employee_id=employee_id).first()
        if existing_employee:
            flash('الرقم الوظيفي موجود بالفعل')
            return redirect(url_for('new_employee'))

        # إنشاء موظف جديد
        employee = Employee(
            employee_id=employee_id,
            name=name,
            position=position,
            role=role,
            phone=phone,
            club_id=club_id,
            is_active=is_active
        )

        db.session.add(employee)
        db.session.commit()

        # إذا كان الدور الوظيفي هو "مدير نادي"، قم بتحديث اسم المدير في النادي
        if role == 'مدير نادي':
            # الحصول على النادي المرتبط بالموظف
            club = Club.query.get(club_id)
            if club:
                # تحديث اسم مدير النادي
                club.manager_name = name
                db.session.commit()
                print(f"تم تحديث مدير النادي {club.name} إلى {name}")

        flash('تم إضافة الموظف بنجاح!')
        return redirect(url_for('employees'))

    return render_template('employees/new.html', title='إضافة موظف جديد', clubs=clubs)

@app.route('/employees/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        # التحقق من أن الموظف ينتمي إلى نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
            return redirect(url_for('employees'))

    # الحصول على قائمة النوادي المتاحة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    if request.method == 'POST':
        # الحصول على بيانات النموذج
        employee_id = request.form['employee_id']

        # التحقق من عدم وجود رقم وظيفي مكرر (إذا تم تغييره)
        if employee_id != employee.employee_id:
            existing_employee = Employee.query.filter_by(employee_id=employee_id).first()
            if existing_employee:
                flash('الرقم الوظيفي موجود بالفعل')
                return redirect(url_for('edit_employee', id=id))

        # تحديث بيانات الموظف
        employee.employee_id = employee_id
        employee.name = request.form['name']
        employee.position = request.form['position']

        # الحصول على الدور الوظيفي الجديد
        new_role = request.form['role']
        employee.role = new_role

        employee.phone = request.form['phone']
        employee.club_id = request.form['club_id']
        employee.is_active = 'is_active' in request.form

        # إذا كان الدور الوظيفي هو "مدير نادي"، قم بتحديث اسم المدير في النادي
        if new_role == 'مدير نادي':
            # الحصول على النادي المرتبط بالموظف
            club = Club.query.get(employee.club_id)
            if club:
                # تحديث اسم مدير النادي
                club.manager_name = employee.name
                print(f"تم تحديث مدير النادي {club.name} إلى {employee.name}")

        db.session.commit()

        flash('تم تحديث بيانات الموظف بنجاح!')
        return redirect(url_for('employee_detail', id=employee.id))

    return render_template('employees/edit.html', title='تعديل بيانات الموظف', employee=employee, clubs=clubs)

@app.route('/employees/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_employee(id):
    try:
        employee = Employee.query.get_or_404(id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            # التحقق من أن الموظف ينتمي إلى نادي متاح للمستخدم
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
                return redirect(url_for('employees'))

        db.session.delete(employee)
        db.session.commit()

        flash('تم حذف الموظف بنجاح!')
        return redirect(url_for('employees'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف الموظف: {str(e)}')
        return redirect(url_for('employees'))

@app.route('/employees/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_employee(id):
    employee = Employee.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        # التحقق من أن الموظف ينتمي إلى نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
            return redirect(url_for('employees'))

    employee.is_active = not employee.is_active
    db.session.commit()

    status = 'تفعيل' if employee.is_active else 'تعطيل'
    flash(f'تم {status} الموظف بنجاح!')
    return redirect(url_for('employee_detail', id=employee.id))

@app.route('/employees/import_excel', methods=['GET', 'POST'])
@login_required
def import_employees_excel():
    # التحقق من صلاحية المستخدم (فقط المسؤول يمكنه استيراد الموظفين)
    if not current_user.is_admin:
        flash('ليس لديك صلاحية لاستيراد الموظفين')
        return redirect(url_for('employees'))

    # قائمة لتخزين الأندية المتشابهة التي تم العثور عليها أثناء الاستيراد
    similar_clubs_found = []
    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من اختيار ملف
        if file.filename == '':
            flash('لم يتم اختيار ملف')
            return redirect(request.url)

        # التحقق من صحة امتداد الملف
        if file and allowed_file(file.filename):
            # تأمين اسم الملف وحفظه
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)

            try:
                # قراءة ملف إكسل
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)

                # التحقق من وجود الأعمدة المطلوبة
                required_columns = ['employee_id', 'name', 'position', 'role', 'club_id']
                for col in required_columns:
                    if col not in df.columns:
                        flash(f'العمود {col} غير موجود في الملف')
                        return redirect(request.url)

                # طباعة معلومات عن البيانات المستوردة
                print(f"Total rows in Excel: {len(df)}")
                print(f"Columns: {df.columns.tolist()}")
                print(f"First row sample: {df.iloc[0].to_dict() if not df.empty else 'No data'}")

                # تعديل أسماء الأعمدة لتتوافق مع النظام
                column_mapping = {
                    'Status': 'is_active',  # تغيير Status إلى is_active
                    'status': 'is_active',  # تغيير status إلى is_active
                    'CLUB_ID': 'club_id',   # تغيير CLUB_ID إلى club_id
                    'Club_id': 'club_id',   # تغيير Club_id إلى club_id
                    'EMPLOYEE_ID': 'employee_id',  # تغيير EMPLOYEE_ID إلى employee_id
                    'Employee_id': 'employee_id',  # تغيير Employee_id إلى employee_id
                    'NAME': 'name',         # تغيير NAME إلى name
                    'Name': 'name',         # تغيير Name إلى name
                    'POSITION': 'position', # تغيير POSITION إلى position
                    'Position': 'position', # تغيير Position إلى position
                    'ROLE': 'role',         # تغيير ROLE إلى role
                    'Role': 'role',         # تغيير Role إلى role
                    'PHONE': 'phone',       # تغيير PHONE إلى phone
                    'Phone': 'phone'        # تغيير Phone إلى phone
                }

                # طباعة أسماء الأعمدة قبل التغيير
                print(f"Original columns: {df.columns.tolist()}")

                # تطبيق التغييرات على أسماء الأعمدة
                df = df.rename(columns=column_mapping)

                # طباعة أسماء الأعمدة بعد التغيير
                print(f"Renamed columns: {df.columns.tolist()}")

                # تحويل قيم الحالة إلى قيم منطقية
                if 'is_active' in df.columns:
                    # تحويل القيم النصية إلى قيم منطقية
                    def convert_status(status):
                        if isinstance(status, bool):
                            return status
                        if isinstance(status, (int, float)):
                            return bool(status)
                        if isinstance(status, str):
                            status = status.lower().strip()
                            if status in ['true', 'yes', 'y', '1', 'active', 'نشط', 'مفعل']:
                                return True
                            elif status in ['false', 'no', 'n', '0', 'inactive', 'غير نشط', 'معطل']:
                                return False
                        # القيمة الافتراضية هي True
                        return True

                    # تطبيق التحويل على عمود is_active
                    df['is_active'] = df['is_active'].apply(convert_status)
                    print(f"Converted is_active values: {df['is_active'].tolist()[:5]}")

                # إضافة الموظفين إلى قاعدة البيانات
                success_count = 0
                error_count = 0

                for index, row in df.iterrows():
                    try:
                        # التحقق من وجود الموظف مسبقاً
                        existing_employee = Employee.query.filter_by(employee_id=row['employee_id']).first()



                        # التحقق من وجود النادي
                        try:
                            # محاولة الحصول على النادي باستخدام المعرف أو الاسم
                            club = None
                            club_id_value = row['club_id']

                            # محاولة الحصول على النادي باستخدام المعرف
                            if isinstance(club_id_value, (int, float)) or (isinstance(club_id_value, str) and club_id_value.isdigit()):
                                club_id = int(club_id_value)
                                club = Club.query.get(club_id)

                            # إذا لم يتم العثور على النادي، حاول البحث باستخدام الاسم
                            if not club and isinstance(club_id_value, str):
                                # إزالة كلمة "نادي" من بداية الاسم إذا وجدت
                                club_name = club_id_value
                                if club_name.startswith('نادي '):
                                    club_name = club_name[5:].strip()

                                # البحث عن النادي بالاسم المطابق تماماً أولاً
                                club = Club.query.filter(Club.name == club_name).first()

                                # إذا لم يتم العثور على النادي، نبحث عن النادي بالاسم المطابق تماماً مع إضافة "نادي" في البداية
                                if not club:
                                    club = Club.query.filter(Club.name == f"نادي {club_name}").first()

                                # إذا لم يتم العثور على النادي، نعرض قائمة بالأندية المتشابهة للاختيار
                                if not club:
                                    similar_clubs = Club.query.filter(Club.name.like(f'%{club_name}%')).all()
                                    if similar_clubs:
                                        print(f"Found similar clubs for '{club_name}':")
                                        for i, similar_club in enumerate(similar_clubs):
                                            print(f"  {i+1}. {similar_club.name} (ID: {similar_club.id})")

                                        # إضافة إلى قائمة الأندية المتشابهة
                                        similar_clubs_found.append({
                                            'original_name': club_name,
                                            'matched_club': similar_clubs[0].name,
                                            'matched_id': similar_clubs[0].id,
                                            'all_matches': [{'id': c.id, 'name': c.name} for c in similar_clubs]
                                        })

                                        # استخدام النادي الأول في القائمة مع تنبيه في السجل
                                        club = similar_clubs[0]
                                        print(f"Using first match: {club.name} (ID: {club.id})")

                                # إذا لم يتم العثور على النادي، قم بإنشاء نادي جديد
                                if not club:
                                    # إنشاء نادي جديد
                                    new_club = Club(
                                        name=club_name,
                                        location='',  # موقع فارغ
                                        manager_name='',  # اسم المدير فارغ
                                        phone=''  # رقم الهاتف فارغ
                                    )
                                    db.session.add(new_club)
                                    db.session.commit()  # حفظ النادي الجديد للحصول على معرفه

                                    print(f"Created new club: {club_name} with ID {new_club.id}")
                                    club = new_club

                            if not club:
                                print(f"Club not found and could not be created: {club_id_value}")
                                error_count += 1
                                continue

                            # استخدام معرف النادي الذي تم العثور عليه
                            club_id = club.id

                        except Exception as e:
                            print(f"Error finding club: {row['club_id']} - {str(e)}")
                            error_count += 1
                            continue

                        # الحصول على الدور الوظيفي
                        role = row['role']
                        name = row['name']

                        if existing_employee:
                            # تحديث الموظف الموجود
                            existing_employee.name = name
                            existing_employee.position = row['position']
                            existing_employee.role = role
                            existing_employee.phone = row.get('phone', '')
                            existing_employee.club_id = club_id
                            existing_employee.is_active = row.get('is_active', True)

                            # إذا كان الدور الوظيفي هو "مدير نادي"، قم بتحديث اسم المدير في النادي
                            if role == 'مدير نادي':
                                # الحصول على النادي المرتبط بالموظف
                                club = Club.query.get(club_id)
                                if club:
                                    # تحديث اسم مدير النادي
                                    club.manager_name = name
                                    print(f"تم تحديث مدير النادي {club.name} إلى {name}")
                        else:
                            # إنشاء موظف جديد
                            employee = Employee(
                                employee_id=row['employee_id'],
                                name=name,
                                position=row['position'],
                                role=role,
                                phone=row.get('phone', ''),
                                club_id=club_id,
                                is_active=row.get('is_active', True)
                            )
                            db.session.add(employee)

                            # إذا كان الدور الوظيفي هو "مدير نادي"، قم بتحديث اسم المدير في النادي
                            if role == 'مدير نادي':
                                # الحصول على النادي المرتبط بالموظف
                                club = Club.query.get(club_id)
                                if club:
                                    # تحديث اسم مدير النادي
                                    club.manager_name = name
                                    print(f"تم تحديث مدير النادي {club.name} إلى {name}")

                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error importing row {index}: {str(e)}")
                        # طباعة بيانات الصف الذي فشل استيراده
                        print(f"Row data: {row.to_dict()}")

                db.session.commit()

                # إعداد رسالة النجاح
                success_message = f'تم استيراد {success_count} موظف بنجاح. فشل استيراد {error_count} موظف.'

                # إذا كان هناك أندية متشابهة، نضيف تنبيهاً
                if similar_clubs_found:
                    flash(success_message, 'success')
                    flash('تم العثور على أندية متشابهة أثناء الاستيراد. يرجى مراجعة التفاصيل أدناه:', 'warning')
                    # تخزين قائمة الأندية المتشابهة في الجلسة
                    session['similar_clubs_found'] = similar_clubs_found
                    return redirect(url_for('show_similar_clubs'))
                else:
                    flash(success_message)
                    return redirect(url_for('employees'))

            except Exception as e:
                flash(f'حدث خطأ أثناء معالجة الملف: {str(e)}')
                return redirect(request.url)
        else:
            flash('نوع الملف غير مسموح. يرجى استخدام ملفات Excel (.xlsx, .xls) أو CSV (.csv)')
            return redirect(request.url)

    return render_template('employees/import_excel.html', title='استيراد بيانات الموظفين من إكسل')

@app.route('/download/employee_template')
@login_required
def download_employee_template():
    # إنشاء قالب إكسل للموظفين
    template_data = {
        'employee_id': ['EMP001', 'EMP002', 'EMP003', 'EMP004'],
        'name': ['محمد أحمد', 'خالد محمد', 'فاطمة علي', 'سارة محمد'],
        'position': ['مدرب', 'مدير نادي', 'موظف خدمة عملاء', 'عامل'],
        'role': ['مدرب سباحة', 'مدير نادي', 'خدمة عملاء', 'عامل نظافة'],
        'phone': ['0501111111', '0502222222', '0503333333', '0504444444'],
        'club_id': [1, 1, 2, 2],
        'is_active': [True, True, True, False]
    }

    df = pd.DataFrame(template_data)
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'employee_template.xlsx')
    df.to_excel(template_path, index=False)

    return send_from_directory(directory=app.config['UPLOAD_FOLDER'], path='employee_template.xlsx', as_attachment=True)

@app.route('/employees/similar_clubs')
@login_required
def show_similar_clubs():
    # التحقق من صلاحية المستخدم (فقط المسؤول يمكنه الوصول)
    if not current_user.is_admin:
        flash('ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect(url_for('employees'))

    # الحصول على قائمة الأندية المتشابهة من الجلسة
    similar_clubs = session.get('similar_clubs_found', [])

    # مسح البيانات من الجلسة بعد عرضها
    if 'similar_clubs_found' in session:
        session.pop('similar_clubs_found')

    return render_template('employees/similar_clubs.html',
                          title='الأندية المتشابهة',
                          similar_clubs=similar_clubs)

# مسارات API للتعامل مع طلبات AJAX
@app.route('/api/facilities/<int:facility_id>/toggle', methods=['POST'])
@login_required
def api_toggle_facility(facility_id):
    facility = Facility.query.get_or_404(facility_id)
    facility.is_active = not facility.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'is_active': facility.is_active,
        'message': 'تم تفعيل المرفق بنجاح' if facility.is_active else 'تم تعطيل المرفق بنجاح'
    })

@app.route('/api/facilities/<int:facility_id>/items/<int:item_id>/toggle', methods=['POST'])
@login_required
def api_toggle_facility_item(facility_id, item_id):
    item = FacilityItem.query.get_or_404(item_id)

    if item.facility_id != facility_id:
        return jsonify({
            'success': False,
            'message': 'البند غير موجود في هذا المرفق'
        }), 400

    item.is_active = not item.is_active
    db.session.commit()

    return jsonify({
        'success': True,
        'is_active': item.is_active,
        'message': 'تم تفعيل البند بنجاح' if item.is_active else 'تم تعطيل البند بنجاح'
    })



@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

















# متابعة الكاميرات
@app.route('/camera-checks')
@login_required
def camera_checks_list():
    # توجيه المستخدم إلى صفحة قائمة الأندية
    return redirect(url_for('camera_checks_clubs_list'))

@app.route('/camera-checks/clubs')
@login_required
def camera_checks_clubs_list():
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على قائمة الأندية المتاحة للمستخدم
    clubs = []
    if current_user.is_admin:
        if search_query:
            clubs_query = Club.query.filter(Club.name.contains(search_query))
        else:
            clubs_query = Club.query
    else:
        if search_query:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id,
                Club.name.contains(search_query)
            )
        else:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id
            )

    # تحديد بداية ونهاية الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    # اسم الشهر الحالي بالعربية
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    current_month_name = f"{arabic_months[today.month - 1]} {today.year}"

    for club in clubs_query.all():
        # عدد متابعات الكاميرات في النادي
        camera_checks = CameraCheck.query.filter_by(club_id=club.id).order_by(CameraCheck.check_date.desc()).all()
        club.camera_checks_count = len(camera_checks)

        # تاريخ آخر متابعة
        club.last_check_date = camera_checks[0].check_date if camera_checks else None

        # حساب عدد المخالفات المسجلة في الشهر الحالي
        current_month_violations = 0
        current_month_checks = CameraCheck.query.filter(
            CameraCheck.club_id == club.id,
            CameraCheck.check_date >= month_start,
            CameraCheck.check_date <= month_end
        ).all()

        for check in current_month_checks:
            if check.violations_count and check.violations_count.isdigit():
                current_month_violations += int(check.violations_count)
            elif isinstance(check.violations_count, int):
                current_month_violations += check.violations_count

        club.current_month_violations = current_month_violations

        clubs.append(club)

    return render_template('camera_checks/clubs_list.html',
                          title='سجل متابعة الكاميرات',
                          clubs=clubs,
                          search_query=search_query,
                          current_month_name=current_month_name)

@app.route('/camera-checks/club/<int:club_id>')
@login_required
def camera_checks_club_detail(club_id):
    # التحقق من وجود النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('camera_checks_clubs_list'))

    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على متابعات الكاميرات للنادي
    if search_query:
        # يمكن تطبيق البحث على حقول أخرى حسب الحاجة
        camera_checks = CameraCheck.query.filter(
            CameraCheck.club_id == club_id,
            CameraCheck.notes.contains(search_query)
        ).order_by(CameraCheck.check_date.desc()).all()
    else:
        camera_checks = CameraCheck.query.filter_by(club_id=club_id).order_by(CameraCheck.check_date.desc()).all()

    return render_template('camera_checks/club_detail.html',
                          title='متابعة كاميرات ' + club.name,
                          club=club,
                          camera_checks=camera_checks,
                          search_query=search_query)

@app.route('/camera-checks/new', methods=['GET', 'POST'])
@login_required
def new_camera_check():
    # الحصول على قائمة النوادي
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        # المستخدم العادي يرى فقط النوادي المحددة له
        clubs = current_user.clubs

    # طباعة معلومات للتشخيص
    print(f"User: {current_user.name}, Clubs Count: {len(clubs)}")
    for club in clubs:
        print(f"  - {club.name} (ID: {club.id})")

    # تحديد فترات المتابعة
    time_slots = ['12:00', '02:00', '03:00', '05:00', '08:00', '10:00', '11:00', '11:50']

    if request.method == 'POST':
        club_id = request.form.get('club_id')
        notes = request.form.get('notes', '')
        violations_count = request.form.get('violations_count', '')

        # إنشاء متابعة جديدة
        camera_check = CameraCheck(
            check_date=date.today(),
            club_id=club_id,
            user_id=current_user.id,
            notes=notes,
            violations_count=violations_count,
            status='active'  # تعيين قيمة لعمود status
        )

        db.session.add(camera_check)
        db.session.commit()

        # إضافة فترات المتابعة باستخدام SQL مباشرة
        import sqlite3
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        for time_slot in time_slots:
            is_working = 1 if request.form.get(f'time_slot_{time_slot}') == 'on' else 0
            cursor.execute(
                "INSERT INTO camera_time_slot (camera_check_id, time_slot, is_working) VALUES (?, ?, ?)",
                (camera_check.id, time_slot, is_working)
            )

        conn.commit()
        conn.close()

        flash('تم إضافة متابعة الكاميرات بنجاح!')
        return redirect(url_for('camera_checks_club_detail', club_id=club_id))

    return render_template('camera_checks/new.html',
                          title='متابعة كاميرات جديدة',
                          clubs=clubs,
                          time_slots=time_slots)

@app.route('/camera-checks/club/<int:club_id>/new', methods=['GET', 'POST'])
@login_required
def new_camera_check_for_club(club_id):
    # التحقق من وجود النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('camera_checks_clubs_list'))

    # تحديد فترات المتابعة
    time_slots = ['12:00', '02:00', '03:00', '05:00', '08:00', '10:00', '11:00', '11:50']

    if request.method == 'POST':
        notes = request.form.get('notes', '')
        violations_count = request.form.get('violations_count', 0)

        # إنشاء سجل متابعة جديد
        camera_check = CameraCheck(
            club_id=club_id,
            check_date=date.today(),  # استخدام تاريخ اليوم
            user_id=current_user.id,
            notes=notes,
            violations_count=violations_count,
            status='active'  # تعيين قيمة لعمود status
        )

        db.session.add(camera_check)
        db.session.commit()

        # إضافة فترات المتابعة باستخدام SQL مباشرة
        import sqlite3
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()

        for time_slot in time_slots:
            is_working = 1 if request.form.get(f'time_slot_{time_slot}') == 'on' else 0
            cursor.execute(
                "INSERT INTO camera_time_slot (camera_check_id, time_slot, is_working) VALUES (?, ?, ?)",
                (camera_check.id, time_slot, is_working)
            )

        conn.commit()
        conn.close()

        flash('تم إضافة متابعة الكاميرات بنجاح!')
        return redirect(url_for('camera_checks_club_detail', club_id=club_id))

    # الحصول على قائمة النوادي للقائمة المنسدلة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    return render_template('camera_checks/new.html',
                          title='متابعة كاميرات جديدة',
                          clubs=clubs,
                          selected_club_id=club_id,  # تمرير معرف النادي المحدد
                          time_slots=time_slots)

@app.route('/camera-checks/<int:id>')
@login_required
def camera_check_detail(id):
    # الحصول على بيانات المتابعة باستخدام SQL مباشرة
    camera_check = CameraCheck.query.get_or_404(id)

    # الحصول على فترات المتابعة باستخدام SQL مباشرة
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row  # للحصول على النتائج كقاموس
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, camera_check_id, time_slot, is_working FROM camera_time_slot WHERE camera_check_id = ? ORDER BY time_slot",
        (id,)
    )
    time_slots = cursor.fetchall()

    conn.close()

    return render_template('camera_checks/detail.html',
                          title='تفاصيل متابعة الكاميرات',
                          camera_check=camera_check,
                          time_slots=time_slots)

@app.route('/camera-checks/<int:id>/delete', methods=['POST'])
@login_required
def delete_camera_check(id):
    # الحصول على بيانات المتابعة
    camera_check = CameraCheck.query.get_or_404(id)
    club_id = camera_check.club_id

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and camera_check.club not in current_user.clubs:
        flash('ليس لديك صلاحية لحذف هذه المتابعة')
        return redirect(url_for('camera_checks_clubs_list'))

    try:
        # حذف فترات المتابعة أولاً (إذا كانت موجودة)
        import sqlite3
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM camera_time_slot WHERE camera_check_id = ?", (id,))
        conn.commit()
        conn.close()

        # حذف المتابعة
        db.session.delete(camera_check)
        db.session.commit()

        flash('تم حذف متابعة الكاميرات بنجاح!')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف متابعة الكاميرات: {str(e)}')

    return redirect(url_for('camera_checks_club_detail', club_id=club_id))

@app.route('/camera-checks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_camera_check(id):
    # الحصول على بيانات المتابعة
    camera_check = CameraCheck.query.get_or_404(id)

    # طباعة معلومات المتابعة للتشخيص
    print(f"Camera Check ID: {camera_check.id}")
    print(f"Club: {camera_check.club.name}")
    print(f"Date: {camera_check.check_date}")
    print(f"Violations Count: {camera_check.violations_count}")
    print(f"Notes: {camera_check.notes}")

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and camera_check.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذه المتابعة')
        return redirect(url_for('camera_checks_clubs_list'))

    # الحصول على فترات المتابعة باستخدام SQL مباشرة
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row  # للحصول على النتائج كقاموس
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, camera_check_id, time_slot, is_working FROM camera_time_slot WHERE camera_check_id = ? ORDER BY time_slot",
        (id,)
    )
    time_slots = cursor.fetchall()

    # التحقق من افتتاح النادي (الفترة الأولى)
    club_opening = False
    if time_slots and len(time_slots) > 0:
        club_opening = time_slots[0]['is_working'] == 1

    if request.method == 'POST':
        # تحديث بيانات المتابعة
        camera_check.notes = request.form.get('notes', '')
        camera_check.violations_count = request.form.get('violations_count', '')

        db.session.commit()

        # تحديث فترات المتابعة
        for time_slot in time_slots:
            is_working = 1 if request.form.get(f"time_slot_{time_slot['time_slot']}") == 'on' else 0
            cursor.execute(
                "UPDATE camera_time_slot SET is_working = ? WHERE id = ?",
                (is_working, time_slot['id'])
            )

        conn.commit()
        conn.close()

        flash('تم تحديث متابعة الكاميرات بنجاح!')
        return redirect(url_for('camera_checks_club_detail', club_id=camera_check.club_id))

    conn.close()

    return render_template('camera_checks/edit.html',
                          title='تعديل متابعة الكاميرات',
                          camera_check=camera_check,
                          time_slots=time_slots,
                          club_opening=club_opening)

@app.route('/camera-checks/<int:id>/delete-old', methods=['GET', 'POST'])
@login_required
def delete_camera_check_old(id):
    if request.method == 'GET':
        # عرض صفحة تأكيد الحذف
        camera_check = CameraCheck.query.get_or_404(id)
        return render_template('camera_checks/delete.html',
                            title='حذف متابعة الكاميرات',
                            camera_check=camera_check)
    else:  # POST request
        # حذف المتابعة مباشرة باستخدام SQL
        import sqlite3

        try:
            # فتح اتصال بقاعدة البيانات
            conn = sqlite3.connect('app.db')
            cursor = conn.cursor()

            # حذف فترات المتابعة أولاً
            cursor.execute("DELETE FROM camera_time_slot WHERE camera_check_id = ?", (id,))

            # حذف المتابعة نفسها
            cursor.execute("DELETE FROM camera_check WHERE id = ?", (id,))

            # حفظ التغييرات
            conn.commit()
            conn.close()

            flash('تم حذف متابعة الكاميرات بنجاح!')
        except Exception as e:
            flash('حدث خطأ أثناء حذف المتابعة!')
            print(f"خطأ في حذف المتابعة: {str(e)}")

        return redirect(url_for('camera_checks_clubs_list'))



# مسار لجلب مرافق النادي باستخدام AJAX
@app.route('/checks/get_club_facilities/<int:club_id>')
@login_required
def get_check_club_facilities(club_id):
    print(f"\n\n[DEBUG] تم استدعاء API لجلب مرافق النادي بمعرف: {club_id}\n\n")
    try:
        # التحقق من وجود النادي
        club = Club.query.get_or_404(club_id)
        print(f"[DEBUG] تم العثور على النادي: {club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and club not in current_user.clubs:
            print(f"[DEBUG] تم رفض الوصول للمستخدم: {current_user.username}")
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا النادي'}), 403

        # الحصول على المرافق النشطة للنادي
        club_facilities = club.facilities
        print(f"[DEBUG] تم العثور على {len(club_facilities)} مرفق للنادي")
        for facility in club_facilities:
            print(f"[DEBUG] مرفق: {facility.name} (معرف: {facility.id})")

        # الحصول على بنود المرافق للنادي
        club_facility_items_raw = ClubFacilityItem.query.filter_by(club_id=club_id).all()
        print(f"[DEBUG] تم العثور على {len(club_facility_items_raw)} بند مرفق للنادي")

        # إذا لم تكن هناك بنود مرافق للنادي، قم بإضافة بنود المرافق الافتراضية
        if len(club_facility_items_raw) == 0:
            # الحصول على جميع المرافق
            all_facilities = Facility.query.all()

            # إضافة المرافق للنادي
            for facility in all_facilities:
                if facility not in club.facilities:
                    club.facilities.append(facility)

            # حفظ التغييرات
            db.session.commit()

            # الحصول على جميع بنود المرافق
            all_facility_items = FacilityItem.query.all()

            # إضافة بنود المرافق للنادي
            for item in all_facility_items:
                # التحقق من أن البند ليس موجودًا بالفعل للنادي
                existing_item = ClubFacilityItem.query.filter_by(
                    club_id=club_id,
                    facility_id=item.facility_id,
                    facility_item_id=item.id
                ).first()

                if not existing_item:
                    club_facility_item = ClubFacilityItem(
                        club_id=club_id,
                        facility_id=item.facility_id,
                        facility_item_id=item.id,
                        is_active=True
                    )
                    db.session.add(club_facility_item)

            # حفظ التغييرات
            db.session.commit()

            # إعادة تحميل بنود المرافق للنادي
            club_facility_items_raw = ClubFacilityItem.query.filter_by(club_id=club_id).all()

        # الحصول على معلومات بنود المرافق
        club_facility_items = []
        for cfi in club_facility_items_raw:
            # الحصول على بند المرفق من قاعدة البيانات
            facility_item = FacilityItem.query.get(cfi.facility_item_id)
            if facility_item:
                # تعيين بند المرفق يدوياً
                cfi.facility_item = facility_item
                club_facility_items.append(cfi)

        # تنظيم بنود المرافق حسب المرفق
        facilities_data = []
        for facility in club_facilities:
            print(f"[DEBUG] جاري البحث عن بنود المرفق: {facility.name}")

            # الحصول على بنود المرفق مباشرة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()
            print(f"[DEBUG] تم العثور على {len(facility_items)} بند مباشر للمرفق")

            # إعداد قائمة البنود
            items = []

            # إضافة بنود المرفق مباشرة
            for item in facility_items:
                items.append({
                    'id': item.id,
                    'name': item.name,
                    'is_active': True
                })
                print(f"[DEBUG] تمت إضافة البند مباشرة: {item.name}")

            # إضافة بنود المرفق من جدول ClubFacilityItem
            for cfi in club_facility_items_raw:
                if cfi.facility_id == facility.id and cfi.is_active:
                    facility_item = FacilityItem.query.get(cfi.facility_item_id)
                    if facility_item and facility_item.is_active:
                        # التحقق من عدم وجود البند مسبقاً
                        item_exists = False
                        for item in items:
                            if item['id'] == facility_item.id:
                                item_exists = True
                                break

                        if not item_exists:
                            items.append({
                                'id': facility_item.id,
                                'name': facility_item.name,
                                'is_active': cfi.is_active
                            })
                            print(f"[DEBUG] تمت إضافة البند من ClubFacilityItem: {facility_item.name}")

            # إضافة المرفق دائماً حتى لو لم يكن لديه بنود
            facilities_data.append({
                'id': facility.id,
                'name': facility.name,
                'items': items,
                'items_count': len(items)
            })
            print(f"[DEBUG] تمت إضافة المرفق إلى الاستجابة: {facility.name} مع {len(items)} بند")

        print(f"[DEBUG] الاستجابة النهائية: {facilities_data}")
        import sys
        sys.stdout.flush()  # للتأكد من طباعة جميع السجلات
        return jsonify(facilities_data)
    except Exception as e:
        print(f"[ERROR] حدث خطأ في مسار API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'حدث خطأ أثناء جلب المرافق: {str(e)}'}), 500

# مسار لعرض مرافق النادي في صفحة HTML
@app.route('/checks/view_club_facilities/<int:club_id>')
def view_club_facilities(club_id):
    try:
        # التحقق من وجود النادي
        club = Club.query.get_or_404(club_id)

        # الحصول على المرافق النشطة للنادي
        club_facilities = club.facilities

        # الحصول على جميع بنود المرافق للنادي
        club_facility_items = []
        try:
            # استخدام استعلام SQL مباشر للحصول على بنود المرافق مع معلوماتها
            import sqlite3
            conn = sqlite3.connect('app.db')
            conn.row_factory = sqlite3.Row  # للحصول على النتائج كقاموس
            cursor = conn.cursor()

            # الحصول على بنود المرافق مع معلوماتها
            cursor.execute("""
                SELECT cfi.id, cfi.club_id, cfi.facility_id, cfi.facility_item_id, cfi.is_active,
                       fi.id as fi_id, fi.name as fi_name, fi.facility_id as fi_facility_id, fi.is_active as fi_is_active
                FROM club_facility_item as cfi
                JOIN facility_item as fi ON cfi.facility_item_id = fi.id
                WHERE cfi.club_id = ?
            """, (club_id,))

            # الحصول على النتائج
            results = cursor.fetchall()
            print(f"Found {len(results)} facility items for club {club.name} using direct SQL")

            # إنشاء قائمة بكائنات ClubFacilityItem مع معلوماتها
            for row in results:
                # إنشاء كائن ClubFacilityItem مع معلوماته
                cfi = ClubFacilityItem(
                    id=row['id'],
                    club_id=row['club_id'],
                    facility_id=row['facility_id'],
                    facility_item_id=row['facility_item_id'],
                    is_active=row['is_active']
                )

                # إنشاء كائن FacilityItem وربطه بكائن ClubFacilityItem
                fi = FacilityItem(
                    id=row['fi_id'],
                    name=row['fi_name'],
                    facility_id=row['fi_facility_id'],
                    is_active=row['fi_is_active']
                )
                cfi.facility_item = fi

                club_facility_items.append(cfi)

            # إغلاق الاتصال بقاعدة البيانات
            conn.close()

            print(f"Processed {len(club_facility_items)} facility items for club {club.name}")
        except Exception as e:
            print(f"Error loading club facility items: {str(e)}")

        # تنظيم بنود المرافق حسب المرفق
        facilities_with_items = {}
        for facility in club_facilities:
            items = [cfi for cfi in club_facility_items if cfi.facility_id == facility.id]
            if items:
                facilities_with_items[facility] = items

        return render_template('checks/view_facilities.html',
                              title=f'مرافق وبنود نادي {club.name}',
                              club=club,
                              facilities_with_items=facilities_with_items)
    except Exception as e:
        print(f"Error in view_club_facilities: {str(e)}")
        flash(f'حدث خطأ أثناء عرض مرافق النادي: {str(e)}')
        return redirect(url_for('checks_list'))

# مسارات التشيك
@app.route('/checks')
@login_required
def checks_list():
    # توجيه المستخدم إلى صفحة قائمة الأندية
    return redirect(url_for('checks_clubs_list'))

@app.route('/checks/clubs')
@login_required
def checks_clubs_list():
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على قائمة الأندية المتاحة للمستخدم
    if current_user.is_admin:
        if search_query:
            clubs = Club.query.filter(Club.name.contains(search_query)).all()
        else:
            clubs = Club.query.all()
    else:
        if search_query:
            clubs = [club for club in current_user.clubs if search_query.lower() in club.name.lower()]
        else:
            clubs = current_user.clubs

    # إضافة التاريخ الحالي لاستخدامه في القالب
    from datetime import datetime
    import locale

    # محاولة تعيين اللغة العربية للحصول على أسماء الشهور بالعربية
    try:
        locale.setlocale(locale.LC_TIME, 'ar_SA.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'ar_SA')
        except:
            try:
                locale.setlocale(locale.LC_TIME, 'ar')
            except:
                pass  # إذا فشلت جميع المحاولات، سنستخدم الأسماء العربية المحددة يدوياً

    now = datetime.now()
    current_month = now.month
    current_year = now.year

    # قائمة بأسماء الشهور بالعربية
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

    # الحصول على اسم الشهر الحالي بالعربية
    current_month_name = arabic_months[current_month - 1]  # نقص 1 لأن الفهرس يبدأ من 0

    print(f"[DEBUG] التاريخ الحالي: {now}, الشهر: {current_month} ({current_month_name}), السنة: {current_year}")

    # حساب متوسط النسبة لكل نادي مسبقاً
    clubs_with_stats = []
    for club in clubs:
        # حساب متوسط النسبة لجميع التشيكات
        all_total_percentage = 0
        all_count = 0
        current_total_percentage = 0
        current_count = 0

        for check in club.checks:
            percentage = check.get_compliance_percentage()
            all_total_percentage += percentage
            all_count += 1

            # التحقق من الشهر الحالي
            check_month = check.check_date.month
            check_year = check.check_date.year
            print(f"[DEBUG] تشيك لنادي {club.name}: تاريخ: {check.check_date}, شهر: {check_month}, سنة: {check_year}")

            if check_month == current_month and check_year == current_year:
                current_total_percentage += percentage
                current_count += 1
                print(f"[DEBUG] تمت إضافة التشيك للشهر الحالي")

        # حساب المتوسطات
        avg_percentage = round(all_total_percentage / all_count) if all_count > 0 else 0
        current_avg_percentage = round(current_total_percentage / current_count) if current_count > 0 else 0

        # إضافة الإحصائيات للنادي
        club.stats = {
            'all_count': all_count,
            'avg_percentage': avg_percentage,
            'current_count': current_count,
            'current_avg_percentage': current_avg_percentage
        }

        print(f"[DEBUG] إحصائيات نادي {club.name}: الكلي: {avg_percentage}%, الشهر الحالي: {current_avg_percentage}%")
        clubs_with_stats.append(club)

    return render_template('checks/clubs_list.html',
                          title='قائمة الأندية',
                          clubs=clubs_with_stats,
                          search_query=search_query,
                          now=now,
                          current_month=current_month,
                          current_year=current_year,
                          current_month_name=current_month_name)

@app.route('/checks/club/<int:club_id>')
@login_required
def checks_club_detail(club_id):
    # التحقق من وجود النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('checks_clubs_list'))

    # البحث والتصفية
    search_query = request.args.get('search', '')
    month_filter = request.args.get('month_filter', 'current')  # القيمة الافتراضية هي الشهر الحالي

    # إعداد قائمة الشهور العربية
    arabic_months = [
        (1, 'يناير'), (2, 'فبراير'), (3, 'مارس'), (4, 'إبريل'),
        (5, 'مايو'), (6, 'يونيو'), (7, 'يوليو'), (8, 'أغسطس'),
        (9, 'سبتمبر'), (10, 'أكتوبر'), (11, 'نوفمبر'), (12, 'ديسمبر')
    ]

    # الحصول على الشهر والسنة الحالية
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    current_month_name = arabic_months[current_month - 1][1]

    # تحديد الشهر المختار واسمه
    selected_month = month_filter
    selected_month_name = ""

    # إنشاء استعلام قاعدة البيانات الأساسي
    query = Check.query.filter(Check.club_id == club_id)

    # تطبيق فلتر البحث إذا وجد
    if search_query:
        query = query.filter(Check.notes.contains(search_query))

    # تطبيق فلتر الشهر
    if month_filter == 'current':
        # الشهر الحالي فقط
        start_date = datetime(current_year, current_month, 1)
        if current_month == 12:
            next_month_year = current_year + 1
            next_month = 1
        else:
            next_month_year = current_year
            next_month = current_month + 1
        end_date = datetime(next_month_year, next_month, 1) - timedelta(days=1)

        query = query.filter(Check.check_date.between(start_date, end_date))
        selected_month_name = current_month_name
    elif month_filter != 'all':
        # شهر محدد
        try:
            selected_month_num = int(month_filter)
            if 1 <= selected_month_num <= 12:
                # تحديد السنة بناءً على الشهر المختار (إذا كان الشهر المختار أكبر من الشهر الحالي، فهو من السنة الماضية)
                selected_year = current_year
                if selected_month_num > current_month:
                    selected_year -= 1

                start_date = datetime(selected_year, selected_month_num, 1)
                if selected_month_num == 12:
                    next_month_year = selected_year + 1
                    next_month = 1
                else:
                    next_month_year = selected_year
                    next_month = selected_month_num + 1
                end_date = datetime(next_month_year, next_month, 1) - timedelta(days=1)

                query = query.filter(Check.check_date.between(start_date, end_date))
                selected_month_name = arabic_months[selected_month_num - 1][1]
        except ValueError:
            # في حالة حدوث خطأ، نعود إلى الشهر الحالي
            month_filter = 'current'
            start_date = datetime(current_year, current_month, 1)
            if current_month == 12:
                next_month_year = current_year + 1
                next_month = 1
            else:
                next_month_year = current_year
                next_month = current_month + 1
            end_date = datetime(next_month_year, next_month, 1) - timedelta(days=1)

            query = query.filter(Check.check_date.between(start_date, end_date))
            selected_month_name = current_month_name

    # ترتيب النتائج حسب التاريخ تنازليًا
    checks = query.order_by(Check.check_date.desc()).all()

    return render_template('checks/club_detail.html',
                          title=f'تشيكات نادي {club.name}',
                          club=club,
                          checks=checks,
                          search_query=search_query,
                          selected_month=month_filter,
                          selected_month_name=selected_month_name,
                          current_month_name=current_month_name,
                          months=arabic_months)

@app.route('/checks/new', methods=['GET', 'POST'])
@login_required
def new_check():
    # الحصول على قائمة النوادي
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # الحصول على النادي المحدد من الطلب
    selected_club_id = request.args.get('club_id')
    print(f"\n\n[DEBUG] Selected club ID from request: {selected_club_id}\n\n")
    selected_club = None
    facilities_data = []

    # إذا تم تحديد نادي، قم بجلب المرافق والبنود
    if selected_club_id:
        try:
            selected_club_id = int(selected_club_id)
            selected_club = Club.query.get(selected_club_id)

            # التحقق من صلاحية الوصول
            if selected_club and (current_user.is_admin or selected_club in current_user.clubs):
                # الحصول على مرافق النادي
                club_facilities = list(selected_club.facilities)

                # إذا لم يكن للنادي أي مرافق، قم بإضافة جميع المرافق النشطة
                if len(club_facilities) == 0:
                    all_facilities = Facility.query.filter_by(is_active=True).all()
                    for facility in all_facilities:
                        selected_club.facilities.append(facility)
                    db.session.commit()
                    club_facilities = list(selected_club.facilities)

                # معالجة كل مرفق
                for facility in club_facilities:
                    # الحصول على بنود المرفق النشطة
                    facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

                    # إعداد قائمة البنود
                    items = []
                    for item in facility_items:
                        # التحقق من حالة البند في جدول ClubFacilityItem
                        club_facility_item = ClubFacilityItem.query.filter_by(
                            club_id=selected_club_id,
                            facility_id=facility.id,
                            facility_item_id=item.id
                        ).first()

                        # إضافة البند فقط إذا كان نشطًا في جدول ClubFacilityItem أو إذا لم يكن موجودًا
                        if club_facility_item is None or club_facility_item.is_active:
                            items.append({
                                'id': item.id,
                                'name': item.name
                            })

                    # إضافة المرفق دائماً حتى لو لم يكن لديه بنود
                    facility_data = {
                        'id': facility.id,
                        'name': facility.name,
                        'facility_items': items,
                        'items_count': len(items)
                    }
                    facilities_data.append(facility_data)
        except Exception as e:
            print(f"Error loading club facilities: {str(e)}")
            import traceback
            traceback.print_exc()

    if request.method == 'POST':
        club_id = request.form.get('club_id')
        notes = request.form.get('notes', '')

        print(f"\n\n[DEBUG] POST request received with club_id: {club_id}\n\n")

        # التحقق من وجود النادي
        if not club_id:
            flash('يرجى اختيار النادي أولاً')
            return redirect(url_for('new_check'))

        # التحقق من وجود تشيك لنفس النادي في نفس اليوم
        today = date.today()
        try:
            club_id = int(club_id)  # تحويل معرف النادي إلى رقم صحيح
            existing_check = Check.query.filter_by(club_id=club_id, check_date=today).first()
            if existing_check:
                flash(f'يوجد بالفعل تشيك لهذا النادي لهذا اليوم')
                return redirect(url_for('check_detail', id=existing_check.id))
        except Exception as e:
            print(f"خطأ في التحقق من وجود تشيك: {str(e)}")
            flash('حدث خطأ أثناء التحقق من وجود تشيك سابق')
            return redirect(url_for('new_check'))

        # التحقق من وجود بنود للتشيك
        has_items = False
        for key in request.form.keys():
            if key.startswith('item_'):
                has_items = True
                break

        # إذا لم تكن هناك بنود، قم بتوجيه المستخدم إلى صفحة جلب المرافق
        if not has_items:
            # إذا لم تكن هناك بنود، قم بتوجيه المستخدم إلى صفحة جلب المرافق
            return redirect(url_for('new_check', club_id=club_id))

        # إذا كانت هناك بنود، قم بإنشاء تشيك جديد
        try:
            check = Check(
                check_date=today,
                club_id=club_id,
                user_id=current_user.id,
                notes=notes
            )

            db.session.add(check)
            db.session.commit()
            print(f"تم إنشاء تشيك جديد برقم {check.id}")
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في إنشاء التشيك: {str(e)}")
            flash('حدث خطأ أثناء إنشاء التشيك. يرجى المحاولة مرة أخرى.')
            return redirect(url_for('new_check'))

        # الحصول على بنود المرافق المرسلة من النموذج
        try:
            for key in request.form.keys():
                if key.startswith('item_'):
                    # استخراج معرف بند المرفق من اسم الحقل
                    item_id = int(key.split('_')[1])
                    facility_item = FacilityItem.query.get(item_id)

                    if facility_item:
                        # التحقق مما إذا كان البند مطابقًا أم لا
                        is_compliant = request.form.get(key) == 'on'

                        # الحصول على الملاحظات لهذا البند
                        notes_key = f'notes_{item_id}'
                        item_notes = request.form.get(notes_key, '')

                        # إنشاء بند تشيك جديد
                        check_item = CheckItem(
                            check_id=check.id,
                            facility_id=facility_item.facility_id,
                            facility_item_id=item_id,
                            is_compliant=is_compliant,
                            notes=item_notes
                        )

                        db.session.add(check_item)
                        db.session.flush()  # للحصول على معرف البند الجديد

                        # معالجة الصور المرفقة لهذا البند
                        image_key = f'image_{item_id}'
                        if image_key in request.files:
                            image_file = request.files[image_key]
                            if image_file and image_file.filename:
                                try:
                                    # التحقق من نوع الملف (صورة)
                                    if image_file.content_type.startswith('image/'):
                                        # تأمين اسم الملف وحفظه
                                        filename = secure_filename(image_file.filename)
                                        unique_filename = f"{uuid.uuid4()}_{filename}"
                                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                                        image_file.save(file_path)

                                        # إنشاء صورة بند تشيك جديدة
                                        check_item_image = CheckItemImage(
                                            check_item_id=check_item.id,
                                            image_path=unique_filename
                                        )

                                        db.session.add(check_item_image)
                                        print(f"تم حفظ الصورة: {unique_filename}")
                                except Exception as img_error:
                                    print(f"خطأ في حفظ الصورة: {str(img_error)}")
                                    # لا نريد أن تفشل العملية بأكملها بسبب خطأ في الصورة
                                    pass
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في إضافة بنود التشيك: {str(e)}")
            flash('حدث خطأ أثناء إضافة بنود التشيك. يرجى المحاولة مرة أخرى.')
            return redirect(url_for('new_check'))

        try:
            db.session.commit()
            print("تم حفظ التشيك وبنوده بنجاح")

            # إعادة تحميل التشيك للتأكد من تحديث البيانات
            db.session.refresh(check)

            flash('تم إضافة التشيك بنجاح!')
            return redirect(url_for('checks_list'))
        except Exception as e:
            db.session.rollback()
            print(f"خطأ في حفظ التشيك النهائي: {str(e)}")
            flash('حدث خطأ أثناء حفظ التشيك. يرجى المحاولة مرة أخرى.')
            return redirect(url_for('new_check'))

    return render_template('checks/new.html',
                          title='تشيك جديد',
                          clubs=clubs,
                          selected_club=selected_club,
                          facilities_data=facilities_data)

@app.route('/checks/<int:id>')
@login_required
def check_detail(id):
    check = Check.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and check.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التشيك')
        return redirect(url_for('checks_list'))

    # الحصول على جميع المرافق والبنود المتاحة للنادي
    club = check.club
    club_facilities = list(club.facilities)

    # قاموس لتخزين البنود الحالية للتشيك للرجوع إليها لاحقًا
    check_items_dict = {}
    print(f"\n\n[DEBUG] Check ID: {check.id}, Total items: {len(check.items)}")
    for check_item in check.items:
        check_items_dict[check_item.facility_item_id] = check_item
        print(f"[DEBUG] Check item {check_item.id} for facility item {check_item.facility_item_id}: is_compliant={check_item.is_compliant}, notes='{check_item.notes}'")

    # تنظيم المرافق والبنود
    facilities_with_items = {}

    # معالجة كل مرفق
    for facility in club_facilities:
        # الحصول على بنود المرفق النشطة
        facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

        # إنشاء قائمة البنود لهذا المرفق
        items_list = []

        # معالجة كل بند مرفق
        for facility_item in facility_items:
            # التحقق مما إذا كان البند موجودًا في التشيك
            if facility_item.id in check_items_dict:
                # إذا كان البند موجودًا، استخدم بيانات التشيك الحالية
                items_list.append(check_items_dict[facility_item.id])
            else:
                # إذا لم يكن البند موجودًا، قم بإنشاء كائن مؤقت
                temp_item = type('obj', (object,), {
                    'facility_item': facility_item,
                    'facility_item_id': facility_item.id,
                    'is_compliant': False,
                    'notes': '',
                    'images': []
                })
                items_list.append(temp_item)

        # إضافة المرفق وبنوده إلى القاموس
        if items_list:
            facilities_with_items[facility] = items_list

    # حساب إحصائيات التشيك باستخدام الدوال الجديدة
    total_items = check.get_total_items_count()
    compliant_items = check.get_compliant_items_count()
    non_compliant_items = total_items - compliant_items
    compliance_percentage = check.get_compliance_percentage()

    return render_template('checks/detail.html',
                          title='تفاصيل التشيك',
                          check=check,
                          facilities_with_items=facilities_with_items,
                          total_items=total_items,
                          compliant_items=compliant_items,
                          non_compliant_items=non_compliant_items,
                          compliance_percentage=compliance_percentage)

@app.route('/checks/<int:id>/print')
@login_required
def check_print(id):
    check = Check.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and check.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التشيك')
        return redirect(url_for('checks_list'))

    # الحصول على جميع المرافق والبنود المتاحة للنادي
    club = check.club
    club_facilities = list(club.facilities)

    # قاموس لتخزين البنود الحالية للتشيك للرجوع إليها لاحقًا
    check_items_dict = {}
    for check_item in check.items:
        check_items_dict[check_item.facility_item_id] = check_item

    # تنظيم المرافق والبنود
    facilities_with_items = {}

    # معالجة كل مرفق
    for facility in club_facilities:
        # الحصول على بنود المرفق النشطة
        facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

        # إنشاء قائمة البنود لهذا المرفق
        items_list = []

        # معالجة كل بند مرفق
        for facility_item in facility_items:
            # التحقق مما إذا كان البند موجودًا في التشيك
            if facility_item.id in check_items_dict:
                # إذا كان البند موجودًا، استخدم بيانات التشيك الحالية
                items_list.append(check_items_dict[facility_item.id])
            else:
                # إذا لم يكن البند موجودًا، قم بإنشاء كائن مؤقت
                temp_item = type('obj', (object,), {
                    'facility_item': facility_item,
                    'facility_item_id': facility_item.id,
                    'is_compliant': False,
                    'notes': '',
                    'images': []
                })
                items_list.append(temp_item)

        # إضافة المرفق وبنوده إلى القاموس
        if items_list:
            facilities_with_items[facility] = items_list

    # حساب إحصائيات التشيك باستخدام الدوال الجديدة
    total_items = check.get_total_items_count()
    compliant_items = check.get_compliant_items_count()
    non_compliant_items = total_items - compliant_items
    compliance_percentage = check.get_compliance_percentage()

    return render_template('checks/print.html',
                          title='طباعة التشيك',
                          check=check,
                          facilities_with_items=facilities_with_items,
                          total_items=total_items,
                          compliant_items=compliant_items,
                          non_compliant_items=non_compliant_items,
                          compliance_percentage=compliance_percentage)

@app.route('/checks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_check(id):
    check = Check.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and check.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التشيك')
        return redirect(url_for('checks_list'))

    if request.method == 'POST':
        # تحديث ملاحظات التشيك
        check.notes = request.form.get('notes', '')

        # الحصول على جميع المرافق والبنود المتاحة للنادي
        club = check.club
        club_facilities = list(club.facilities)

        # قاموس لتخزين البنود الحالية للتشيك للرجوع إليها لاحقًا
        check_items_dict = {}
        for check_item in check.items:
            check_items_dict[check_item.facility_item_id] = check_item

        # معالجة كل مرفق
        for facility in club_facilities:
            # الحصول على بنود المرفق النشطة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

            for facility_item in facility_items:
                item_key = f'item_{facility_item.id}'
                notes_key = f'notes_{facility_item.id}'

                # التحقق مما إذا كان البند موجودًا في التشيك الحالي
                if facility_item.id in check_items_dict:
                    # تحديث البند الموجود
                    check_item = check_items_dict[facility_item.id]

                    # تحديث حالة المطابقة
                    check_item.is_compliant = request.form.get(item_key) == 'on'

                    # تحديث الملاحظات
                    check_item.notes = request.form.get(notes_key, '')
                else:
                    # إنشاء بند جديد
                    is_compliant = request.form.get(item_key) == 'on'
                    notes = request.form.get(notes_key, '')

                    # إنشاء بند تشيك جديد
                    new_check_item = CheckItem(
                        check_id=check.id,
                        facility_id=facility.id,
                        facility_item_id=facility_item.id,
                        is_compliant=is_compliant,
                        notes=notes
                    )
                    db.session.add(new_check_item)
                    db.session.flush()  # للحصول على معرف البند الجديد
                    check_item = new_check_item

                # معالجة الصور المرفقة لهذا البند
                image_key = f'image_{facility_item.id}'
                if image_key in request.files:
                    image_file = request.files[image_key]
                    if image_file and image_file.filename:
                        try:
                            # التحقق من نوع الملف (صورة)
                            if image_file.content_type.startswith('image/'):
                                # تأمين اسم الملف وحفظه
                                filename = secure_filename(image_file.filename)
                                unique_filename = f"{uuid.uuid4()}_{filename}"
                                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                                image_file.save(file_path)

                                # إنشاء صورة بند تشيك جديدة
                                check_item_image = CheckItemImage(
                                    check_item_id=check_item.id,
                                    image_path=unique_filename
                                )

                                db.session.add(check_item_image)
                                print(f"تم حفظ الصورة: {unique_filename}")
                        except Exception as img_error:
                            print(f"خطأ في حفظ الصورة: {str(img_error)}")
                            # لا نريد أن تفشل العملية بأكملها بسبب خطأ في الصورة
                            pass

        db.session.commit()

        # إعادة تحميل التشيك للتأكد من تحديث البيانات
        db.session.refresh(check)

        flash('تم تحديث التشيك بنجاح!')
        return redirect(url_for('checks_list'))

    # الحصول على جميع المرافق والبنود المتاحة للنادي
    club = check.club
    club_facilities = list(club.facilities)

    # قاموس لتخزين البنود الحالية للتشيك للرجوع إليها لاحقًا
    check_items_dict = {}
    for check_item in check.items:
        check_items_dict[check_item.facility_item_id] = check_item

    # تنظيم المرافق والبنود
    facilities_with_items = {}

    # معالجة كل مرفق
    for facility in club_facilities:
        # الحصول على بنود المرفق النشطة
        facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()

        # إنشاء قائمة البنود لهذا المرفق
        items_list = []

        for facility_item in facility_items:
            # التحقق مما إذا كان البند موجودًا في التشيك الحالي
            if facility_item.id in check_items_dict:
                # إذا كان البند موجودًا، استخدم بيانات التشيك الحالية
                items_list.append(check_items_dict[facility_item.id])
            else:
                # إذا لم يكن البند موجودًا، قم بإنشاء كائن مؤقت
                temp_item = type('obj', (object,), {
                    'facility_item': facility_item,
                    'facility_item_id': facility_item.id,
                    'is_compliant': False,
                    'notes': '',
                    'images': []
                })
                items_list.append(temp_item)

        # إضافة المرفق وبنوده إلى القاموس
        if items_list:
            facilities_with_items[facility] = items_list

    return render_template('checks/edit.html',
                          title='تعديل التشيك',
                          check=check,
                          facilities_with_items=facilities_with_items)

@app.route('/checks/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_check(id):
    check = Check.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and check.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التشيك')
        return redirect(url_for('checks_list'))

    if request.method == 'GET':
        # عرض صفحة تأكيد الحذف
        return render_template('checks/delete.html',
                              title='حذف التشيك',
                              check=check)
    else:  # POST request
        # حذف التشيك وجميع بنوده وصوره
        db.session.delete(check)
        db.session.commit()

        flash('تم حذف التشيك بنجاح!')
        return redirect(url_for('checks_list'))

@app.route('/api/checks/get_club_facilities/<int:club_id>')
@login_required
def get_club_facilities_for_check(club_id):
    print("\n\n[DEBUG] API CALLED WITH CLUB ID:", club_id, "\n\n")
    try:
        print(f"\n\n[DEBUG] API call for club_id: {club_id}")
        # التحقق من وجود النادي
        club = Club.query.get_or_404(club_id)
        print(f"[DEBUG] Found club: {club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and club not in current_user.clubs:
            print(f"[DEBUG] Access denied for user: {current_user.username}")
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا النادي'}), 403

        # الحصول على المرافق النشطة للنادي
        club_facilities = club.facilities
        print(f"[DEBUG] Found {len(club_facilities)} facilities for club")
        for facility in club_facilities:
            print(f"[DEBUG] Facility: {facility.name} (ID: {facility.id})")

        # الحصول على بنود المرافق النشطة للنادي
        club_facility_items = ClubFacilityItem.query.filter_by(club_id=club_id, is_active=True).all()
        print(f"[DEBUG] Found {len(club_facility_items)} club facility items")

        # تنظيم البيانات للإرجاع
        facilities_data = []
        for facility in club_facilities:
            # الحصول على بنود المرفق النشطة
            items = []
            for cfi in club_facility_items:
                if cfi.facility_id == facility.id:
                    facility_item = FacilityItem.query.get(cfi.facility_item_id)
                    print(f"[DEBUG] Checking facility item: {facility_item.name if facility_item else 'None'} (ID: {cfi.facility_item_id})")
                    if facility_item and facility_item.is_active:
                        items.append({
                            'id': facility_item.id,
                            'name': facility_item.name
                        })
                        print(f"[DEBUG] Added item: {facility_item.name}")

            # إضافة المرفق فقط إذا كان لديه بنود نشطة
            if items:
                facilities_data.append({
                    'id': facility.id,
                    'name': facility.name,
                    'items': items,
                    'items_count': len(items)
                })
                print(f"[DEBUG] Added facility to response: {facility.name} with {len(items)} items")
            else:
                print(f"[DEBUG] Facility {facility.name} has no active items, skipping")

        print(f"[DEBUG] Final response: {facilities_data}")
        # طباعة المعلومات في وحدة التحكم
        import sys
        sys.stdout.flush()
        return jsonify(facilities_data)
    except Exception as e:
        print(f"[ERROR] Error in get_club_facilities_for_check: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'حدث خطأ أثناء جلب المرافق: {str(e)}'}), 500



# مسار API جديد لجلب مرافق وبنود النادي
@app.route('/api/v1/clubs/<int:club_id>/facilities', methods=['GET'])
@login_required
def get_club_facilities_and_items(club_id):
    print(f"\n\n[DEBUG] تم استدعاء API الجديد لجلب مرافق النادي بمعرف: {club_id}\n\n")
    try:
        # التحقق من وجود النادي
        club = Club.query.get_or_404(club_id)
        print(f"[DEBUG] تم العثور على النادي: {club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and club not in current_user.clubs:
            print(f"[DEBUG] تم رفض الوصول للمستخدم: {current_user.username}")
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا النادي'}), 403

        # الحصول على المرافق النشطة للنادي
        facilities_data = []

        # الحصول على مرافق النادي المحدد
        club_facilities = list(club.facilities)
        print(f"[DEBUG] تم العثور على {len(club_facilities)} مرفق للنادي")

        # إذا لم يكن للنادي أي مرافق، قم بإضافة جميع المرافق النشطة
        if len(club_facilities) == 0:
            print(f"[DEBUG] لا توجد مرافق للنادي، سيتم إضافة جميع المرافق النشطة")
            all_facilities = Facility.query.filter_by(is_active=True).all()
            for facility in all_facilities:
                club.facilities.append(facility)
            db.session.commit()
            club_facilities = list(club.facilities)
            print(f"[DEBUG] تم إضافة {len(club_facilities)} مرفق للنادي")

        # معالجة كل مرفق
        for facility in club_facilities:
            print(f"[DEBUG] معالجة المرفق: {facility.name} (معرف: {facility.id})")

            # الحصول على بنود المرفق النشطة
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()
            print(f"[DEBUG] تم العثور على {len(facility_items)} بند للمرفق")

            # إعداد قائمة البنود
            items = []
            for item in facility_items:
                items.append({
                    'id': item.id,
                    'name': item.name
                })
                print(f"[DEBUG] تمت إضافة البند: {item.name}")

            # إضافة المرفق دائماً حتى لو لم يكن لديه بنود
            facility_data = {
                'id': facility.id,
                'name': facility.name,
                'items': items,
                'items_count': len(items)
            }
            facilities_data.append(facility_data)
            print(f"[DEBUG] تمت إضافة المرفق إلى الاستجابة: {facility.name} مع {len(items)} بند")

        print(f"[DEBUG] الاستجابة النهائية: {facilities_data}")
        import sys
        sys.stdout.flush()  # للتأكد من طباعة جميع السجلات
        return jsonify(facilities_data)
    except Exception as e:
        print(f"[ERROR] حدث خطأ في مسار API: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'حدث خطأ أثناء جلب المرافق: {str(e)}'}), 500

# مسارات الأعطال الحرجة
@app.route('/critical-issues')
@login_required
def critical_issues_list():
    # لا نحتاج للتحقق من صلاحية العرض هنا - العرض متاح للجميع
    # البحث والتصفية
    search_query = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    # التحقق من وجود جدول الأعطال الحرجة
    try:
        # بناء الاستعلام
        query = CriticalIssue.query

        # التحقق مما إذا كان المستخدم مسؤولاً
        if not current_user.is_admin:
            # المستخدم العادي يرى فقط الأعطال المتعلقة بالنوادي التابعة له
            user_club_ids = [club.id for club in current_user.clubs]
            query = query.filter(CriticalIssue.club_id.in_(user_club_ids))

        # تطبيق فلتر البحث
        if search_query:
            query = query.join(Club).filter(
                Club.name.contains(search_query) |
                CriticalIssue.ticket_number.contains(search_query)
            )

        # تطبيق فلتر الحالة
        if status_filter:
            query = query.filter(CriticalIssue.status == status_filter)

        # ترتيب النتائج حسب تاريخ الإنشاء (الأحدث أولاً)
        issues = query.order_by(CriticalIssue.creation_date.desc()).all()
    except Exception:
        # في حالة وجود خطأ (مثل عدم وجود الجدول)
        issues = []

    # الحصول على قائمة النوادي المتاحة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # قائمة خيارات الحالة
    status_options = [
        'اغلاق الطلب بدون صيانة',
        'تخطت تاريخ الاستحقاق',
        'معلقة',
        'تمت الصيانة'
    ]

    # إنشاء جدول الأعطال الحرجة إذا لم يكن موجوداً
    try:
        db.create_all()
    except Exception:
        pass

    return render_template('critical_issues/index.html',
                          title='سجل الأعطال الحرجة',
                          issues=issues,
                          clubs=clubs,
                          status_options=status_options,
                          search_query=search_query,
                          status_filter=status_filter)

@app.route('/critical-issues/new', methods=['GET', 'POST'])
@login_required
def new_critical_issue():
    # الحصول على قائمة النوادي المتاحة
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # التحقق من وجود نوادي متاحة
    if not clubs:
        flash('لا يوجد لديك نوادي متاحة لإضافة أعطال')
        return redirect(url_for('critical_issues_list'))

    # قائمة خيارات الحالة
    status_options = [
        'اغلاق الطلب بدون صيانة',
        'تخطت تاريخ الاستحقاق',
        'معلقة'
    ]

    # إنشاء جدول الأعطال الحرجة إذا لم يكن موجوداً
    try:
        db.create_all()
    except Exception:
        pass

    # الحصول على المرافق للنادي المحدد
    selected_club_id = request.args.get('club_id')
    facilities = []

    if selected_club_id:
        try:
            selected_club = Club.query.get(selected_club_id)
            if selected_club:
                facilities = selected_club.facilities
        except Exception:
            pass
    elif clubs and len(clubs) > 0:
        # إذا لم يتم تحديد نادي، استخدم أول نادي في القائمة
        selected_club_id = str(clubs[0].id)
        facilities = clubs[0].facilities

    if request.method == 'POST':
        try:
            club_id = request.form.get('club_id')
            facility_id = request.form.get('facility_id')
            ticket_number = request.form.get('ticket_number')
            creation_date = datetime.strptime(request.form.get('creation_date'), '%Y-%m-%d').date()
            due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
            status = request.form.get('status')
            notes = request.form.get('notes', '')

            # إنشاء عطل جديد
            issue = CriticalIssue(
                club_id=club_id,
                ticket_number=ticket_number,
                creation_date=creation_date,
                due_date=due_date,
                status=status,
                notes=notes
            )

            # إضافة المرفق معطلة مؤقتا
            # if facility_id:
            #     try:
            #         issue.facility_id = facility_id
            #     except Exception as e:
            #         print(f"Error setting facility_id: {str(e)}")

            db.session.add(issue)
            db.session.commit()

            flash('تم إضافة العطل الحرج بنجاح!')
            return redirect(url_for('critical_issues_list'))
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة العطل: {str(e)}')

    # التاريخ الحالي للعرض في النموذج
    current_date = date.today().strftime('%Y-%m-%d')

    return render_template('critical_issues/new.html',
                          title='إضافة عطل حرج جديد',
                          clubs=clubs,
                          facilities=facilities,
                          selected_club_id=selected_club_id,
                          status_options=status_options,
                          current_date=current_date)

# مسار API للحصول على مرافق النادي
@app.route('/api/clubs/<int:club_id>/facilities')
@login_required
def get_club_facilities(club_id):
    try:
        club = Club.query.get_or_404(club_id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and club not in current_user.clubs:
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى هذا النادي'}), 403

        facilities = [{'id': facility.id, 'name': facility.name} for facility in club.facilities]
        return jsonify(facilities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/critical-issues/<int:id>')
@login_required
def critical_issue_detail(id):
    try:
        issue = CriticalIssue.query.get_or_404(id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and issue.club not in current_user.clubs:
            flash('ليس لديك صلاحية للوصول إلى هذا العطل')
            return redirect(url_for('critical_issues_list'))

        return render_template('critical_issues/detail.html',
                            title='تفاصيل العطل الحرج',
                            issue=issue)
    except Exception as e:
        flash(f'حدث خطأ أثناء عرض تفاصيل العطل: {str(e)}')
        return redirect(url_for('critical_issues_list'))

@app.route('/critical-issues/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_critical_issue(id):
    try:
        issue = CriticalIssue.query.get_or_404(id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and issue.club not in current_user.clubs:
            flash('ليس لديك صلاحية للوصول إلى هذا العطل')
            return redirect(url_for('critical_issues_list'))

        # الحصول على قائمة النوادي والمرافق
        if current_user.is_admin:
            clubs = Club.query.all()
        else:
            clubs = current_user.clubs

        # الحصول على مرافق النادي الحالي
        facilities = issue.club.facilities

        # قائمة خيارات الحالة
        status_options = [
            'اغلاق الطلب بدون صيانة',
            'تخطت تاريخ الاستحقاق',
            'معلقة'
        ]

        if request.method == 'POST':
            try:
                club_id = request.form.get('club_id')
                facility_id = request.form.get('facility_id')
                ticket_number = request.form.get('ticket_number')
                creation_date = datetime.strptime(request.form.get('creation_date'), '%Y-%m-%d').date()
                due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
                status = request.form.get('status')
                notes = request.form.get('notes', '')

                # تحديث بيانات العطل
                issue.club_id = club_id
                issue.ticket_number = ticket_number
                issue.creation_date = creation_date
                issue.due_date = due_date
                issue.status = status
                issue.notes = notes

                # إضافة المرفق معطلة مؤقتا
                # if facility_id:
                #     try:
                #         issue.facility_id = facility_id
                #     except Exception as e:
                #         print(f"Error setting facility_id: {str(e)}")

                db.session.commit()

                flash('تم تحديث العطل الحرج بنجاح!')
                return redirect(url_for('critical_issue_detail', id=issue.id))
            except Exception as e:
                flash(f'حدث خطأ أثناء تحديث العطل: {str(e)}')

        # التاريخ الحالي للعرض في النموذج
        creation_date = issue.creation_date.strftime('%Y-%m-%d')
        due_date = issue.due_date.strftime('%Y-%m-%d')

        return render_template('critical_issues/edit.html',
                            title='تعديل العطل الحرج',
                            issue=issue,
                            clubs=clubs,
                            facilities=facilities,
                            status_options=status_options,
                            creation_date=creation_date,
                            due_date=due_date)
    except Exception as e:
        flash(f'حدث خطأ أثناء تحميل صفحة التعديل: {str(e)}')
        return redirect(url_for('critical_issues_list'))

@app.route('/critical-issues/<int:id>/close', methods=['GET', 'POST'])
@login_required
def close_critical_issue(id):
    try:
        issue = CriticalIssue.query.get_or_404(id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and issue.club not in current_user.clubs:
            flash('ليس لديك صلاحية للوصول إلى هذا العطل')
            return redirect(url_for('critical_issues_list'))

        # قائمة خيارات الحالة
        status_options = [
            'تمت الصيانة',
            'ترحيل تاريخ الاستحقاق'
        ]

        if request.method == 'POST':
            try:
                status = request.form.get('status')
                notes = request.form.get('notes', '')

                # تحديث الحالة
                issue.status = status

                # إذا كانت الحالة هي ترحيل تاريخ الاستحقاق
                if status == 'ترحيل تاريخ الاستحقاق':
                    # التحقق من وجود تاريخ جديد
                    new_due_date_str = request.form.get('new_due_date')
                    if not new_due_date_str:
                        flash('يرجى تحديد تاريخ الاستحقاق الجديد')
                        return render_template('critical_issues/close.html',
                                            title='إغلاق العطل الحرج',
                                            issue=issue,
                                            status_options=status_options)
                    # تحديث تاريخ الاستحقاق إلى التاريخ الجديد
                    new_due_date = datetime.strptime(new_due_date_str, '%Y-%m-%d').date()
                    issue.due_date = new_due_date

                # تحديث الملاحظات
                issue.notes = notes

                db.session.commit()

                flash('تم إغلاق العطل الحرج بنجاح!')
                return redirect(url_for('critical_issues_list'))
            except Exception as e:
                flash(f'حدث خطأ أثناء إغلاق العطل: {str(e)}')

        return render_template('critical_issues/close.html',
                            title='إغلاق العطل الحرج',
                            issue=issue,
                            status_options=status_options)
    except Exception as e:
        flash(f'حدث خطأ أثناء تحميل صفحة إغلاق العطل: {str(e)}')
        return redirect(url_for('critical_issues_list'))

@app.route('/critical-issues/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_critical_issue(id):
    try:
        issue = CriticalIssue.query.get_or_404(id)

        # التحقق من صلاحية الوصول
        if not current_user.is_admin and issue.club not in current_user.clubs:
            flash('ليس لديك صلاحية للوصول إلى هذا العطل')
            return redirect(url_for('critical_issues_list'))

        db.session.delete(issue)
        db.session.commit()

        flash('تم حذف العطل الحرج بنجاح!')
        return redirect(url_for('critical_issues_list'))
    except Exception as e:
        flash(f'حدث خطأ أثناء حذف العطل: {str(e)}')
        return redirect(url_for('critical_issues_list'))

# مسارات المبيعات
@app.route('/sales')
@login_required
def sales_list():
    # توجيه المستخدم إلى صفحة قائمة الأندية
    return redirect(url_for('sales_clubs_list'))

@app.route('/sales/clubs')
@login_required
def sales_clubs_list():
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على الشهر المطلوب عرضه (الافتراضي هو الشهر الحالي)
    current_month = datetime.now().strftime('%Y-%m')
    selected_month = request.args.get('month', current_month)

    # الحصول على قائمة الأندية المتاحة للمستخدم
    if current_user.is_admin:
        if search_query:
            clubs_query = Club.query.filter(Club.name.contains(search_query))
        else:
            clubs_query = Club.query
    else:
        if search_query:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id,
                Club.name.contains(search_query)
            )
        else:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id
            )

    # الحصول على النسبة المئوية للمبيعات للشهر المحدد لكل نادي
    clubs = []
    for club in clubs_query.all():
        # البحث عن تارجيت الشهر المحدد للنادي
        target = SalesTarget.query.filter_by(club_id=club.id, month=selected_month).first()
        if target:
            # حساب النسبة المئوية للمبيعات
            achievement_percentage = target.get_achievement_percentage()
            club.achievement_percentage = achievement_percentage
        else:
            club.achievement_percentage = 0
        clubs.append(club)

    # تحويل الشهر إلى صيغة مقروءة
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

    # الحصول على قائمة الشهور المتاحة (الشهر الحالي والشهور السابقة)
    available_months = []
    # الحصول على جميع الشهور المتاحة من قاعدة البيانات
    all_months = db.session.query(SalesTarget.month).distinct().order_by(SalesTarget.month.desc()).all()
    available_months = [month[0] for month in all_months]

    # إذا كان الشهر المحدد غير موجود في القائمة، أضفه
    if selected_month not in available_months and selected_month == current_month:
        available_months.append(selected_month)
        available_months.sort(reverse=True)

    # تحويل الشهور إلى صيغة مقروءة
    formatted_months = {}
    for month_str in available_months:
        year, month = month_str.split('-')
        formatted_months[month_str] = f"{arabic_months[int(month)-1]} {year}"

    # تحويل الشهر المحدد إلى صيغة مقروءة
    year, month = selected_month.split('-')
    formatted_month = f"{arabic_months[int(month)-1]} {year}"

    return render_template('sales/clubs_list.html',
                          title='سجل المبيعات',
                          clubs=clubs,
                          search_query=search_query,
                          formatted_month=formatted_month,
                          selected_month=selected_month,
                          available_months=available_months,
                          formatted_months=formatted_months)

@app.route('/sales/club/<int:club_id>')
@login_required
def sales_club_detail(club_id):
    # التحقق من وجود النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('sales_clubs_list'))

    # الحصول على جميع تقارير المبيعات للنادي
    targets = SalesTarget.query.filter_by(club_id=club_id).order_by(SalesTarget.month.desc()).all()

    # تحويل الشهر إلى صيغة مقروءة
    def format_month(month_str):
        year, month = month_str.split('-')
        arabic_months = [
            'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
        return f"{arabic_months[int(month)-1]} {year}"

    formatted_months = {target.month: format_month(target.month) for target in targets}

    return render_template('sales/club_detail.html',
                          title=f'سجل مبيعات {club.name}',
                          club=club,
                          targets=targets,
                          formatted_months=formatted_months)

@app.route('/sales/target/new', methods=['GET', 'POST'])
@login_required
def new_sales_target():
    # الحصول على معرف النادي من الرابط
    selected_club_id = request.args.get('club_id')
    selected_club = None

    # الحصول على قائمة النوادي
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # التحقق من وجود النادي المحدد
    if selected_club_id:
        try:
            selected_club_id = int(selected_club_id)
            # التحقق من أن النادي موجود ومتاح للمستخدم
            if current_user.is_admin:
                selected_club = Club.query.get(selected_club_id)
            else:
                # التحقق من أن النادي متاح للمستخدم
                for club in clubs:
                    if club.id == selected_club_id:
                        selected_club = club
                        break
        except (ValueError, TypeError):
            pass

    if request.method == 'POST':
        club_id = request.form.get('club_id')
        month = request.form.get('month')
        target_amount = request.form.get('target_amount')

        # التحقق من صحة البيانات
        if not club_id or not month or not target_amount:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('new_sales_target'))

        try:
            target_amount = float(target_amount.replace(',', ''))
        except ValueError:
            flash('يرجى إدخال قيمة صحيحة للتارجيت')
            return redirect(url_for('new_sales_target'))

        # التحقق من عدم وجود تارجيت للنادي في نفس الشهر
        existing_target = SalesTarget.query.filter_by(club_id=club_id, month=month).first()
        if existing_target:
            flash('يوجد بالفعل تارجيت لهذا النادي في هذا الشهر')
            return redirect(url_for('edit_sales_target', id=existing_target.id))

        # إنشاء تارجيت جديد
        target = SalesTarget(
            club_id=club_id,
            month=month,
            target_amount=target_amount
        )

        db.session.add(target)
        db.session.commit()

        flash('تم إضافة التارجيت بنجاح!')
        return redirect(url_for('sales_list'))

    # الحصول على الشهر الحالي
    current_month = datetime.now().strftime('%Y-%m')

    return render_template('sales/target_new.html',
                          title='تسجيل تارجيت شهري',
                          clubs=clubs,
                          current_month=current_month,
                          selected_club=selected_club)

@app.route('/sales/target/<int:id>')
@login_required
def sales_target_detail(id):
    target = SalesTarget.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التارجيت')
        return redirect(url_for('sales_list'))

    # الحصول على المبيعات اليومية مرتبة حسب التاريخ
    daily_sales = DailySales.query.filter_by(target_id=id).order_by(DailySales.sale_date).all()

    # حساب إحصائيات التارجيت
    days_in_month = target.get_days_in_month()
    daily_target = target.get_daily_target()
    achieved_amount = target.get_achieved_amount()
    remaining_amount = target.get_remaining_amount()
    achievement_percentage = target.get_achievement_percentage()

    # حساب مجموع المبيعات اليومية بدون مبيعات الأونلاين
    daily_sales_total = sum(sale.amount for sale in daily_sales)

    # تحويل الشهر إلى صيغة مقروءة
    year, month = target.month.split('-')
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    formatted_month = f"{arabic_months[int(month)-1]} {year}"

    return render_template('sales/target_detail.html',
                          title='تفاصيل التارجيت',
                          target=target,
                          daily_sales=daily_sales,
                          days_in_month=days_in_month,
                          daily_target=daily_target,
                          achieved_amount=achieved_amount,
                          remaining_amount=remaining_amount,
                          achievement_percentage=achievement_percentage,
                          formatted_month=formatted_month,
                          daily_sales_total=daily_sales_total,
                          online_sales=target.online_sales)

@app.route('/sales/target/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_sales_target(id):
    target = SalesTarget.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التارجيت')
        return redirect(url_for('sales_list'))

    if request.method == 'POST':
        target_amount = request.form.get('target_amount')

        # التحقق من صحة البيانات
        if not target_amount:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('edit_sales_target', id=id))

        try:
            target_amount = float(target_amount.replace(',', ''))
        except ValueError:
            flash('يرجى إدخال قيمة صحيحة للتارجيت')
            return redirect(url_for('edit_sales_target', id=id))

        # تحديث التارجيت
        target.target_amount = target_amount
        target.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث التارجيت بنجاح!')
        return redirect(url_for('sales_target_detail', id=id))

    return render_template('sales/target_edit.html',
                          title='تعديل التارجيت',
                          target=target)

@app.route('/sales/daily/new', methods=['GET', 'POST'])
@login_required
def new_daily_sales():
    # الحصول على قائمة النوادي
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # الحصول على معرف النادي من الرابط
    selected_club_id = request.args.get('club_id')
    selected_club = None

    if selected_club_id:
        try:
            selected_club_id = int(selected_club_id)
            # التحقق من أن النادي موجود ومتاح للمستخدم
            if current_user.is_admin:
                selected_club = Club.query.get(selected_club_id)
            else:
                # التحقق من أن النادي متاح للمستخدم
                for club in clubs:
                    if club.id == selected_club_id:
                        selected_club = club
                        break
        except (ValueError, TypeError):
            pass

    if request.method == 'POST':
        club_id = request.form.get('club_id')
        sale_date = request.form.get('sale_date')
        amount = request.form.get('amount')

        # التحقق من صحة البيانات
        if not club_id or not sale_date or not amount:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('new_daily_sales'))

        try:
            amount = float(amount.replace(',', ''))
            sale_date = datetime.strptime(sale_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('يرجى إدخال قيم صحيحة')
            return redirect(url_for('new_daily_sales'))

        # الحصول على الشهر من التاريخ
        month = sale_date.strftime('%Y-%m')

        # البحث عن التارجيت المناسب
        target = SalesTarget.query.filter_by(club_id=club_id, month=month).first()

        # إذا لم يكن هناك تارجيت، قم بإنشاء واحد جديد
        if not target:
            target = SalesTarget(
                club_id=club_id,
                month=month,
                target_amount=0  # تارجيت افتراضي
            )
            db.session.add(target)
            db.session.commit()
            flash('تم إنشاء تارجيت جديد للشهر الحالي')

        # التحقق من عدم وجود مبيعات لنفس اليوم
        existing_sale = DailySales.query.filter_by(target_id=target.id, sale_date=sale_date).first()
        if existing_sale:
            # تحديث المبيعات الموجودة
            existing_sale.amount = amount
            existing_sale.updated_at = datetime.now()
            db.session.commit()
            flash('تم تحديث مبيعات اليوم بنجاح!')
        else:
            # إنشاء مبيعات جديدة
            daily_sale = DailySales(
                target_id=target.id,
                sale_date=sale_date,
                amount=amount
            )
            db.session.add(daily_sale)
            db.session.commit()
            flash('تم إضافة مبيعات اليوم بنجاح!')

        return redirect(url_for('sales_target_detail', id=target.id))

    # الحصول على التاريخ الحالي
    current_date = date.today().strftime('%Y-%m-%d')

    return render_template('sales/daily_new.html',
                          title='تسجيل مبيعات يومية',
                          clubs=clubs,
                          current_date=current_date,
                          selected_club=selected_club)

@app.route('/sales/daily/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_daily_sales(id):
    daily_sale = DailySales.query.get_or_404(id)
    target = daily_sale.target

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذه المبيعات')
        return redirect(url_for('sales_list'))

    if request.method == 'POST':
        amount = request.form.get('amount')
        sale_date = request.form.get('sale_date')

        # التحقق من صحة البيانات
        if not amount or not sale_date:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('edit_daily_sales', id=id))

        try:
            amount = float(amount.replace(',', ''))
            new_sale_date = datetime.strptime(sale_date, '%Y-%m-%d').date()
        except ValueError:
            flash('يرجى إدخال قيم صحيحة')
            return redirect(url_for('edit_daily_sales', id=id))

        # الحصول على الشهر من التاريخ الجديد
        new_month = new_sale_date.strftime('%Y-%m')

        # إذا تغير الشهر، تحقق من وجود تارجيت للشهر الجديد
        if new_month != target.month:
            new_target = SalesTarget.query.filter_by(club_id=target.club_id, month=new_month).first()

            # إذا لم يكن هناك تارجيت للشهر الجديد، قم بإنشاء واحد
            if not new_target:
                new_target = SalesTarget(
                    club_id=target.club_id,
                    month=new_month,
                    target_amount=0  # تارجيت افتراضي
                )
                db.session.add(new_target)
                db.session.commit()
                flash('تم إنشاء تارجيت جديد للشهر ' + new_month)

            # تحديث التارجيت المرتبط بالمبيعات
            daily_sale.target_id = new_target.id

        # تحديث المبيعات
        daily_sale.amount = amount
        daily_sale.sale_date = new_sale_date
        daily_sale.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث المبيعات بنجاح!')
        return redirect(url_for('sales_target_detail', id=target.id))

    return render_template('sales/daily_edit.html',
                          title='تعديل المبيعات',
                          daily_sale=daily_sale)

@app.route('/sales/daily/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_daily_sales(id):
    daily_sale = DailySales.query.get_or_404(id)
    target = daily_sale.target

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذه المبيعات')
        return redirect(url_for('sales_list'))

    # حذف المبيعات
    db.session.delete(daily_sale)
    db.session.commit()

    flash('تم حذف المبيعات بنجاح!')
    return redirect(url_for('sales_target_detail', id=target.id))

@app.route('/sales/target/<int:id>/update-additional-sales', methods=['POST'])
@login_required
def update_additional_sales(id):
    target = SalesTarget.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التارجيت')
        return redirect(url_for('sales_list'))

    # الحصول على قيم المبيعات الإضافية
    online_sales = request.form.get('online_sales', '0')
    personal_training_sales = request.form.get('personal_training_sales', '0')

    try:
        # تحويل القيم إلى أرقام عشرية
        online_sales = float(online_sales.replace(',', ''))
        personal_training_sales = float(personal_training_sales.replace(',', ''))

        # تحديث قيم المبيعات
        target.online_sales = online_sales
        target.personal_training_sales = personal_training_sales
        target.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث المبيعات الإضافية بنجاح!')
    except ValueError:
        flash('يرجى إدخال قيم صحيحة للمبيعات')

    return redirect(url_for('sales_target_detail', id=target.id))

@app.route('/sales/target/<int:id>/delete', methods=['POST'])
@login_required
def delete_sales_target(id):
    target = SalesTarget.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and target.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا التارجيت')
        return redirect(url_for('sales_list'))

    # التحقق من صلاحية الحذف
    if not current_user.has_permission('delete_sales_target'):
        flash('ليس لديك صلاحية لحذف التارجيت')
        return redirect(url_for('sales_list'))

    try:
        # حذف التارجيت وجميع المبيعات اليومية المرتبطة به
        db.session.delete(target)
        db.session.commit()

        flash('تم حذف التارجيت بنجاح!')
        return redirect(url_for('sales_list'))
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف التارجيت: {str(e)}')
        return redirect(url_for('sales_list'))

# مسارات إدارة دوام الموظفين
@app.route('/clubs/<int:club_id>/schedules')
@login_required
def club_schedules(club_id):
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    # الحصول على الموظفين مرتبين حسب الوظيفة
    employees_by_position = {}
    for employee in club.employees:
        position = employee.position
        if position not in employees_by_position:
            employees_by_position[position] = []
        employees_by_position[position].append(employee)

    # ترتيب الموظفين داخل كل وظيفة حسب الدور الوظيفي
    for position in employees_by_position:
        # تحديد الدور الوظيفي الذي يجب أن يكون في المقدمة حسب الوظيفة
        priority_role = ''
        if position == 'خدمة عملاء':
            priority_role = 'مدير نادي'  # مدير نادي في المقدمة لخدمة العملاء
        elif position == 'مدرب':
            priority_role = 'مدير لياقة'  # مدير لياقة في المقدمة للمدربين
        elif position == 'عامل':
            priority_role = 'مشرف عمال'  # مشرف عمال في المقدمة للعمال

        # ترتيب الموظفين
        if priority_role:
            # فصل الموظفين ذوي الأولوية عن البقية
            priority_employees = [e for e in employees_by_position[position] if e.role == priority_role]
            other_employees = [e for e in employees_by_position[position] if e.role != priority_role]

            # ترتيب كل مجموعة حسب الاسم
            priority_employees.sort(key=lambda e: e.name)
            other_employees.sort(key=lambda e: e.name)

            # دمج المجموعتين مع وضع ذوي الأولوية في المقدمة
            employees_by_position[position] = priority_employees + other_employees
        else:
            # ترتيب حسب الاسم فقط
            employees_by_position[position].sort(key=lambda e: e.name)

    # ترتيب الوظائف بالترتيب المطلوب: خدمة عملاء, مدرب, عامل
    ordered_positions = []

    # إضافة خدمة العملاء أولاً إذا وجدت
    if 'خدمة عملاء' in employees_by_position:
        ordered_positions.append('خدمة عملاء')

    # إضافة مدرب ثانياً إذا وجدت
    if 'مدرب' in employees_by_position:
        ordered_positions.append('مدرب')

    # إضافة عامل ثالثاً إذا وجدت
    if 'عامل' in employees_by_position:
        ordered_positions.append('عامل')

    # إضافة بقية الوظائف إن وجدت
    for position in employees_by_position.keys():
        if position not in ordered_positions:
            ordered_positions.append(position)

    # الحصول على جداول الدوام للموظفين
    employee_ids = [employee.id for employee in club.employees]
    schedules = EmployeeSchedule.query.filter(
        EmployeeSchedule.club_id == club_id,
        EmployeeSchedule.employee_id.in_(employee_ids)
    ).all()

    # تنظيم جداول الدوام حسب معرف الموظف
    schedules_by_employee = {}
    for schedule in schedules:
        schedules_by_employee[schedule.employee_id] = schedule

    return render_template('schedules/index.html',
                          title=f'دوام موظفي {club.name}',
                          club=club,
                          employees_by_position=employees_by_position,
                          schedules_by_employee=schedules_by_employee,
                          ordered_positions=ordered_positions)

@app.route('/clubs/<int:club_id>/schedules/new', methods=['GET', 'POST'])
@login_required
def new_schedule(club_id):
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')

        # التحقق من وجود الموظف
        employee = Employee.query.get_or_404(employee_id)
        if employee.club_id != club_id:
            flash('الموظف لا ينتمي لهذا النادي')
            return redirect(url_for('club_schedules', club_id=club_id))

        # التحقق من عدم وجود جدول دوام مسبق لهذا الموظف
        existing_schedule = EmployeeSchedule.query.filter_by(
            employee_id=employee_id,
            club_id=club_id
        ).first()

        if existing_schedule:
            flash('يوجد بالفعل جدول دوام لهذا الموظف')
            return redirect(url_for('edit_schedule', club_id=club_id, schedule_id=existing_schedule.id))

        # الحصول على بيانات النموذج
        shift_type = request.form.get('shift_type', 'one_shift')
        work_hours = request.form.get('work_hours', '8')
        shift1_start = request.form.get('shift1_start')
        shift1_end = request.form.get('shift1_end')
        shift2_start = request.form.get('shift2_start')
        shift2_end = request.form.get('shift2_end')
        mobile_number = request.form.get('mobile_number')

        # الحصول على أيام الدوام والإجازة
        work_days = request.form.getlist('work_days')
        off_days = request.form.getlist('off_days')

        # الحصول على معلومات التخصيص
        allocation_days_count = request.form.get('allocation_days_count', '1')

        # معلومات اليوم الأول
        allocation_from = request.form.get('allocation_from')
        allocation_to = request.form.get('allocation_to')
        allocation_days = request.form.getlist('allocation_days')

        # معلومات اليوم الثاني (إذا تم اختيار يومين)
        allocation_from_2 = request.form.get('allocation_from_2')
        allocation_to_2 = request.form.get('allocation_to_2')
        allocation_days_2 = request.form.getlist('allocation_days_2')

        # تجميع البيانات
        allocation_info = {
            'days_count': allocation_days_count,
            'day1': {
                'from': allocation_from,
                'to': allocation_to,
                'days': allocation_days
            }
        }

        if allocation_days_count == '2':
            allocation_info['day2'] = {
                'from': allocation_from_2,
                'to': allocation_to_2,
                'days': allocation_days_2
            }

        # تخزين البيانات كسلسلة نصية JSON
        import json
        allocation_day = json.dumps(allocation_info)

        # إنشاء جدول دوام جديد
        schedule = EmployeeSchedule(
            employee_id=employee_id,
            club_id=club_id,
            shift_type=shift_type,
            work_hours=int(work_hours),
            shift1_start=shift1_start,
            shift1_end=shift1_end,
            shift2_start=shift2_start,
            shift2_end=shift2_end,
            mobile_number=mobile_number,
            work_days=','.join(work_days) if work_days else '',
            off_days=','.join(off_days) if off_days else '',
            allocation_from=allocation_from,
            allocation_to=allocation_to,
            allocation_day=allocation_day
        )

        db.session.add(schedule)
        db.session.commit()

        flash('تم إضافة جدول الدوام بنجاح!')
        return redirect(url_for('club_schedules', club_id=club_id))

    # الحصول على الموظفين الذين ليس لديهم جدول دوام بعد
    employees_with_schedules = db.session.query(EmployeeSchedule.employee_id).filter_by(club_id=club_id).all()
    employees_with_schedules_ids = [e[0] for e in employees_with_schedules]

    available_employees = Employee.query.filter(
        Employee.club_id == club_id,
        ~Employee.id.in_(employees_with_schedules_ids) if employees_with_schedules_ids else True
    ).all()

    return render_template('schedules/new.html',
                          title='إضافة جدول دوام جديد',
                          club=club,
                          available_employees=available_employees)

@app.route('/clubs/<int:club_id>/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_schedule(club_id, schedule_id):
    club = Club.query.get_or_404(club_id)
    schedule = EmployeeSchedule.query.get_or_404(schedule_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    # التحقق من أن الجدول ينتمي للنادي المحدد
    if schedule.club_id != club_id:
        flash('جدول الدوام لا ينتمي لهذا النادي')
        return redirect(url_for('club_schedules', club_id=club_id))

    if request.method == 'POST':
        # تحديث بيانات الجدول
        schedule.shift_type = request.form.get('shift_type', 'one_shift')
        schedule.work_hours = int(request.form.get('work_hours', '8'))
        schedule.shift1_start = request.form.get('shift1_start')
        schedule.shift1_end = request.form.get('shift1_end')
        schedule.shift2_start = request.form.get('shift2_start')
        schedule.shift2_end = request.form.get('shift2_end')
        schedule.mobile_number = request.form.get('mobile_number')

        # تحديث أيام الدوام والإجازة
        work_days = request.form.getlist('work_days')
        off_days = request.form.getlist('off_days')

        schedule.work_days = ','.join(work_days) if work_days else ''
        schedule.off_days = ','.join(off_days) if off_days else ''

        # تحديث معلومات التخصيص
        allocation_days_count = request.form.get('allocation_days_count', '1')

        # معلومات اليوم الأول
        allocation_from = request.form.get('allocation_from')
        allocation_to = request.form.get('allocation_to')
        allocation_days = request.form.getlist('allocation_days')

        # معلومات اليوم الثاني (إذا تم اختيار يومين)
        allocation_from_2 = request.form.get('allocation_from_2')
        allocation_to_2 = request.form.get('allocation_to_2')
        allocation_days_2 = request.form.getlist('allocation_days_2')

        # طباعة البيانات للتشخيص
        print("=== بيانات التخصيص المرسلة من النموذج ===")
        print(f"عدد أيام التخصيص: {allocation_days_count}")
        print(f"اليوم الأول - من: {allocation_from}, إلى: {allocation_to}, الأيام: {allocation_days}")
        print(f"اليوم الثاني - من: {allocation_from_2}, إلى: {allocation_to_2}, الأيام: {allocation_days_2}")

        # تجميع البيانات
        allocation_info = {
            'days_count': allocation_days_count,
            'day1': {
                'from': allocation_from,
                'to': allocation_to,
                'days': allocation_days
            }
        }

        if allocation_days_count == '2':
            allocation_info['day2'] = {
                'from': allocation_from_2,
                'to': allocation_to_2,
                'days': allocation_days_2
            }

        # تخزين البيانات كسلسلة نصية JSON
        import json
        allocation_json = json.dumps(allocation_info)
        print(f"البيانات المخزنة في JSON: {allocation_json}")
        schedule.allocation_day = allocation_json

        db.session.commit()

        flash('تم تحديث جدول الدوام بنجاح!')
        return redirect(url_for('club_schedules', club_id=club_id))

    # تحويل سلسلة أيام الدوام والإجازة إلى قوائم
    work_days_list = schedule.work_days.split(',') if schedule.work_days else []
    off_days_list = schedule.off_days.split(',') if schedule.off_days else []

    # طباعة بيانات التخصيص للتشخيص
    print("=== بيانات التخصيص المخزنة في قاعدة البيانات ===")
    print(f"allocation_day: {schedule.allocation_day}")

    # تهيئة متغيرات لبيانات التخصيص
    days_count = '1'
    day1_from = schedule.allocation_from or ''
    day1_to = schedule.allocation_to or ''
    day1_days = []
    day2_from = ''
    day2_to = ''
    day2_days = []

    # محاولة تحليل البيانات المخزنة
    if schedule.allocation_day and schedule.allocation_day.startswith('{'):
        import json
        try:
            allocation_data = json.loads(schedule.allocation_day)
            print(f"تم تحليل البيانات بنجاح: {allocation_data}")

            # تحديث عدد أيام التخصيص
            days_count = allocation_data.get('days_count', '1')
            print(f"عدد أيام التخصيص: {days_count}")

            # تحديث بيانات اليوم الأول
            if 'day1' in allocation_data:
                day1 = allocation_data['day1']
                day1_from = day1.get('from', '')
                day1_to = day1.get('to', '')
                day1_days = day1.get('days', [])
                print(f"اليوم الأول - من: {day1_from}, إلى: {day1_to}, الأيام: {day1_days}")

            # تحديث بيانات اليوم الثاني
            if 'day2' in allocation_data:
                day2 = allocation_data['day2']
                day2_from = day2.get('from', '')
                day2_to = day2.get('to', '')
                day2_days = day2.get('days', [])
                print(f"اليوم الثاني - من: {day2_from}, إلى: {day2_to}, الأيام: {day2_days}")
            else:
                print("لا توجد بيانات لليوم الثاني")
        except json.JSONDecodeError as e:
            print(f"خطأ في تحليل البيانات: {e}")
    else:
        # إذا لم تكن البيانات بتنسيق JSON، استخدم البيانات القديمة
        if schedule.allocation_day:
            day1_days = schedule.allocation_day.split(',')
        print("لا توجد بيانات تخصيص بتنسيق JSON")

    return render_template('schedules/edit.html',
                          title='تعديل جدول الدوام',
                          club=club,
                          schedule=schedule,
                          work_days=work_days_list,
                          off_days=off_days_list,
                          days_count=days_count,
                          day1_from=day1_from,
                          day1_to=day1_to,
                          day1_days=day1_days,
                          day2_from=day2_from,
                          day2_to=day2_to,
                          day2_days=day2_days)

@app.route('/clubs/<int:club_id>/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(club_id, schedule_id):
    club = Club.query.get_or_404(club_id)
    schedule = EmployeeSchedule.query.get_or_404(schedule_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('clubs'))

    # التحقق من أن الجدول ينتمي للنادي المحدد
    if schedule.club_id != club_id:
        flash('جدول الدوام لا ينتمي لهذا النادي')
        return redirect(url_for('club_schedules', club_id=club_id))

    db.session.delete(schedule)
    db.session.commit()

    flash('تم حذف جدول الدوام بنجاح!')
    return redirect(url_for('club_schedules', club_id=club_id))

# مسارات إدارة المخالفات (الإجراءات النظامية)
@app.route('/violations')
@login_required
def violations_list():
    # توجيه المستخدم إلى صفحة قائمة الأندية
    return redirect(url_for('violations_clubs_list'))

@app.route('/violations/clubs')
@login_required
def violations_clubs_list():
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على قائمة الأندية المتاحة للمستخدم
    if current_user.is_admin:
        if search_query:
            clubs_query = Club.query.filter(Club.name.contains(search_query))
        else:
            clubs_query = Club.query
    else:
        if search_query:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id,
                Club.name.contains(search_query)
            )
        else:
            clubs_query = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id
            )

    # الحصول على عدد الموظفين وعدد المخالفات لكل نادي
    clubs = []

    # الحصول على الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    # اسم الشهر الحالي بالعربية
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    current_month_name = f"{arabic_months[today.month - 1]} {today.year}"

    for club in clubs_query.all():
        # عدد الموظفين في النادي
        employees_count = Employee.query.filter_by(club_id=club.id).count()

        # عدد المخالفات في الشهر الحالي
        violations_count = Violation.query.join(Employee).filter(
            Employee.club_id == club.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        club.employees_count = employees_count
        club.violations_count = violations_count
        clubs.append(club)

    return render_template('violations/clubs_list.html',
                          title='سجل المخالفات',
                          clubs=clubs,
                          search_query=search_query,
                          current_month_name=current_month_name)

@app.route('/violations/club/<int:club_id>')
@login_required
def violations_club_detail(club_id):
    # التحقق من وجود النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('violations_clubs_list'))

    # البحث والتصفية
    search_query = request.args.get('search', '')

    # الحصول على قائمة الموظفين في النادي
    if search_query:
        employees_query = Employee.query.filter(
            Employee.club_id == club_id,
            Employee.name.contains(search_query) | Employee.employee_id.contains(search_query)
        )
    else:
        employees_query = Employee.query.filter_by(club_id=club_id)

    # الحصول على الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    # اسم الشهر الحالي بالعربية
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    current_month_name = f"{arabic_months[today.month - 1]} {today.year}"

    # الحصول على عدد المخالفات لكل موظف في الشهر الحالي
    employees = []
    for employee in employees_query.all():
        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        employee.violations_count = violations_count
        employees.append(employee)

    return render_template('violations/club_detail.html',
                          title=f'مخالفات {club.name}',
                          club=club,
                          employees=employees,
                          search_query=search_query,
                          current_month_name=current_month_name)

@app.route('/violations/employee/<int:employee_id>')
@login_required
def violations_employee_detail(employee_id):
    # التحقق من وجود الموظف
    employee = Employee.query.get_or_404(employee_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and employee.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
        return redirect(url_for('violations_clubs_list'))

    # الحصول على معلمة الفلتر من الطلب
    filter_type = request.args.get('filter', 'all')  # القيمة الافتراضية هي 'all'

    # الحصول على جميع مخالفات الموظف مرتبة حسب التاريخ (الأحدث أولاً)
    violations_query = Violation.query.filter_by(employee_id=employee_id)

    # تطبيق الفلتر إذا كان "الشهر الحالي"
    if filter_type == 'current_month':
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_query = violations_query.filter(
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        )

    # تنفيذ الاستعلام وترتيب النتائج
    violations = violations_query.order_by(Violation.violation_date.desc()).all()

    # حساب رقم المخالفة من نفس النوع لكل مخالفة
    for violation in violations:
        # حساب عدد المخالفات من نفس النوع للموظف
        same_type_violations_count = Violation.query.filter(
            Violation.employee_id == employee_id,
            Violation.violation_type_id == violation.violation_type_id,
            Violation.id <= violation.id  # نحسب فقط المخالفات حتى هذه المخالفة (بما فيها)
        ).count()

        # إضافة الرقم كخاصية مؤقتة للمخالفة
        violation.same_type_number = same_type_violations_count

    # تنظيم المخالفات حسب الشهر
    violations_by_month = {}
    arabic_months = [
        'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]

    # الحصول على اسم الشهر الحالي
    today = date.today()
    current_month_name = f"{arabic_months[today.month - 1]} {today.year}"

    for violation in violations:
        month_key = f"{violation.violation_date.year}-{violation.violation_date.month}"
        month_name = f"{arabic_months[violation.violation_date.month - 1]} {violation.violation_date.year}"

        if month_key not in violations_by_month:
            violations_by_month[month_key] = {
                'month_name': month_name,
                'violations': []
            }

        violations_by_month[month_key]['violations'].append(violation)

    # تحويل القاموس إلى قائمة مرتبة حسب الشهر (الأحدث أولاً)
    violations_by_month = [violations_by_month[key] for key in sorted(violations_by_month.keys(), reverse=True)]

    return render_template('violations/employee_detail.html',
                          title=f'مخالفات {employee.name}',
                          employee=employee,
                          violations_by_month=violations_by_month,
                          filter_type=filter_type,
                          current_month_name=current_month_name)

@app.route('/violations/employee/<int:employee_id>/new')
@login_required
def new_violation_for_employee(employee_id):
    # التحقق من وجود الموظف
    employee = Employee.query.get_or_404(employee_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and employee.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
        return redirect(url_for('violations_clubs_list'))

    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('add_violation'):
        flash('ليس لديك صلاحية لإضافة مخالفة جديدة')
        return redirect(url_for('violations_employee_detail', employee_id=employee_id))

    # حساب عدد المخالفات في الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    violations_count = Violation.query.filter(
        Violation.employee_id == employee.id,
        Violation.violation_date >= month_start,
        Violation.violation_date <= month_end
    ).count()

    # الحصول على قائمة أنواع المخالفات النشطة
    violation_types = ViolationType.query.filter_by(is_active=True).all()

    # قائمة مصادر المخالفة
    violation_sources = ['مدبر المنطقه', 'مدير النادي', 'مراقبه الكاميرات', 'مدير الانديه']

    # التاريخ الحالي للعرض في النموذج
    current_date = date.today().strftime('%Y-%m-%d')

    # طباعة معلومات تشخيصية
    print(f"تم العثور على الموظف: {employee.name}, الرقم الوظيفي: {employee.employee_id}")
    print(f"عدد المخالفات في الشهر الحالي: {violations_count}")

    # عرض نموذج المخالفة المخصص للموظف
    return render_template('violations/employee_violation.html',
                           title='إضافة مخالفة جديدة',
                           employee=employee,
                           violations_count=violations_count,
                           violation_types=violation_types,
                           violation_sources=violation_sources,
                           current_date=current_date)

@app.route('/violations/employee/<int:employee_id>/violation/new', methods=['POST'])
@login_required
def new_violation_from_employee(employee_id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('add_violation'):
        flash('ليس لديك صلاحية لإضافة مخالفة جديدة')
        return redirect(url_for('violations_employee_detail', employee_id=employee_id))

    # التحقق من وجود الموظف
    employee = Employee.query.get_or_404(employee_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and employee.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا الموظف')
        return redirect(url_for('violations_clubs_list'))

    if request.method == 'POST':
        # الحصول على بيانات النموذج
        violation_type_id = request.form.get('violation_type_id')  # نوع المخالفة
        violation_date = request.form.get('violation_date')  # تاريخ المخالفة
        violation_source = request.form.get('violation_source')  # مصدر المخالفة
        is_signed = 'is_signed' in request.form  # تم التوقيع
        notes = request.form.get('notes', '')  # ملاحظات

        # التحقق من وجود نوع المخالفة
        violation_type = ViolationType.query.get(violation_type_id)
        if not violation_type:
            flash('نوع المخالفة غير موجود')
            return redirect(url_for('new_violation_for_employee', employee_id=employee_id))

        # تحويل تاريخ المخالفة إلى كائن تاريخ
        try:
            violation_date = datetime.strptime(violation_date, '%Y-%m-%d').date()
        except ValueError:
            flash('تنسيق التاريخ غير صحيح')
            return redirect(url_for('new_violation_for_employee', employee_id=employee_id))

        # حساب رقم المخالفة (عدد المخالفات السابقة للموظف في نفس الشهر + 1)
        month_start = date(violation_date.year, violation_date.month, 1)
        month_end = date(violation_date.year, violation_date.month + 1, 1) if violation_date.month < 12 else date(violation_date.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        previous_violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        violation_number = previous_violations_count + 1

        # معالجة الصورة إذا تم تحميلها
        image_path = None
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image.filename:
                # إنشاء اسم فريد للملف
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                # إنشاء مجلد للصور إذا لم يكن موجوداً
                violations_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'violations')
                if not os.path.exists(violations_folder):
                    os.makedirs(violations_folder)
                # حفظ الصورة
                image_path = os.path.join('violations', filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))

        # إنشاء مخالفة جديدة
        violation = Violation(
            employee_id=employee.id,
            violation_type_id=violation_type.id,
            violation_number=violation_number,
            violation_date=violation_date,
            violation_source=violation_source,
            is_signed=is_signed,
            image_path=image_path,
            notes=notes,
            created_by=current_user.id
        )

        db.session.add(violation)
        db.session.commit()

        flash('تم إضافة المخالفة بنجاح!')
        return redirect(url_for('violations_employee_detail', employee_id=employee_id))

    return redirect(url_for('new_violation_for_employee', employee_id=employee_id))

@app.route('/violations/new', methods=['GET', 'POST'])
@login_required
def new_violation():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('add_violation'):
        flash('ليس لديك صلاحية لإضافة مخالفة جديدة')
        return redirect(url_for('violations_list'))

    # الحصول على قائمة أنواع المخالفات النشطة
    violation_types = ViolationType.query.filter_by(is_active=True).all()

    # قائمة مصادر المخالفة
    violation_sources = ['مدبر المنطقه', 'مدير النادي', 'مراقبه الكاميرات', 'مدير الانديه']

# تم حذف الكود القديم لأنه لم يعد مطلوباً

# تم حذف الكود القديم

    if request.method == 'POST':
        # الحصول على بيانات النموذج
        employee_id = request.form.get('employee_id')  # الرقم الوظيفي من حقل الإدخال
        employee_id_hidden = request.form.get('employee_id_hidden')  # الرقم الوظيفي من الحقل المخفي
        employee_name_hidden = request.form.get('employee_name_hidden')  # اسم الموظف من الحقل المخفي
        employee_role_hidden = request.form.get('employee_role_hidden')  # الدور الوظيفي من الحقل المخفي
        club_name_hidden = request.form.get('club_name_hidden')  # اسم النادي من الحقل المخفي
        violation_number_hidden = request.form.get('violation_number_hidden')  # رقم المخالفة من الحقل المخفي

        violation_type_id = request.form.get('violation_type_id')  # نوع المخالفة
        violation_date = request.form.get('violation_date')  # تاريخ المخالفة
        violation_source = request.form.get('violation_source')  # مصدر المخالفة
        is_signed = 'is_signed' in request.form  # تم التوقيع
        notes = request.form.get('notes', '')  # ملاحظات

        # طباعة بيانات النموذج للتشخيص
        print(f"Form data - employee_id: {employee_id}, employee_id_hidden: {employee_id_hidden}")
        print(f"Form data - employee_name_hidden: {employee_name_hidden}, employee_role_hidden: {employee_role_hidden}")
        print(f"Form data - club_name_hidden: {club_name_hidden}, violation_number_hidden: {violation_number_hidden}")
        print(f"Form data - violation_type_id: {violation_type_id}, violation_date: {violation_date}")

        # استخدام الرقم الوظيفي من الحقل المخفي إذا كان متوفراً
        if employee_id_hidden:
            employee_id = employee_id_hidden

        # التحقق من وجود الموظف
        employee = None

        # محاولة البحث بعدة طرق مختلفة
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()

        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
            except (ValueError, TypeError):
                pass

        if not employee:
            flash('الرقم الوظيفي غير موجود')
            return redirect(url_for('new_violation'))

        # التحقق من وجود نوع المخالفة
        violation_type = ViolationType.query.get(violation_type_id)
        if not violation_type:
            flash('نوع المخالفة غير موجود')
            return redirect(url_for('new_violation'))

        # تحويل تاريخ المخالفة إلى كائن تاريخ
        try:
            violation_date = datetime.strptime(violation_date, '%Y-%m-%d').date()
        except ValueError:
            flash('تنسيق التاريخ غير صحيح')
            return redirect(url_for('new_violation'))

        # حساب رقم المخالفة (عدد المخالفات السابقة للموظف في نفس الشهر + 1)
        # استخدام رقم المخالفة من الحقل المخفي إذا كان متوفراً
        if violation_number_hidden:
            try:
                violation_number = int(violation_number_hidden)
            except (ValueError, TypeError):
                # إذا كان هناك خطأ في تحويل رقم المخالفة، نحسبه من قاعدة البيانات
                month_start = date(violation_date.year, violation_date.month, 1)
                month_end = date(violation_date.year, violation_date.month + 1, 1) if violation_date.month < 12 else date(violation_date.year + 1, 1, 1)
                month_end = month_end - timedelta(days=1)

                previous_violations_count = Violation.query.filter(
                    Violation.employee_id == employee.id,
                    Violation.violation_date >= month_start,
                    Violation.violation_date <= month_end
                ).count()

                violation_number = previous_violations_count + 1
        else:
            # حساب رقم المخالفة من قاعدة البيانات
            month_start = date(violation_date.year, violation_date.month, 1)
            month_end = date(violation_date.year, violation_date.month + 1, 1) if violation_date.month < 12 else date(violation_date.year + 1, 1, 1)
            month_end = month_end - timedelta(days=1)

            previous_violations_count = Violation.query.filter(
                Violation.employee_id == employee.id,
                Violation.violation_date >= month_start,
                Violation.violation_date <= month_end
            ).count()

            violation_number = previous_violations_count + 1

        # معالجة الصورة إذا تم تحميلها
        image_path = None
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image.filename:
                # إنشاء اسم فريد للملف
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                # إنشاء مجلد للصور إذا لم يكن موجوداً
                violations_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'violations')
                if not os.path.exists(violations_folder):
                    os.makedirs(violations_folder)
                # حفظ الصورة
                image_path = os.path.join('violations', filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))

        # إنشاء مخالفة جديدة
        violation = Violation(
            employee_id=employee.id,
            violation_type_id=violation_type.id,
            violation_number=violation_number,
            violation_date=violation_date,
            violation_source=violation_source,
            is_signed=is_signed,
            image_path=image_path,
            notes=notes,
            created_by=current_user.id
        )

        db.session.add(violation)
        db.session.commit()

        flash('تم إضافة المخالفة بنجاح!')
        return redirect(url_for('violations_list'))

    # التاريخ الحالي للعرض في النموذج
    current_date = date.today().strftime('%Y-%m-%d')

    return render_template('violations/new.html',
                          title='إضافة مخالفة جديدة',
                          violation_types=violation_types,
                          violation_sources=violation_sources,
                          current_date=current_date)

@app.route('/violations/<int:id>')
@login_required
def violation_detail(id):
    violation = Violation.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        # التحقق من أن المخالفة تتعلق بموظف في نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if violation.employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذه المخالفة')
            return redirect(url_for('violations_list'))

    # حساب رقم المخالفة من نفس النوع
    same_type_violations_count = Violation.query.filter(
        Violation.employee_id == violation.employee_id,
        Violation.violation_type_id == violation.violation_type_id,
        Violation.id <= violation.id  # نحسب فقط المخالفات حتى هذه المخالفة (بما فيها)
    ).count()

    return render_template('violations/detail.html',
                          title='تفاصيل المخالفة',
                          violation=violation,
                          same_type_number=same_type_violations_count)

@app.route('/violations/<int:id>/delete', methods=['POST'])
@login_required
def delete_violation(id):
    violation = Violation.query.get_or_404(id)
    employee_id = violation.employee_id

    # التحقق من صلاحية الوصول والحذف
    if not current_user.is_admin:
        # التحقق من أن المخالفة تتعلق بموظف في نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if violation.employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذه المخالفة')
            return redirect(url_for('violations_list'))

        # التحقق من صلاحية الحذف
        if not current_user.has_permission('delete_violation'):
            flash('ليس لديك صلاحية لحذف المخالفات')
            return redirect(url_for('violations_employee_detail', employee_id=employee_id))

    try:
        # حذف المخالفة
        db.session.delete(violation)
        db.session.commit()
        flash('تم حذف المخالفة بنجاح!')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء حذف المخالفة: {str(e)}')

    return redirect(url_for('violations_employee_detail', employee_id=employee_id))

@app.route('/violations/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_violation(id):
    violation = Violation.query.get_or_404(id)

    # التحقق من صلاحية الوصول والتعديل
    if not current_user.is_admin:
        # التحقق من أن المخالفة تتعلق بموظف في نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if violation.employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذه المخالفة')
            return redirect(url_for('violations_list'))

        # التحقق من صلاحية التعديل
        if not current_user.has_permission('edit_violation'):
            flash('ليس لديك صلاحية لتعديل المخالفات')
            return redirect(url_for('violation_detail', id=violation.id))

    # الحصول على قائمة أنواع المخالفات النشطة
    violation_types = ViolationType.query.filter_by(is_active=True).all()

    # قائمة مصادر المخالفة
    violation_sources = ['مدبر المنطقه', 'مدير النادي', 'مراقبه الكاميرات', 'مدير الانديه']

    if request.method == 'POST':
        violation_type_id = request.form.get('violation_type_id')  # نوع المخالفة
        violation_date = request.form.get('violation_date')  # تاريخ المخالفة
        violation_source = request.form.get('violation_source')  # مصدر المخالفة
        is_signed = 'is_signed' in request.form  # تم التوقيع
        notes = request.form.get('notes', '')  # ملاحظات

        # التحقق من وجود نوع المخالفة
        violation_type = ViolationType.query.get(violation_type_id)
        if not violation_type:
            flash('نوع المخالفة غير موجود')
            return redirect(url_for('edit_violation', id=violation.id))

        # تحويل تاريخ المخالفة إلى كائن تاريخ
        try:
            violation_date = datetime.strptime(violation_date, '%Y-%m-%d').date()
        except ValueError:
            flash('تنسيق التاريخ غير صحيح')
            return redirect(url_for('edit_violation', id=violation.id))

        # معالجة الصورة إذا تم تحميلها
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image.filename:
                # إنشاء اسم فريد للملف
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                # إنشاء مجلد للصور إذا لم يكن موجوداً
                violations_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'violations')
                if not os.path.exists(violations_folder):
                    os.makedirs(violations_folder)
                # حفظ الصورة
                image_path = os.path.join('violations', filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
                # تحديث مسار الصورة
                violation.image_path = image_path

        # تحديث بيانات المخالفة
        violation.violation_type_id = violation_type.id
        violation.violation_date = violation_date
        violation.violation_source = violation_source
        violation.is_signed = is_signed
        violation.notes = notes
        violation.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث المخالفة بنجاح!')
        return redirect(url_for('violations_employee_detail', employee_id=violation.employee.id))

    # استخدام قالب مخصص للتعديل
    return render_template('violations/edit_employee_violation.html',
                          title='تعديل المخالفة',
                          violation=violation,
                          violation_types=violation_types,
                          violation_sources=violation_sources)

@app.route('/violations/<int:id>/edit/employee', methods=['POST'])
@login_required
def edit_violation_from_employee(id):
    violation = Violation.query.get_or_404(id)

    # التحقق من صلاحية الوصول والتعديل
    if not current_user.is_admin:
        # التحقق من أن المخالفة تتعلق بموظف في نادي متاح للمستخدم
        user_club_ids = [club.id for club in current_user.clubs]
        if violation.employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى هذه المخالفة')
            return redirect(url_for('violations_list'))

        # التحقق من صلاحية التعديل
        if not current_user.has_permission('edit_violation'):
            flash('ليس لديك صلاحية لتعديل المخالفات')
            return redirect(url_for('violation_detail', id=violation.id))

    if request.method == 'POST':
        violation_type_id = request.form.get('violation_type_id')  # نوع المخالفة
        violation_date = request.form.get('violation_date')  # تاريخ المخالفة
        violation_source = request.form.get('violation_source')  # مصدر المخالفة
        is_signed = 'is_signed' in request.form  # تم التوقيع
        notes = request.form.get('notes', '')  # ملاحظات

        # التحقق من وجود نوع المخالفة
        violation_type = ViolationType.query.get(violation_type_id)
        if not violation_type:
            flash('نوع المخالفة غير موجود')
            return redirect(url_for('edit_violation', id=violation.id))

        # تحويل تاريخ المخالفة إلى كائن تاريخ
        try:
            violation_date = datetime.strptime(violation_date, '%Y-%m-%d').date()
        except ValueError:
            flash('تنسيق التاريخ غير صحيح')
            return redirect(url_for('edit_violation', id=violation.id))

        # معالجة الصورة إذا تم تحميلها
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image.filename:
                # إنشاء اسم فريد للملف
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                # إنشاء مجلد للصور إذا لم يكن موجوداً
                violations_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'violations')
                if not os.path.exists(violations_folder):
                    os.makedirs(violations_folder)
                # حفظ الصورة
                image_path = os.path.join('violations', filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_path))
                # تحديث مسار الصورة
                violation.image_path = image_path

        # تحديث بيانات المخالفة
        violation.violation_type_id = violation_type.id
        violation.violation_date = violation_date
        violation.violation_source = violation_source
        violation.is_signed = is_signed
        violation.notes = notes
        violation.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث المخالفة بنجاح!')
        return redirect(url_for('violations_employee_detail', employee_id=violation.employee.id))

@app.route('/violations/types', methods=['GET'])
@login_required
def violation_types_list():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية للوصول إلى أنواع المخالفات')
        return redirect(url_for('violations_list'))

    # الحصول على جميع أنواع المخالفات
    violation_types = ViolationType.query.order_by(ViolationType.name).all()

    # حساب عدد المخالفات لكل نوع
    for vtype in violation_types:
        vtype.violations_count = Violation.query.filter_by(violation_type_id=vtype.id).count()

    return render_template('violations/types_list.html',
                          title='أنواع المخالفات',
                          violation_types=violation_types)

@app.route('/violations/types/add', methods=['GET', 'POST'])
@login_required
def add_violation_type():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية لإضافة أنواع المخالفات')
        return redirect(url_for('violations_list'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = 'is_active' in request.form

        # التحقق من وجود الاسم
        if not name:
            flash('يرجى إدخال اسم نوع المخالفة')
            return redirect(url_for('add_violation_type'))

        # التحقق من عدم وجود نوع مخالفة بنفس الاسم
        existing_type = ViolationType.query.filter_by(name=name).first()
        if existing_type:
            flash('يوجد نوع مخالفة بنفس الاسم بالفعل')
            return redirect(url_for('add_violation_type'))

        # إنشاء نوع مخالفة جديد
        violation_type = ViolationType(
            name=name,
            description=description,
            is_active=is_active,
            is_imported=False
        )

        db.session.add(violation_type)
        db.session.commit()

        flash('تم إضافة نوع المخالفة بنجاح')
        return redirect(url_for('violation_types_list'))

    return render_template('violations/type_form.html',
                          title='إضافة نوع مخالفة جديد',
                          violation_type=None,
                          action='add')

@app.route('/violations/types/<int:id>', methods=['GET'])
@login_required
def view_violation_type(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية لعرض أنواع المخالفات')
        return redirect(url_for('violations_list'))

    # الحصول على نوع المخالفة
    violation_type = ViolationType.query.get_or_404(id)

    # حساب عدد المخالفات المرتبطة بهذا النوع
    violations_count = Violation.query.filter_by(violation_type_id=id).count()

    return render_template('violations/type_detail.html',
                          title=f'تفاصيل نوع المخالفة: {violation_type.name}',
                          violation_type=violation_type,
                          violations_count=violations_count)

@app.route('/violations/types/<int:id>/delete', methods=['POST'])
@login_required
def delete_violation_type(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية لحذف أنواع المخالفات')
        return redirect(url_for('violations_list'))

    # الحصول على نوع المخالفة
    violation_type = ViolationType.query.get_or_404(id)

    # التحقق من عدم وجود مخالفات مرتبطة بهذا النوع
    violations_count = Violation.query.filter_by(violation_type_id=id).count()
    if violations_count > 0:
        flash(f'لا يمكن حذف نوع المخالفة لأنه مرتبط بـ {violations_count} مخالفة')
        return redirect(url_for('violation_types_list'))

    # حذف نوع المخالفة
    db.session.delete(violation_type)
    db.session.commit()

    flash('تم حذف نوع المخالفة بنجاح')
    return redirect(url_for('violation_types_list'))

@app.route('/violations/types/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_violation_type(id):
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية لتعديل أنواع المخالفات')
        return redirect(url_for('violations_list'))

    # الحصول على نوع المخالفة
    violation_type = ViolationType.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_active = 'is_active' in request.form

        # التحقق من وجود الاسم
        if not name:
            flash('يرجى إدخال اسم نوع المخالفة')
            return redirect(url_for('edit_violation_type', id=id))

        # التحقق من عدم وجود نوع مخالفة آخر بنفس الاسم
        existing_type = ViolationType.query.filter(ViolationType.name == name, ViolationType.id != id).first()
        if existing_type:
            flash('يوجد نوع مخالفة آخر بنفس الاسم')
            return redirect(url_for('edit_violation_type', id=id))

        # تحديث نوع المخالفة
        violation_type.name = name
        violation_type.description = description
        violation_type.is_active = is_active
        violation_type.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث نوع المخالفة بنجاح')
        return redirect(url_for('violation_types_list'))

    return render_template('violations/type_form.html',
                          title='تعديل نوع المخالفة',
                          violation_type=violation_type,
                          action='edit')

@app.route('/violations/types/import', methods=['GET', 'POST'])
@login_required
def import_violation_types():
    # التحقق من صلاحية المستخدم
    if not current_user.has_permission('import_violation_types'):
        flash('ليس لديك صلاحية لاستيراد أنواع المخالفات')
        return redirect(url_for('violations_list'))

    if request.method == 'POST':
        # التحقق من وجود ملف
        if 'file' not in request.files:
            flash('لم يتم تحديد ملف')
            return redirect(request.url)

        file = request.files['file']

        # التحقق من أن الملف له اسم
        if file.filename == '':
            flash('لم يتم تحديد ملف')
            return redirect(request.url)

        # التحقق من امتداد الملف
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('يجب أن يكون الملف بتنسيق Excel (.xlsx أو .xls)')
            return redirect(request.url)

        try:
            # قراءة ملف الإكسل
            df = pd.read_excel(file)

            # التحقق من وجود الأعمدة المطلوبة
            required_columns = ['name', 'description']
            for column in required_columns:
                if column not in df.columns:
                    flash(f'الملف لا يحتوي على العمود المطلوب: {column}')
                    return redirect(request.url)

            # إضافة أنواع المخالفات إلى قاعدة البيانات
            success_count = 0
            error_count = 0

            for index, row in df.iterrows():
                try:
                    # التحقق من وجود نوع المخالفة مسبقاً
                    existing_type = ViolationType.query.filter_by(name=row['name']).first()

                    if existing_type:
                        # تحديث نوع المخالفة الموجود
                        existing_type.description = row['description']
                        existing_type.is_active = True
                        existing_type.is_imported = True
                    else:
                        # إنشاء نوع مخالفة جديد
                        violation_type = ViolationType(
                            name=row['name'],
                            description=row['description'],
                            is_active=True,
                            is_imported=True
                        )
                        db.session.add(violation_type)

                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error importing row {index}: {str(e)}")

            db.session.commit()
            flash(f'تم استيراد {success_count} نوع مخالفة بنجاح. فشل استيراد {error_count} نوع مخالفة.')
            return redirect(url_for('violations_list'))

        except Exception as e:
            flash(f'حدث خطأ أثناء قراءة الملف: {str(e)}')
            return redirect(request.url)

    return render_template('violations/import_types.html', title='استيراد أنواع المخالفات')

# API للحصول على بيانات الموظف بناءً على الرقم الوظيفي
@app.route('/api/employee/<employee_id>', methods=['GET'])
@login_required
def get_employee_data(employee_id):
    # طباعة الرقم الوظيفي للتشخيص
    print(f"Searching for employee with ID: {employee_id}")
    print(f"Request headers: {request.headers}")
    print(f"Request method: {request.method}")
    print(f"Request args: {request.args}")

    # محاولة البحث بعدة طرق مختلفة
    employee = None

    # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if employee:
        print(f"Found employee using exact match: {employee.name}")

    # الطريقة 2: البحث بعد إزالة المسافات
    if not employee:
        clean_id = str(employee_id).strip()
        employee = Employee.query.filter_by(employee_id=clean_id).first()
        if employee:
            print(f"Found employee after stripping spaces: {employee.name}")

    # الطريقة 3: البحث باستخدام LIKE
    if not employee:
        employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
        if employee:
            print(f"Found employee using LIKE: {employee.name}")

    # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
    if not employee:
        try:
            emp_id_int = int(employee_id)
            employee = Employee.query.get(emp_id_int)
            if employee:
                print(f"Found employee using numeric ID: {employee.name}")
        except (ValueError, TypeError):
            pass

    # الطريقة 5: البحث باستخدام LIKE مع تنظيف إضافي
    if not employee:
        try:
            # إزالة جميع المسافات والأحرف الخاصة
            clean_id = ''.join(c for c in employee_id if c.isalnum())
            if clean_id:
                employee = Employee.query.filter(Employee.employee_id.like(f"%{clean_id}%")).first()
                if employee:
                    print(f"Found employee using cleaned LIKE: {employee.name}")
        except Exception as e:
            print(f"Error in additional cleaning: {str(e)}")

    # إذا لم يتم العثور على الموظف
    if not employee:
        print(f"Employee not found with ID: {employee_id}")
        return jsonify({'error': 'الموظف غير موجود'}), 404

    print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        user_club_ids = [club.id for club in current_user.clubs]
        if employee.club_id not in user_club_ids:
            print(f"Access denied for user {current_user.name} to employee {employee.name}")
            return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

    # حساب عدد المخالفات في الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    violations_count = Violation.query.filter(
        Violation.employee_id == employee.id,
        Violation.violation_date >= month_start,
        Violation.violation_date <= month_end
    ).count()

    print(f"Violations count for employee {employee.name}: {violations_count}")

    # إرجاع بيانات الموظف
    response_data = {
        'name': employee.name,
        'role': employee.role,
        'club_id': employee.club_id,
        'club_name': employee.club.name,
        'violations_count': violations_count
    }

    print(f"Returning data: {response_data}")
    return jsonify(response_data)

# مسار API بديل للبحث عن الموظف باستخدام الرقم الوظيفي
@app.route('/api/find-employee', methods=['POST'])
@login_required
def find_employee():
    # الحصول على الرقم الوظيفي من الطلب
    try:
        request_data = request.get_json()
        print(f"Request data: {request_data}")

        if not request_data or 'employee_id' not in request_data:
            print("Error: No employee_id in request data")
            return jsonify({'error': 'الرقم الوظيفي غير موجود في الطلب'}), 400

        employee_id = request_data.get('employee_id', '')
        print(f"Searching for employee with ID: {employee_id}")

        # محاولة البحث بعدة طرق مختلفة
        employee = None

        # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            print(f"Found employee using exact match: {employee.name}")

        # الطريقة 2: البحث بعد إزالة المسافات
        if not employee:
            clean_id = str(employee_id).strip()
            employee = Employee.query.filter_by(employee_id=clean_id).first()
            if employee:
                print(f"Found employee after stripping spaces: {employee.name}")

        # الطريقة 3: البحث باستخدام LIKE
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
            if employee:
                print(f"Found employee using LIKE: {employee.name}")

        # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
                if employee:
                    print(f"Found employee using numeric ID: {employee.name}")
            except (ValueError, TypeError):
                pass

        # إذا لم يتم العثور على الموظف
        if not employee:
            print(f"Employee not found with ID: {employee_id}")
            return jsonify({'error': 'الموظف غير موجود'}), 404

        print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                print(f"Access denied for user {current_user.name} to employee {employee.name}")
                return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

        # حساب عدد المخالفات في الشهر الحالي
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        print(f"Violations count for employee {employee.name}: {violations_count}")

        # إرجاع بيانات الموظف
        response_data = {
            'name': employee.name,
            'role': employee.role,
            'club_id': employee.club_id,
            'club_name': employee.club.name,
            'violations_count': violations_count
        }

        print(f"Returning data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in find_employee API: {str(e)}")
        return jsonify({'error': f'حدث خطأ أثناء البحث عن الموظف: {str(e)}'}), 500

# مسار API جديد للبحث عن الموظف باستخدام الرقم الوظيفي
@app.route('/api/employee/search', methods=['POST'])
@login_required
def search_employee():
    try:
        # الحصول على الرقم الوظيفي من الطلب
        employee_id = request.form.get('employee_id', '')
        print(f"Searching for employee with ID: {employee_id}")

        if not employee_id:
            return jsonify({'error': 'الرقم الوظيفي غير موجود'}), 400

        # محاولة البحث بعدة طرق مختلفة
        employee = None

        # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            print(f"Found employee using exact match: {employee.name}")

        # الطريقة 2: البحث بعد إزالة المسافات
        if not employee:
            clean_id = str(employee_id).strip()
            employee = Employee.query.filter_by(employee_id=clean_id).first()
            if employee:
                print(f"Found employee after stripping spaces: {employee.name}")

        # الطريقة 3: البحث باستخدام LIKE
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
            if employee:
                print(f"Found employee using LIKE: {employee.name}")

        # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
                if employee:
                    print(f"Found employee using numeric ID: {employee.name}")
            except (ValueError, TypeError):
                pass

        # إذا لم يتم العثور على الموظف
        if not employee:
            print(f"Employee not found with ID: {employee_id}")
            return jsonify({'error': 'الموظف غير موجود'}), 404

        print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                print(f"Access denied for user {current_user.name} to employee {employee.name}")
                return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

        # حساب عدد المخالفات في الشهر الحالي
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        print(f"Violations count for employee {employee.name}: {violations_count}")

        # إرجاع بيانات الموظف
        response_data = {
            'name': employee.name,
            'role': employee.role,
            'club_id': employee.club_id,
            'club_name': employee.club.name,
            'violations_count': violations_count
        }

        print(f"Returning data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in search_employee API: {str(e)}")
        return jsonify({'error': f'حدث خطأ أثناء البحث عن الموظف: {str(e)}'}), 500

# مسار API جديد للبحث عن الموظف وعرض نموذج المخالفة مع بياناته
@app.route('/violations/search-employee', methods=['POST'])
@login_required
def search_employee_for_violation():
    """مسار جديد للبحث عن الموظف وعرض نموذج المخالفة مع بياناته"""
    # الحصول على الرقم الوظيفي من النموذج
    employee_id = request.form.get('employee_id', '')

    if not employee_id:
        flash('الرجاء إدخال الرقم الوظيفي', 'danger')
        return redirect(url_for('new_violation'))

    # البحث عن الموظف
    employee = Employee.query.filter_by(employee_id=employee_id).first()

    if not employee:
        # محاولة البحث بطرق أخرى
        try:
            # البحث باستخدام LIKE
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()

            if not employee:
                # البحث باستخدام المعرف الرقمي
                try:
                    emp_id_int = int(employee_id)
                    employee = Employee.query.get(emp_id_int)
                except (ValueError, TypeError):
                    pass
        except Exception as e:
            print(f"Error searching for employee: {str(e)}")

    if not employee:
        flash('لم يتم العثور على الموظف', 'danger')
        return redirect(url_for('new_violation'))

    # التحقق من صلاحية الوصول
    if not current_user.is_admin:
        user_club_ids = [club.id for club in current_user.clubs]
        if employee.club_id not in user_club_ids:
            flash('ليس لديك صلاحية للوصول إلى بيانات هذا الموظف', 'danger')
            return redirect(url_for('new_violation'))

    # حساب عدد المخالفات في الشهر الحالي
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
    month_end = month_end - timedelta(days=1)

    violations_count = Violation.query.filter(
        Violation.employee_id == employee.id,
        Violation.violation_date >= month_start,
        Violation.violation_date <= month_end
    ).count()

    # الحصول على قائمة أنواع المخالفات النشطة
    violation_types = ViolationType.query.filter_by(is_active=True).all()

    # قائمة مصادر المخالفة
    violation_sources = ['مدبر المنطقه', 'مدير النادي', 'مراقبه الكاميرات', 'مدير الانديه']

    # التاريخ الحالي للعرض في النموذج
    current_date = date.today().strftime('%Y-%m-%d')

    # عرض نموذج المخالفة مع بيانات الموظف
    return render_template('violations/new.html',
                           title='إضافة مخالفة جديدة',
                           employee=employee,
                           violations_count=violations_count,
                           violation_types=violation_types,
                           violation_sources=violation_sources,
                           current_date=current_date,
                           pre_filled=True)


# مسار API جديد للبحث المباشر عن الموظف (محسن)
@app.route('/api/employee/direct-search', methods=['POST'])
@login_required
def direct_search_employee():
    try:
        # الحصول على الرقم الوظيفي من الطلب
        employee_id = request.form.get('employee_id', '')
        print(f"Direct search for employee with ID: {employee_id}")

        if not employee_id:
            print("Error: No employee ID provided")
            return jsonify({'error': 'الرقم الوظيفي غير موجود'}), 400

        # محاولة البحث بعدة طرق مختلفة
        employee = None

        # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            print(f"Found employee using exact match: {employee.name}")

        # الطريقة 2: البحث بعد إزالة المسافات
        if not employee:
            clean_id = str(employee_id).strip()
            employee = Employee.query.filter_by(employee_id=clean_id).first()
            if employee:
                print(f"Found employee after stripping spaces: {employee.name}")

        # الطريقة 3: البحث باستخدام LIKE
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
            if employee:
                print(f"Found employee using LIKE: {employee.name}")

        # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
                if employee:
                    print(f"Found employee using numeric ID: {employee.name}")
            except (ValueError, TypeError):
                pass

        # إذا لم يتم العثور على الموظف
        if not employee:
            print(f"Employee not found with ID: {employee_id}")
            return jsonify({'error': 'الموظف غير موجود'}), 404

        print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                print(f"Access denied for user {current_user.name} to employee {employee.name}")
                return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

        # حساب عدد المخالفات في الشهر الحالي
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        print(f"Violations count for employee {employee.name}: {violations_count}")

        # إرجاع بيانات الموظف
        response_data = {
            'name': employee.name,
            'role': employee.role,
            'club_id': employee.club_id,
            'club_name': employee.club.name,
            'violations_count': violations_count
        }

        print(f"Returning data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in direct_search_employee API: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'حدث خطأ أثناء البحث عن الموظف: {str(e)}'}), 500

# مسار API جديد للبحث البسيط عن الموظف
@app.route('/api/employee/simple-search', methods=['POST'])
@login_required
def simple_search_employee():
    try:
        # الحصول على الرقم الوظيفي من الطلب
        employee_id = request.form.get('employee_id', '')
        print(f"Simple search for employee with ID: {employee_id}")

        if not employee_id:
            return jsonify({'error': 'الرقم الوظيفي غير موجود'}), 400

        # محاولة البحث بعدة طرق مختلفة
        employee = None

        # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            print(f"Found employee using exact match: {employee.name}")

        # الطريقة 2: البحث بعد إزالة المسافات
        if not employee:
            clean_id = str(employee_id).strip()
            employee = Employee.query.filter_by(employee_id=clean_id).first()
            if employee:
                print(f"Found employee after stripping spaces: {employee.name}")

        # الطريقة 3: البحث باستخدام LIKE
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
            if employee:
                print(f"Found employee using LIKE: {employee.name}")

        # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
                if employee:
                    print(f"Found employee using numeric ID: {employee.name}")
            except (ValueError, TypeError):
                pass

        # إذا لم يتم العثور على الموظف
        if not employee:
            print(f"Employee not found with ID: {employee_id}")
            return jsonify({'error': 'الموظف غير موجود'}), 404

        print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                print(f"Access denied for user {current_user.name} to employee {employee.name}")
                return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

        # حساب عدد المخالفات في الشهر الحالي
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        print(f"Violations count for employee {employee.name}: {violations_count}")

        # إرجاع بيانات الموظف
        response_data = {
            'name': employee.name,
            'role': employee.role,
            'club_id': employee.club_id,
            'club_name': employee.club.name,
            'violations_count': violations_count
        }

        print(f"Returning data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in simple_search_employee API: {str(e)}")
        return jsonify({'error': f'حدث خطأ أثناء البحث عن الموظف: {str(e)}'}), 500
# مسار API جديد للبحث عن الموظف باستخدام الرقم الوظيفي
@app.route('/api/employee/find', methods=['POST'])
@login_required
def find_employee_by_id():
    try:
        # الحصول على الرقم الوظيفي من الطلب
        employee_id = request.form.get('employee_id', '')
        print(f"Finding employee with ID: {employee_id}")

        if not employee_id:
            return jsonify({'error': 'الرقم الوظيفي غير موجود'}), 400

        # محاولة البحث بعدة طرق مختلفة
        employee = None

        # الطريقة 1: البحث المباشر باستخدام الرقم الوظيفي كما هو
        employee = Employee.query.filter_by(employee_id=employee_id).first()
        if employee:
            print(f"Found employee using exact match: {employee.name}")

        # الطريقة 2: البحث بعد إزالة المسافات
        if not employee:
            clean_id = str(employee_id).strip()
            employee = Employee.query.filter_by(employee_id=clean_id).first()
            if employee:
                print(f"Found employee after stripping spaces: {employee.name}")

        # الطريقة 3: البحث باستخدام LIKE
        if not employee:
            employee = Employee.query.filter(Employee.employee_id.like(f"%{employee_id}%")).first()
            if employee:
                print(f"Found employee using LIKE: {employee.name}")

        # الطريقة 4: البحث باستخدام المعرف الرقمي مباشرة
        if not employee:
            try:
                emp_id_int = int(employee_id)
                employee = Employee.query.get(emp_id_int)
                if employee:
                    print(f"Found employee using numeric ID: {employee.name}")
            except (ValueError, TypeError):
                pass

        # إذا لم يتم العثور على الموظف
        if not employee:
            print(f"Employee not found with ID: {employee_id}")
            return jsonify({'error': 'الموظف غير موجود'}), 404

        print(f"Found employee: {employee.name}, ID: {employee.employee_id}, Club: {employee.club.name}")

        # التحقق من صلاحية الوصول
        if not current_user.is_admin:
            user_club_ids = [club.id for club in current_user.clubs]
            if employee.club_id not in user_club_ids:
                print(f"Access denied for user {current_user.name} to employee {employee.name}")
                return jsonify({'error': 'ليس لديك صلاحية للوصول إلى بيانات هذا الموظف'}), 403

        # حساب عدد المخالفات في الشهر الحالي
        today = date.today()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month + 1, 1) if today.month < 12 else date(today.year + 1, 1, 1)
        month_end = month_end - timedelta(days=1)

        violations_count = Violation.query.filter(
            Violation.employee_id == employee.id,
            Violation.violation_date >= month_start,
            Violation.violation_date <= month_end
        ).count()

        print(f"Violations count for employee {employee.name}: {violations_count}")

        # إرجاع بيانات الموظف
        response_data = {
            'name': employee.name,
            'role': employee.role,
            'club_id': employee.club_id,
            'club_name': employee.club.name,
            'violations_count': violations_count
        }

        print(f"Returning data: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in find_employee_by_id API: {str(e)}")
        return jsonify({'error': f'حدث خطأ أثناء البحث عن الموظف: {str(e)}'}), 500

# مسارات صفحة شموس
@app.route('/shumoos')
@login_required
def shumoos_list():
    # البحث والتصفية
    search_query = request.args.get('search', '')

    # التحقق مما إذا كان المستخدم مسؤولاً
    if current_user.is_admin:
        # المسؤول يرى جميع الأندية
        if search_query:
            clubs = Club.query.filter(Club.name.contains(search_query)).all()
        else:
            clubs = Club.query.all()
    else:
        # المستخدم العادي يرى فقط الأندية التابعة له
        if search_query:
            clubs = Club.query.join(user_clubs).filter(
                user_clubs.c.user_id == current_user.id,
                Club.name.contains(search_query)
            ).all()
        else:
            clubs = current_user.clubs

    # الحصول على آخر سجل لكل نادي
    clubs_with_latest_record = []
    for club in clubs:
        latest_record = Shumoos.query.filter_by(club_id=club.id).order_by(Shumoos.registration_date.desc()).first()
        record_count = Shumoos.query.filter_by(club_id=club.id).count()
        clubs_with_latest_record.append({
            'club': club,
            'latest_record': latest_record,
            'record_count': record_count
        })

    return render_template('shumoos/index.html',
                          title='سجل شموس',
                          clubs_with_latest_record=clubs_with_latest_record,
                          search_query=search_query)

@app.route('/shumoos/new', methods=['GET', 'POST'])
@login_required
def new_shumoos():
    # الحصول على قائمة النوادي
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # التحقق من وجود معرف نادي في الطلب
    selected_club_id = request.args.get('club_id')
    if selected_club_id:
        try:
            selected_club_id = int(selected_club_id)
        except ValueError:
            selected_club_id = None

    if request.method == 'POST':
        club_id = request.form.get('club_id')
        registered_count = request.form.get('registered_count')
        registration_date = request.form.get('registration_date')

        # التحقق من صحة البيانات
        if not club_id or not registered_count:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('new_shumoos'))

        try:
            registered_count = int(registered_count)
            if registered_count < 0:
                flash('يرجى إدخال عدد صحيح موجب')
                return redirect(url_for('new_shumoos'))
        except ValueError:
            flash('يرجى إدخال عدد صحيح للعدد المسجل')
            return redirect(url_for('new_shumoos'))

        # استخدام تاريخ اليوم مباشرة
        registration_date = date.today()

        # التحقق من عدم وجود سجل لنفس النادي في نفس اليوم
        existing_record = Shumoos.query.filter_by(
            club_id=club_id,
            registration_date=registration_date
        ).first()

        if existing_record:
            flash('يوجد بالفعل سجل لهذا النادي في هذا التاريخ')
            return redirect(url_for('edit_shumoos', id=existing_record.id))

        # إنشاء سجل جديد
        shumoos_record = Shumoos(
            club_id=club_id,
            registered_count=registered_count,
            registration_date=registration_date,
            created_by=current_user.id
        )

        db.session.add(shumoos_record)
        db.session.commit()

        flash('تم إضافة سجل شموس بنجاح!')
        # إذا كان هناك معرف نادي محدد، العودة إلى صفحة سجلات النادي
        if selected_club_id:
            return redirect(url_for('shumoos_club_records', club_id=club_id))
        else:
            return redirect(url_for('shumoos_list'))

    # تنسيق التاريخ بشكل أفضل (YYYY-MM-DD)
    today_formatted = date.today().strftime('%Y-%m-%d')

    return render_template('shumoos/new.html',
                          title='إضافة سجل شموس جديد',
                          clubs=clubs,
                          selected_club_id=selected_club_id,
                          today=today_formatted)

@app.route('/shumoos/record/<int:id>')
@login_required
def shumoos_record_detail(id):
    shumoos_record = Shumoos.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and shumoos_record.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا السجل')
        return redirect(url_for('shumoos_list'))

    return render_template('shumoos/record_detail.html',
                          title='تفاصيل سجل شموس',
                          shumoos_record=shumoos_record)

@app.route('/shumoos/club/<int:club_id>')
@login_required
def shumoos_club_records(club_id):
    # الحصول على النادي
    club = Club.query.get_or_404(club_id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا النادي')
        return redirect(url_for('shumoos_list'))

    # الحصول على سجلات النادي
    shumoos_records = Shumoos.query.filter_by(club_id=club_id).order_by(Shumoos.registration_date.desc()).all()

    return render_template('shumoos/club_records.html',
                          title=f'سجلات شموس - {club.name}',
                          club=club,
                          shumoos_records=shumoos_records)

@app.route('/shumoos/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_shumoos(id):
    shumoos_record = Shumoos.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and shumoos_record.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا السجل')
        return redirect(url_for('shumoos_list'))

    if request.method == 'POST':
        registered_count = request.form.get('registered_count')
        registration_date = request.form.get('registration_date')

        # التحقق من صحة البيانات
        if not registered_count:
            flash('يرجى ملء جميع الحقول المطلوبة')
            return redirect(url_for('edit_shumoos', id=id))

        try:
            registered_count = int(registered_count)
            if registered_count < 0:
                flash('يرجى إدخال عدد صحيح موجب')
                return redirect(url_for('edit_shumoos', id=id))
        except ValueError:
            flash('يرجى إدخال عدد صحيح للعدد المسجل')
            return redirect(url_for('edit_shumoos', id=id))

        # استخدام تاريخ السجل الحالي بدون تغيير
        new_registration_date = shumoos_record.registration_date

        # التحقق من عدم وجود سجل آخر لنفس النادي في نفس اليوم
        if new_registration_date != shumoos_record.registration_date:
            existing_record = Shumoos.query.filter_by(
                club_id=shumoos_record.club_id,
                registration_date=new_registration_date
            ).first()

            if existing_record and existing_record.id != shumoos_record.id:
                flash('يوجد بالفعل سجل لهذا النادي في هذا التاريخ')
                return redirect(url_for('edit_shumoos', id=id))

        # تحديث السجل
        shumoos_record.registered_count = registered_count
        shumoos_record.registration_date = new_registration_date
        shumoos_record.updated_at = datetime.now()

        db.session.commit()

        flash('تم تحديث سجل شموس بنجاح!')
        return redirect(url_for('shumoos_club_records', club_id=shumoos_record.club_id))

    return render_template('shumoos/edit.html',
                          title='تعديل سجل شموس',
                          shumoos_record=shumoos_record)

@app.route('/shumoos/<int:id>/delete', methods=['POST'])
@login_required
def delete_shumoos(id):
    shumoos_record = Shumoos.query.get_or_404(id)

    # التحقق من صلاحية الوصول
    if not current_user.is_admin and shumoos_record.club not in current_user.clubs:
        flash('ليس لديك صلاحية للوصول إلى هذا السجل')
        return redirect(url_for('shumoos_list'))

    db.session.delete(shumoos_record)
    db.session.commit()

    club_id = shumoos_record.club_id
    flash('تم حذف سجل شموس بنجاح!')
    return redirect(url_for('shumoos_club_records', club_id=club_id))

# مسارات تقارير التشيك
@app.route('/check-reports')
@login_required
def check_reports():
    # الحصول على الشهر والسنة من الطلب
    month = request.args.get('month', str(date.today().month))
    year = request.args.get('year', str(date.today().year))
    club_id = request.args.get('club_id', '')
    facility_id = request.args.get('facility_id', '')
    user_id = request.args.get('user_id', '')

    try:
        month = int(month)
        year = int(year)
        if club_id:
            club_id = int(club_id)
        if facility_id:
            facility_id = int(facility_id)
        if user_id:
            user_id = int(user_id)
    except ValueError:
        month = date.today().month
        year = date.today().year
        club_id = None
        facility_id = None
        user_id = None

    # الحصول على قائمة الأندية المتاحة للمستخدم
    if current_user.is_admin:
        clubs = Club.query.all()
    else:
        clubs = current_user.clubs

    # الحصول على قائمة المرافق
    facilities = Facility.query.all()

    # الحصول على قائمة المستخدمين
    users = User.query.all()

    # طباعة معلومات تشخيصية عن المرافق
    print("\n[DEBUG] معلومات المرافق:")
    for facility in facilities:
        print(f"[DEBUG] المرفق {facility.id}: {facility.name}")

    # طباعة معلومات تشخيصية عن الأندية
    print("\n[DEBUG] معلومات الأندية:")
    for club in clubs:
        print(f"[DEBUG] النادي {club.id}: {club.name}")

    # تحديد نطاق التاريخ للشهر المحدد
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    print(f"\n[DEBUG] نطاق التاريخ: {start_date} إلى {end_date}")

    # إنشاء قاموس لتخزين بيانات التقرير
    report_data = {}

    # تصفية الأندية إذا تم تحديد نادي معين
    filtered_clubs = [club for club in clubs if not club_id or club.id == club_id]

    # تصفية المرافق إذا تم تحديد مرفق معين
    filtered_facilities = [facility for facility in facilities if not facility_id or facility.id == facility_id]

    # تصفية الأندية حسب المستخدم إذا تم تحديد مستخدم معين
    if user_id:
        selected_user = User.query.get(user_id)
        if selected_user:
            if not selected_user.is_admin:  # إذا كان المستخدم ليس مسؤولاً، نعرض فقط الأندية المرتبطة به
                filtered_clubs = [club for club in filtered_clubs if club in selected_user.clubs]

    # جمع بيانات التشيك لكل نادي ومرفق
    for club in filtered_clubs:
        club_data = {}

        # الحصول على جميع التشيكات للنادي في الشهر المحدد
        checks = Check.query.filter(
            Check.club_id == club.id,
            Check.check_date >= start_date,
            Check.check_date <= end_date
        ).all()

        print(f"\n[DEBUG] النادي {club.name} - عدد التشيكات: {len(checks)}")
        for check in checks:
            print(f"[DEBUG] تشيك {check.id}: تاريخ {check.check_date}")

        if not checks:
            continue

        # حساب نسبة الامتثال لكل مرفق
        for facility in filtered_facilities:
            # التحقق من أن المرفق مرتبط بالنادي
            if facility not in club.facilities:
                continue

            # التحقق من وجود بنود نشطة للمرفق
            facility_items = FacilityItem.query.filter_by(facility_id=facility.id, is_active=True).all()
            if not facility_items:
                continue

            # متغيرات لحساب نسب الامتثال لكل مرفق في كل تشيك
            facility_percentages = []

            # طباعة معلومات تشخيصية
            print(f"\n[DEBUG] حساب نسبة الامتثال للنادي {club.name} والمرفق {facility.name}")
            print(f"[DEBUG] عدد التشيكات: {len(checks)}")

            # حساب نسبة الامتثال لكل تشيك
            for check in checks:
                # الحصول على بنود التشيك لهذا المرفق
                check_items = CheckItem.query.filter(
                    CheckItem.check_id == check.id,
                    CheckItem.facility_id == facility.id
                ).all()

                # إذا لم تكن هناك بنود لهذا المرفق في هذا التشيك، استمر
                if not check_items:
                    print(f"[DEBUG] لا توجد بنود للمرفق {facility.name} في التشيك {check.id}")
                    continue

                # عدد البنود المطابقة لهذا التشيك
                compliant_count = sum(1 for item in check_items if item.is_compliant)
                total_count = len(check_items)

                # حساب نسبة الامتثال لهذا المرفق في هذا التشيك
                if total_count > 0:
                    facility_check_percentage = (compliant_count / total_count * 100)
                    facility_percentages.append(facility_check_percentage)
                    print(f"[DEBUG] التشيك {check.id}: {compliant_count}/{total_count} = {facility_check_percentage:.1f}%")

            # حساب متوسط نسب الامتثال للمرفق في جميع التشيكات
            if facility_percentages:
                # حساب متوسط النسب المئوية للمرفق في جميع التشيكات
                average_percentage = sum(facility_percentages) / len(facility_percentages)
                percentage = int(average_percentage)
                print(f"[DEBUG] متوسط نسب الامتثال للمرفق {facility.name} في جميع التشيكات: {average_percentage:.1f}% => {percentage}%")

                # حساب إجمالي عدد البنود والبنود المطابقة للمرفق في جميع التشيكات
                total_check_items = 0
                total_compliant_items = 0

                for check in checks:
                    check_items = CheckItem.query.filter(
                        CheckItem.check_id == check.id,
                        CheckItem.facility_id == facility.id
                    ).all()

                    if check_items:
                        compliant_count = sum(1 for item in check_items if item.is_compliant)
                        total_count = len(check_items)

                        total_check_items += total_count
                        total_compliant_items += compliant_count

                # طباعة معلومات تشخيصية إضافية
                print(f"[DEBUG] النسبة المئوية النهائية للمرفق {facility.id} ({facility.name}): {percentage}%")
            else:
                percentage = 0
                total_check_items = 0
                total_compliant_items = 0
                print(f"[DEBUG] لا توجد بيانات لحساب النسبة المئوية")

            # تخزين النسبة في قاموس البيانات
            facility_percentage = percentage

            print(f"[DEBUG] النسبة المئوية النهائية للمرفق {facility.id} ({facility.name}): {facility_percentage}%")

            club_data[facility.id] = {
                'facility_name': facility.name,
                'percentage': facility_percentage,
                'total_items': total_check_items,
                'compliant_items': total_compliant_items
            }

        # إضافة بيانات النادي إلى التقرير
        if club_data:
            report_data[club.id] = {
                'club_name': club.name,
                'facilities': club_data
            }

    # إنشاء قائمة بالشهور للاختيار
    months = [
        {'value': 1, 'name': 'يناير'},
        {'value': 2, 'name': 'فبراير'},
        {'value': 3, 'name': 'مارس'},
        {'value': 4, 'name': 'أبريل'},
        {'value': 5, 'name': 'مايو'},
        {'value': 6, 'name': 'يونيو'},
        {'value': 7, 'name': 'يوليو'},
        {'value': 8, 'name': 'أغسطس'},
        {'value': 9, 'name': 'سبتمبر'},
        {'value': 10, 'name': 'أكتوبر'},
        {'value': 11, 'name': 'نوفمبر'},
        {'value': 12, 'name': 'ديسمبر'}
    ]

    # إنشاء قائمة بالسنوات للاختيار (السنة الحالية والسنتين السابقتين)
    current_year = date.today().year
    years = [current_year - 2, current_year - 1, current_year, current_year + 1]

    return render_template('reports/check_reports.html',
                          title='تقارير التشيك',
                          report_data=report_data,
                          clubs=clubs,
                          facilities=facilities,
                          users=users,
                          months=months,
                          years=years,
                          selected_month=month,
                          selected_year=year,
                          selected_club_id=club_id,
                          selected_facility_id=facility_id,
                          selected_user_id=user_id)

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
