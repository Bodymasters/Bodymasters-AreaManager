import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات جدول check_item من SQLite
sqlite_conn = sqlite3.connect('app.db')
try:
    check_item_df = pd.read_sql_query('SELECT * FROM check_item', sqlite_conn)
    print(f"تم استخراج {len(check_item_df)} سجل من جدول check_item")
except Exception as e:
    print(f"حدث خطأ أثناء استخراج البيانات: {e}")
    sqlite_conn.close()
    exit(1)
sqlite_conn.close()

# تحويل الأعمدة التي قد تكون منطقية
boolean_columns = ['is_compliant', 'is_active', 'is_deleted']
for col in boolean_columns:
    if col in check_item_df.columns:
        check_item_df[col] = check_item_df[col].astype(bool)

# حفظ البيانات في ملف CSV للاحتفاظ بها
check_item_df.to_csv('check_item_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات جدول check_item في ملف check_item_backup.csv")

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
    
    # إدراج البيانات في جدول check_item في Supabase
    if len(check_item_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(check_item_df.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = check_item_df.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO check_item ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(check_item_df)} سجل إلى جدول check_item في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM check_item')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول check_item في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")