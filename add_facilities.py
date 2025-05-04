from app import app, db, Facility

# قائمة المرافق
facilities = [
    "مسبح",
    "ملعب كرة قدم",
    "صالة رياضية",
    "ملعب تنس",
    "ساونا",
    "جاكوزي",
    "قاعة متعددة الأغراض"
]

# إضافة المرافق إلى قاعدة البيانات
with app.app_context():
    for facility_name in facilities:
        # التحقق من وجود المرفق مسبقاً
        existing = Facility.query.filter_by(name=facility_name).first()
        if not existing:
            facility = Facility(name=facility_name)
            db.session.add(facility)
            print(f"تمت إضافة المرفق: {facility_name}")
    
    # حفظ التغييرات
    db.session.commit()
    print("تم إضافة المرافق بنجاح!")
