import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# استخراج بيانات عناصر التشيك من SQLite
sqlite_conn = sqlite3.connect('app.db')
check_items_df = pd.read_sql_query('SELECT * FROM check_item', sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(check_items_df)} عنصر تشيك من قاعدة البيانات المحلية")

# تحويل الأعمدة المنطقية من أرقام صحيحة إلى قيم منطقية
if 'is_compliant' in check_items_df.columns:
    check_items_df['is_compliant'] = check_items_df['is_compliant'].astype(bool)

# حفظ البيانات في ملف CSV للاحتفاظ بها
check_items_df.to_csv('check_items_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات عناصر التشيك في ملف CSV")

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
    
    # تعطيل قيود المفتاح الأجنبي مؤقتاً
    cursor.execute('SET session_replication_role = replica;')
    
    # إدراج البيانات في جدول عناصر التشيك في Supabase
    if len(check_items_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(check_items_df.columns)
        
        # تحويل DataFrame إلى قائمة من السجلات
        records = check_items_df.to_dict('records')
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO check_item ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام باستخدام execute_values
        execute_values(cursor, insert_query, [tuple(record.values()) for record in records])
        pg_conn.commit()
        
        print(f"تم نقل {len(check_items_df)} عنصر تشيك إلى Supabase بنجاح")
    
    # إعادة تفعيل قيود المفتاح الأجنبي
    cursor.execute('SET session_replication_role = DEFAULT;')
    pg_conn.commit()
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM check_item')
    count = cursor.fetchone()[0]
    print(f"عدد عناصر التشيك في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")