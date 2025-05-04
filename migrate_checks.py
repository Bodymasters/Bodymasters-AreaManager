import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات التشيك من SQLite
sqlite_conn = sqlite3.connect('app.db')
checks_df = pd.read_sql_query('SELECT * FROM "check"', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(checks_df)} تشيك من قاعدة البيانات المحلية")

# حفظ البيانات في ملف CSV للاحتفاظ بها
checks_df.to_csv('checks_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات التشيك في ملف CSV")

# الاتصال بقاعدة بيانات Supabase
db_params = {
    'host': 'db.xcjvscvcrwxbivrhuxtz.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Bodymasters@1298',  # استبدل هذا بكلمة المرور الخاصة بك
    'port': '5432'
}

try:
    # الاتصال بقاعدة البيانات
    pg_conn = psycopg2.connect(**db_params)
    cursor = pg_conn.cursor()
    
    # تعطيل قيود المفتاح الأجنبي مؤقت سوه
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول التشيك في Supabase
    if len(checks_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(checks_df.columns)
        values = [tuple(row) for row in checks_df.values]
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO "check" ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام
        execute_values(cursor, insert_query, values)
        pg_conn.commit()
        
        print(f"تم نقل {len(checks_df)} تشيك إلى Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM "check"')
    count = cursor.fetchone()[0]
    print(f"عدد التشيكات في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")