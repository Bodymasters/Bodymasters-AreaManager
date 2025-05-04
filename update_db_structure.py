import os
import sqlite3

# الحصول على مسار قاعدة البيانات
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'area_manager.db')

def add_facility_id_column():
    """إضافة عمود facility_id إلى جدول critical_issue"""
    try:
        # اتصال بقاعدة البيانات
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # التحقق مما إذا كان العمود موجوداً بالفعل
        cursor.execute("PRAGMA table_info(critical_issue)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'facility_id' not in column_names:
            # إضافة العمود
            cursor.execute("ALTER TABLE critical_issue ADD COLUMN facility_id INTEGER REFERENCES facility(id)")
            conn.commit()
            print("تم إضافة عمود facility_id بنجاح!")
        else:
            print("عمود facility_id موجود بالفعل.")
        
        conn.close()
        return True
    except Exception as e:
        print(f"حدث خطأ أثناء إضافة العمود: {str(e)}")
        return False

if __name__ == "__main__":
    # محاولة إضافة العمود
    if add_facility_id_column():
        print("تم تحديث قاعدة البيانات بنجاح!")
    else:
        print("فشل تحديث قاعدة البيانات.")
