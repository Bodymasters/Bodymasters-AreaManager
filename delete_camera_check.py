import sqlite3
import sys

def delete_camera_check(check_id):
    """
    حذف متابعة الكاميرات وفتراتها
    """
    print(f"بدء حذف المتابعة رقم {check_id}")
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # التحقق من وجود المتابعة
    cursor.execute("SELECT id FROM camera_check WHERE id = ?", (check_id,))
    check_exists = cursor.fetchone()
    print(f"هل المتابعة موجودة: {check_exists is not None}")
    
    if not check_exists:
        print(f"المتابعة رقم {check_id} غير موجودة!")
        conn.close()
        return False
    
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
        print("الاستخدام: python delete_camera_check.py <check_id>")
        sys.exit(1)
    
    check_id = int(sys.argv[1])
    success = delete_camera_check(check_id)
    
    if success:
        print(f"تم حذف المتابعة رقم {check_id} بنجاح!")
    else:
        print(f"فشل في حذف المتابعة رقم {check_id}!")
