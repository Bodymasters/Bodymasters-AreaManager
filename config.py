import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

# إعدادات قاعدة البيانات
DB_TYPE = os.environ.get('DB_TYPE', 'sqlite')  # 'sqlite' أو 'postgresql'

# إعدادات SQLite
SQLITE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

# إعدادات PostgreSQL (Supabase)
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'your-supabase-host.supabase.co')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'postgres')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'your-password')
POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')

# تكوين رابط قاعدة البيانات بناءً على النوع
def get_database_uri():
    if DB_TYPE == 'sqlite':
        return f'sqlite:///{SQLITE_DB_PATH}'
    elif DB_TYPE == 'postgresql':
        return f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    else:
        raise ValueError(f"نوع قاعدة البيانات غير مدعوم: {DB_TYPE}")

# إعدادات أخرى للتطبيق
SECRET_KEY = os.environ.get('SECRET_KEY', 'secret-key-12345')
SQLALCHEMY_TRACK_MODIFICATIONS = False
