import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import time

# قائمة بأسماء الجداول التي تم نقلها بالفعل (لتجنب نقلها مرة أخرى)
already_migrated = ['user', 'club', 'check', 'check_item']

# استخراج أسماء جميع الجداول من SQLite
sqlite_conn = sqlite3.connect('app.db')
cursor = sqlite_conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [table[0] for table in cursor.fetchall()]
cursor.close()
sqlite_conn.close()

print(f"تم العثور على {len(tables)} جدول في قاعدة البيانات المحلية")
print("الجداول: " + ", ".join(tables))

# استبعاد الجداول التي تم نقلها بالفعل
tables_to_migrate = [table for table in tables if table not in already_migrated]
print(f"سيتم نقل {len(tables_to_migrate)} جدول")
print("الجداول المراد نقلها: " + ", ".join(tables_to_migrate))

# الاتصال بقاعدة بيانات Supabase
db_params = {
    'host': 'db.xcjvscvcrwxbivrhuxtz.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Bodymasters@1298',  # استبدل هذا بكلمة المرور الخاصة بك
    'port': '5432'
}

# تحديد الأعمدة التي قد تكون منطقية
boolean_columns = ['is_compliant', 'is_active', 'is_deleted', 'is_admin', 'is_enabled', 'is_completed']

# نقل كل جدول
for table_name in tables_to_migrate:
    print(f"\nجاري نقل جدول {table_name}...")
    
    # استخراج بيانات الجدول من SQLite
    sqlite_conn = sqlite3.connect('app.db')
    try:
        table_df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', sqlite_conn)
        print(f"  تم استخراج {len(table_df)} سجل من جدول {table_name}")
    except Exception as e:
        print(f"  حدث خطأ أثناء استخراج البيانات من جدول {table_name}: {e}")
        sqlite_conn.close()
        continue
    sqlite_conn.close()
    
    # تحويل الأعمدة التي قد تكون منطقية
    for col in boolean_columns:
        if col in table_df.columns:
            table_df[col] = table_df[col].astype(bool)
    
    # حفظ البيانات في ملف CSV للاحتفاظ بها
    backup_file = f'{table_name}_backup.csv'
    table_df.to_csv(backup_file, index=False, encoding='utf-8-sig')
    print(f"  تم حفظ بيانات جدول {table_name} في ملف {backup_file}")
    
    try:
        # الاتصال بقاعدة البيانات
        pg_conn = psycopg2.connect(**db_params)
        cursor = pg_conn.cursor()
        
        # تعطيل قيود المفتاح الأجنبي مؤقتاً
        cursor.execute('SET session_replication_role = replica;')
        
        # إدراج البيانات في الجدول في Supabase
        if len(table_df) > 0:
            # تحضير البيانات للإدراج
            columns = list(table_df.columns)
            
            # تحويل DataFrame إلى قائمة من السجلات
            records = table_df.to_dict('records')
            
            # إنشاء استعلام الإدراج
            insert_query = f"""
            INSERT INTO "{table_name}" ({', '.join([f'"{col}"' for col in columns])})
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """
            
            # تنفيذ الاستعلام باستخدام execute_values
            execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
            pg_conn.commit()
            
            print(f"  تم نقل {len(table_df)} سجل إلى جدول {table_name} في Supabase بنجاح")
        
        # إعادة تفعيل قيود المفتاح الأجنبي
        cursor.execute('SET session_replication_role = DEFAULT;')
        pg_conn.commit()
        
        # التحقق من البيانات
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
        print(f"  عدد السجلات في جدول {table_name} في قاعدة بيانات Supabase: {count}")
        
        cursor.close()
        pg_conn.close()
        
    except Exception as e:
        print(f"  حدث خطأ أثناء نقل جدول {table_name}: {e}")
    
    # انتظار قليلاً بين نقل الجداول لتجنب الضغط على قاعدة البيانات
    time.sleep(1)

print("\nتم الانتهاء من نقل جميع الجداول")