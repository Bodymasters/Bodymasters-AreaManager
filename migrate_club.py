import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات جدول club من SQLite
sqlite_conn = sqlite3.connect('app.db')
club_df = pd.read_sql_query('SELECT * FROM club', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(club_df)} سجل من جدول club")

# تحويل الأعمدة التي قد تكون منطقية
boolean_columns = ['is_active', 'is_deleted']
for col in boolean_columns:
    if col in club_df.columns:
        club_df[col] = club_df[col].astype(bool)

# حفظ البيانات في ملف CSV للاحتفاظ بها
club_df.to_csv('club_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات جدول club في ملف club_backup.csv")

# الاتصال بقاعدة بيانات Supabase
db_params = {
    'host': 'db.xcjvscvcrwxbivrhuxtz.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Bodymasters@1298',
    'port': '5432'
}

try:
    # الاتصال بقاعدة البيانات
    pg_conn = psycopg2.connect(**db_params)
    cursor = pg_conn.cursor()
    
    # تعطيل قيود المفتاح الأجنبي مؤقت<|im_start|>
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول club في Supabase
    if len(club_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(club_df.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = club_df.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO club ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(club_df)} سجل إلى جدول club في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM club')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول club في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")