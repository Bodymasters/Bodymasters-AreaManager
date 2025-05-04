import psycopg2

# الاتصال بقاعدة بيانات Supabase
db_params = {
    'host': 'db.xcjvscvcrwxbivrhuxtz.supabase.co',
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Bodymasters@1298',
    'port': '5432'
}

# الاستعلام الذي سيتم تنفيذه
query = """
CREATE TABLE IF NOT EXISTS role_permission (
    role VARCHAR(50),
    permission_id INTEGER,
    PRIMARY KEY (role, permission_id),
    FOREIGN KEY (permission_id) REFERENCES permission(id)
);
"""

try:
    # الاتصال بقاعدة البيانات
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    # تنفيذ الاستعلام
    try:
        cursor.execute(query)
        conn.commit()
        print("تم تنفيذ الاستعلام بنجاح")
    except Exception as e:
        conn.rollback()
        print(f"حدث خطأ في الاستعلام: {e}")
    
    # إغلاق الاتصال
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"حدث خطأ في الاتصال بقاعدة البيانات: {e}")