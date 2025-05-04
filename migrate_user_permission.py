import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات جدول user_permission من SQLite
sqlite_conn = sqlite3.connect('app.db')
user_permission_df = pd.read_sql_query('SELECT * FROM user_permission', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(user_permission_df)} سجل من جدول user_permission")

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
    
    # استخراج أزواج (user_id, permission_id) الموجودة بالفعل في جدول user_permission في Supabase
    cursor.execute('SELECT user_id, permission_id FROM user_permission')
    existing_pairs = [(row[0], row[1]) for row in cursor.fetchall()]
    print(f"عدد الأزواج الموجودة بالفعل في جدول user_permission: {len(existing_pairs)}")
    
    # استبعاد السجلات التي تحتوي على أزواج موجودة بالفعل
    user_permission_df['pair'] = list(zip(user_permission_df['user_id'], user_permission_df['permission_id']))
    user_permission_df_filtered = user_permission_df[~user_permission_df['pair'].isin(existing_pairs)]
    user_permission_df_filtered = user_permission_df_filtered.drop('pair', axis=1)
    print(f"عدد السجلات بعد استبعاد الأزواج المكررة: {len(user_permission_df_filtered)}")
    
    # تعطيل قيود المفتاح الأجنبي مؤقت<|im_start|>
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول user_permission في Supabase
    if len(user_permission_df_filtered) > 0:
        # تحضير البيانات للإدراج
        columns = list(user_permission_df_filtered.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = user_permission_df_filtered.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO user_permission ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(user_permission_df_filtered)} سجل إلى جدول user_permission في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM user_permission')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول user_permission في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")