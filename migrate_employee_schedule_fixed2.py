import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

# استخراج بيانات جدول employee_schedule من SQLite
sqlite_conn = sqlite3.connect('app.db')
schedule_df = pd.read_sql_query('SELECT * FROM employee_schedule', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(schedule_df)} سجل من جدول employee_schedule من SQLite")

# معالجة القيم الفارغة والقيم NaN
for col in schedule_df.columns:
    # استبدال القيم الفارغة والقيم NaN بـ None
    schedule_df[col] = schedule_df[col].replace('', None)
    schedule_df[col] = schedule_df[col].replace(np.nan, None)

# حفظ البيانات في ملف CSV للاحتفاظ بها
schedule_df.to_csv('employee_schedule_fixed2.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات جدول employee_schedule في ملف employee_schedule_fixed2.csv")

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
    
    # إنشاء جدول مؤقت لتخزين البيانات
    cursor.execute("""
    CREATE TEMP TABLE temp_employee_schedule (
        id INTEGER,
        employee_id INTEGER,
        club_id INTEGER,
        shift1_start TEXT,
        shift1_end TEXT,
        shift2_start TEXT,
        shift2_end TEXT,
        work_days TEXT,
        off_days TEXT,
        allocation_from TEXT,
        allocation_to TEXT,
        allocation_day TEXT,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        shift_type TEXT,
        work_hours INTEGER
    );
    """)
    pg_conn.commit()
    
    # إدراج البيانات في الجدول المؤقت
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
            cursor.execute("""
            INSERT INTO temp_employee_schedule (
                id, employee_id, club_id, shift1_start, shift1_end, shift2_start, shift2_end,
                work_days, off_days, allocation_from, allocation_to, allocation_day,
                created_at, updated_at, shift_type, work_hours
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, data)
            pg_conn.commit()
        except Exception as e:
            pg_conn.rollback()
            print(f"حدث خطأ أثناء إدراج السجل {row['id']} في الجدول المؤقت: {e}")
    
    # نقل البيانات من الجدول المؤقت إلى جدول employee_schedule
    cursor.execute("""
    INSERT INTO employee_schedule (
        id, employee_id, club_id, shift1_start, shift1_end, shift2_start, shift2_end,
        work_days, off_days, created_at, updated_at, shift_type, work_hours
    )
    SELECT
        id, employee_id, club_id, shift1_start, shift1_end, shift2_start, shift2_end,
        work_days, off_days, created_at, updated_at, shift_type, work_hours
    FROM temp_employee_schedule
    ON CONFLICT (id) DO NOTHING;
    """)
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM employee_schedule')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول employee_schedule في قاعدة بيانات Supabase: {count}")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")