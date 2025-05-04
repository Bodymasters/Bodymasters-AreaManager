import psycopg2

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
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    
    # إزالة قيد الفرادة على عمود location
    query = """
    ALTER TABLE club DROP CONSTRAINT IF EXISTS club_location_key;
    """
    
    # تنفيذ الاستعلام
    cursor.execute(query)
    conn.commit()
    print("تم إزالة قيد الفرادة على عمود location بنجاح")
    
    # إغلاق الاتصال
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"حدث خطأ: {e}")