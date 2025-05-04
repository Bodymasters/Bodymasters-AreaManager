import sqlite3
import sys

def delete_camera_check(check_id):
    """
    حذف متابعة الكاميرات وفتراتها مباشرة من قاعدة البيانات
    """
    print(f"بدء حذف المتابعة رقم {check_id}")
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    try:
        # حذف فترات المتابعة أولاً
        cursor.execute("DELETE FROM camera_time_slot WHERE camera_check_id = ?", (check_id,))
        time_slots_deleted = cursor.rowcount
        print(f"تم حذف {time_slots_deleted} فترة متابعة للمتابعة {check_id}")
        
        # حذف المتابعة نفسها
        cursor.execute("DELETE FROM camera_check WHERE id = ?", (check_id,))
        checks_deleted = cursor.rowcount
        print(f"تم حذف {checks_deleted} متابعة برقم {check_id}")
        
        conn.commit()
        print(f"تم حذف المتابعة رقم {check_id} بنجاح!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"خطأ في حذف المتابعة: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("الاستخدام: python direct_delete.py <check_id>")
        sys.exit(1)
    
    try:
        check_id = int(sys.argv[1])
        success = delete_camera_check(check_id)
        
        if success:
            print(f"تم حذف المتابعة رقم {check_id} بنجاح!")
            sys.exit(0)
        else:
            print(f"فشل في حذف المتابعة رقم {check_id}!")
            sys.exit(1)
    except ValueError:
        print("يجب أن يكون معرف المتابعة رقمًا صحيحًا")
        sys.exit(1)
