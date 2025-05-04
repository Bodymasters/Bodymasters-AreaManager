import sqlite3
import psycopg2

# استخراج هيكل الجدول من SQLite
sqlite_conn = sqlite3.connect('app.db')
cursor = sqlite_conn.cursor()
cursor.execute("PRAGMA table_info(sales_target);")
sqlite_columns = cursor.fetchall()
sqlite_conn.close()

print("هيكل جدول sales_target في SQLite:")
for column in sqlite_columns:
    print(f"  اسم العمود: {column[1]}, النوع: {column[2]}")

# الاتصال بقاعدة بيانات Supabase
db_params = {
    'host': 'db.xcjvscvcrwxbivrhuxtz.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Bodymasters@1298',  # استبدل هذا بكلمة المرور الخاصة بك
    'port': '5432'
}

# استخراج هيكل الجدول من Supabase
pg_conn = psycopg2.connect(**db_params)
cursor = pg_conn.cursor()
cursor.execute("""
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'sales_target'
ORDER BY ordinal_position;
""")
supabase_columns = cursor.fetchall()
pg_conn.close()

print("\nهيكل جدول sales_target في Supabase:")
for column in supabase_columns:
    print(f"  اسم العمود: {column[0]}, النوع: {column[1]}")