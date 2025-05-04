import sqlite3
import os
import shutil
from datetime import datetime

# إنشاء مجلد للنسخ الاحتياطي
backup_folder = 'database_backup'
if not os.path.exists(backup_folder):
    os.makedirs(backup_folder)

# اسم ملف النسخة الاحتياطية مع التاريخ والوقت
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = os.path.join(backup_folder, f"app_db_backup_{current_time}.db")

# نسخ ملف قاعدة البيانات
original_db = 'app.db'  # تأكد من أن هذا هو اسم ملف قاعدة البيانات الخاص بك
shutil.copy2(original_db, backup_file)

print(f"تم إنشاء نسخة احتياطية في: {backup_file}")