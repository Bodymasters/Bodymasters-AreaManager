import sqlite3

def reset_camera_tables():
    """
    حذف جميع البيانات من جداول متابعة الكاميرات وإعادة إنشائها
    """
    print("بدء إعادة تعيين جداول متابعة الكاميرات...")
    
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    try:
        # حذف الجداول الحالية
        cursor.execute("DROP TABLE IF EXISTS camera_time_slot")
        cursor.execute("DROP TABLE IF EXISTS camera_check")
        print("تم حذف الجداول القديمة")
        
        # إنشاء جدول camera_check
        cursor.execute("""
        CREATE TABLE camera_check (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_date DATE NOT NULL,
            club_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (club_id) REFERENCES club (id),
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        """)
        print("تم إنشاء جدول camera_check")
        
        # إنشاء جدول camera_time_slot
        cursor.execute("""
        CREATE TABLE camera_time_slot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_check_id INTEGER NOT NULL,
            time_slot VARCHAR(10) NOT NULL,
            is_working BOOLEAN DEFAULT 0,
            FOREIGN KEY (camera_check_id) REFERENCES camera_check (id) ON DELETE CASCADE
        )
        """)
        print("تم إنشاء جدول camera_time_slot")
        
        conn.commit()
        print("تم إعادة تعيين جداول متابعة الكاميرات بنجاح!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"خطأ في إعادة تعيين الجداول: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    reset_camera_tables()
