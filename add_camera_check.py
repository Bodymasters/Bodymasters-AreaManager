import sqlite3
from datetime import date

# فتح اتصال بقاعدة البيانات
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

try:
    # إضافة متابعة جديدة
    cursor.execute("""
    INSERT INTO camera_check (check_date, club_id, user_id, status, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (date.today().isoformat(), 1, 1, 'active', 'متابعة تجريبية'))
    
    check_id = cursor.lastrowid
    print(f"تم إضافة متابعة جديدة برقم {check_id}")
    
    # إضافة فترات المتابعة
    time_slots = ['08:00', '12:00', '16:00', '20:00']
    for time_slot in time_slots:
        cursor.execute("""
        INSERT INTO camera_time_slot (camera_check_id, time_slot, is_working)
        VALUES (?, ?, ?)
        """, (check_id, time_slot, 0))
    
    print(f"تم إضافة {len(time_slots)} فترة متابعة للمتابعة رقم {check_id}")
    
    # حفظ التغييرات
    conn.commit()
    print("تم حفظ التغييرات بنجاح!")
except Exception as e:
    conn.rollback()
    print(f"خطأ في إضافة المتابعة: {str(e)}")
finally:
    # إغلاق الاتصال
    conn.close()
