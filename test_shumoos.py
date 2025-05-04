from app import app, db, Shumoos, Club, User
from datetime import date

# إنشاء سجل تجريبي في جدول شموس
with app.app_context():
    # التحقق من وجود نادي ومستخدم
    club = Club.query.first()
    user = User.query.first()
    
    if club and user:
        # إنشاء سجل تجريبي
        test_record = Shumoos(
            club_id=club.id,
            registered_count=100,
            registration_date=date.today(),
            created_by=user.id
        )
        
        # إضافة السجل إلى قاعدة البيانات
        db.session.add(test_record)
        db.session.commit()
        
        print(f"تم إنشاء سجل تجريبي بنجاح! المعرف: {test_record.id}")
        
        # التحقق من وجود السجل
        record = Shumoos.query.get(test_record.id)
        if record:
            print(f"تم التحقق من وجود السجل: النادي: {record.club.name}, العدد: {record.registered_count}")
        else:
            print("لم يتم العثور على السجل!")
    else:
        print("لا يوجد نادي أو مستخدم في قاعدة البيانات!")
