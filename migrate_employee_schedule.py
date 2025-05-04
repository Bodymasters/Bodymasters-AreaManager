import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات جدول employee_schedule من SQLite
sqlite_conn = sqlite3.connect('app.db')
schedule_df = pd.read_sql_query('SELECT * FROM employee_schedule', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(schedule_df)} سجل من جدول employee_schedule")

# معالجة قيم التاريخ الفارغة
date_columns = ['allocation_from', 'allocation_to', 'allocation_day']
for col in date_columns:
    if col in schedule_df.columns:
        # استبدال القيم الفارغة بـ NULL
        schedule_df[col] = schedule_df[col].replace('', None)

# حفظ البيانات في ملف CSV للاحتفاظ بها
schedule_df.to_csv('employee_schedule_fixed.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات جدول employee_schedule في ملف employee_schedule_fixed.csv")

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
    
    # إدراج البيانات في جدول employee_schedule في Supabase
    if len(schedule_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(schedule_df.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = schedule_df.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO employee_schedule ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(schedule_df)} سجل إلى جدول employee_schedule في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM employee_schedule')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول employee_schedule في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")