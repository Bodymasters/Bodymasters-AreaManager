import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys

# التحقق من وجود اسم الجدول كمعامل
if len(sys.argv) < 2:
    print("الرجاء تحديد اسم الجدول المراد نقله")
    print("مثال: python migrate_table.py violation")
    sys.exit(1)

# اسم الجدول المراد نقله
table_name = sys.argv[1]

# استخراج بيانات الجدول من SQLite
sqlite_conn = sqlite3.connect('app.db')
try:
    table_df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', sqlite_conn)
    print(f"تم استخراج {len(table_df)} سجل من جدول {table_name}")
except Exception as e:
    print(f"حدث خطأ أثناء استخراج البيانات: {e}")
    sqlite_conn.close()
    sys.exit(1)
sqlite_conn.close()

# تحويل الأعمدة التي قد تكون منطقية
boolean_columns = ['is_compliant', 'is_active', 'is_deleted', 'is_admin', 'is_enabled', 'is_completed', 'is_imported', 'is_working', 'is_signed']
for col in boolean_columns:
    if col in table_df.columns:
        table_df[col] = table_df[col].astype(bool)

# حفظ البيانات في ملف CSV للاحتفاظ بها
backup_file = f'{table_name}_backup.csv'
table_df.to_csv(backup_file, index=False, encoding='utf-8-sig')
print(f"تم حفظ بيانات جدول {table_name} في ملف {backup_file}")

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
    
    # إدراج البيانات في الجدول في Supabase
    if len(table_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(table_df.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = table_df.to_dict('records')
        
        # إنشاء استعلام الإدراج
        # تحقق من وجود عمود id في الجدول
        cursor.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}' AND column_name = 'id'
        """)
        has_id_column = cursor.fetchone() is not None
        
        if has_id_column:
            insert_query = f"""
            INSERT INTO "{table_name}" ({', '.join([f'"{col}"' for col in columns])})
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """
        else:
            insert_query = f"""
            INSERT INTO "{table_name}" ({', '.join([f'"{col}"' for col in columns])})
            VALUES %s
            """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(table_df)} سجل إلى جدول {table_name} في Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
    count = cursor.fetchone()[0]
    print(f"عدد السجلات في جدول {table_name} في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")