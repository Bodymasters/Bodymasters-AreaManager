import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات جدول permission من SQLite
sqlite_conn = sqlite3.connect('app.db')
permission_df = pd.read_sql_query('SELECT * FROM permission', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(permission_df)} سجل من جدول permission")

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
    
    # استخراج الأكواد الموجودة بالفعل في جدول permission في Supabase
    cursor.execute('SELECT code FROM permission')
    existing_codes = [row[0] for row in cursor.fetchall()]
    print(f"عدد الأكواد الموجودة بالفعل في جدول permission: {len(existing_codes)}")
    
    # استبعاد السجلات التي تحتوي على أكواد موجودة بالفعل
    permission_df_filtered = permission_df[~permission_df['code'].isin(existing_codes)]
    print(f"عدد السجلات بعد استبعاد الأكواد المكررة: {len(permission_df_filtered)}")
    
    # تعطيل قيود المفتاح الأجنبي مؤقت<|im_start|>
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول permission في Supabase
    if len(permission_df_filtered) > 0:
        # تحضير البيانات للإدراج
        columns = list(permission_df_filtered.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = permission_df_filtered.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO permission ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(permission_df_filtered)} سجل إلى جدول permission في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM permission')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول permission في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")