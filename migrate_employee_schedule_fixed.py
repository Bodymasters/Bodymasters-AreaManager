import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج هيكل جدول employee_schedule في Supabase
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
    
    # استخراج هيكل الجدول من Supabase
    cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'employee_schedule'
    ORDER BY ordinal_position;
    """)
    supabase_columns = cursor.fetchall()
    
    print("هيكل جدول employee_schedule في Supabase:")
    for column in supabase_columns:
        print(f"  اسم العمود: {column[0]}, النوع: {column[1]}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")

# استخراج بيانات جدول employee_schedule من SQLite
sqlite_conn = sqlite3.connect('app.db')
schedule_df = pd.read_sql_query('SELECT * FROM employee_schedule', sqlite_conn)
sqlite_conn.close()

print(f"\nتم استخراج {len(schedule_df)} سجل من جدول employee_schedule من SQLite")

# تحويل الأعمدة التي قد تكون تواريخ
date_columns = ['allocation_from', 'allocation_to', 'allocation_day']
for col in date_columns:
    if col in schedule_df.columns:
        # استبدال القيم الفارغة والقيم غير الصالحة بـ NULL
        schedule_df[col] = pd.to_datetime(schedule_df[col], errors='coerce')

# حفظ البيانات في ملف CSV للاحتفاظ بها
schedule_df.to_csv('employee_schedule_fixed.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات جدول employee_schedule في ملف employee_schedule_fixed.csv")

# إنشاء استعلام SQL لإدراج البيانات في جدول employee_schedule
insert_sql = """
INSERT INTO employee_schedule (
    id, employee_id, club_id, shift1_start, shift1_end, shift2_start, shift2_end,
    work_days, off_days, allocation_from, allocation_to, allocation_day,
    created_at, updated_at, shift_type, work_hours
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO NOTHING;
"""

try:
    # الاتصال بقاعدة البيانات
    pg_conn = psycopg2.connect(**db_params)
    cursor = pg_conn.cursor()
    
    # تعطيل قيود المفتاح الأجنبي مؤقت<|im_start|>
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول employee_schedule في Supabase
    inserted_count = 0
    for _, row in schedule_df.iterrows():
        try:
            # تحضير البيانات للإدراج
            data = (
                row['id'], row['employee_id'], row['club_id'],
                row['shift1_start'], row['shift1_end'], row['shift2_start'], row['shift2_end'],
                row['work_days'], row['off_days'],
                row['allocation_from'], row['allocation_to'], row['allocation_day'],
                row['created_at'], row['updated_at'], row['shift_type'], row['work_hours']
            )
            
            # تنفيذ الاستعلام
            cursor.execute(insert_sql, data)
            pg_conn.commit()
            inserted_count += 1
        except Exception as e:
            pg_conn.rollback()
            print(f"حدث خطأ أثناء إدراج السجل {row['id']}: {e}")
    
    print(f"تم نقل {inserted_count} سجل إلى جدول employee_schedule في Supabase بنجاح")
    
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