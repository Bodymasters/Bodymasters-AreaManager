import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات المستخدمين من SQLite
sqlite_conn = sqlite3.connect('app.db')
users_df = pd.read_sql_query("SELECT * FROM user", sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(users_df)} مستخدم من قاعدة البيانات المحلية")

# تحويل عمود is_admin من عدد صحيح إلى قيمة منطقية
if 'is_admin' in users_df.columns:
    users_df['is_admin'] = users_df['is_admin'].astype(bool)
    print("تم تحويل عمود is_admin إلى قيم منطقية")

# حفظ البيانات في ملف CSV للاحتفاظ بها
users_df.to_csv('users_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات المستخدمين في ملف CSV")

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
    
    # إدراج البيانات في جدول المستخدمين في Supabase
    if len(users_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(users_df.columns)
        values = [tuple(row) for row in users_df.values]
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO "user" ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام
        execute_values(cursor, insert_query, values)
        pg_conn.commit()
        
        print(f"تم نقل {len(users_df)} مستخدم إلى Supabase بنجاح")
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM "user"')
    count = cursor.fetchone()[0]
    print(f"عدد المستخدمين في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")