import sqlite3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid

# استخراج بيانات النوادي من SQLite
sqlite_conn = sqlite3.connect('app.db')
clubs_df = pd.read_sql_query("SELECT * FROM club", sqlite_conn)
sqlite_conn.close()

print(f"تم استخراج {len(clubs_df)} نادي من قاعدة البيانات المحلية")

# معالجة القيم المكررة في عمود location
if 'location' in clubs_df.columns:
    # تحديد القيم المكررة
    duplicate_locations = clubs_df['location'].value_counts()
    duplicate_locations = duplicate_locations[duplicate_locations > 1].index.tolist()
    
    # إضافة قيمة فريدة للقيم المكررة
    for loc in duplicate_locations:
        # تحديد الصفوف التي تحتوي على القيمة المكررة
        duplicate_rows = clubs_df[clubs_df['location'] == loc].index.tolist()
        
        # تعديل القيم المكررة باستثناء الأولى
        for i, idx in enumerate(duplicate_rows[1:], 1):
            clubs_df.at[idx, 'location'] = f"{loc} {i}"
    
    print("تم معالجة القيم المكررة في عمود location")

# حفظ البيانات في ملف CSV للاحتفاظ بها
clubs_df.to_csv('clubs_backup.csv', index=False, encoding='utf-8-sig')
print("تم حفظ بيانات النوادي في ملف CSV")

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
    
    # إدراج البيانات في جدول النوادي في Supabase
    if len(clubs_df) > 0:
        # تحضير البيانات للإدراج
        columns = list(clubs_df.columns)
        values = [tuple(row) for row in clubs_df.values]
        
        # إنشاء استعلام الإدراج
        insert_query = f"""
        INSERT INTO club ({', '.join([f'"{col}"' for col in columns])})
        VALUES %s
        ON CONFLICT (id) DO NOTHING
        """
        
        # تنفيذ الاستعلام
        execute_values(cursor, insert_query, values)
        pg_conn.commit()
        
        print(f"تم نقل {len(clubs_df)} نادي إلى Supabase بنجاح")
    
    # التحقق من البيانات
    cursor.execute('SELECT COUNT(*) FROM club')
    count = cursor.fetchone()[0]
    print(f"عدد النوادي في قاعدة بيانات Supabase: {count}")
    
    cursor.close()
    pg_conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")