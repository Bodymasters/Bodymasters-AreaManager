import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# التحقق من جدول المستخدمين
print("=== جدول المستخدمين ===")
cursor.execute("SELECT id, username, name, is_admin FROM user")
users = cursor.fetchall()
for user in users:
    user_id, username, name, is_admin = user
    print(f"المستخدم: {name} (ID: {user_id}, اسم المستخدم: {username}, مسؤول: {is_admin})")
    
    # الحصول على النوادي المرتبطة بالمستخدم
    cursor.execute("SELECT c.id, c.name FROM club c JOIN user_clubs uc ON c.id = uc.club_id WHERE uc.user_id = ?", (user_id,))
    clubs = cursor.fetchall()
    print(f"النوادي المرتبطة: {len(clubs)}")
    for club in clubs:
        club_id, club_name = club
        print(f"  - {club_name} (ID: {club_id})")
    print("---")

# التحقق من جدول النوادي
print("\n=== جدول النوادي ===")
cursor.execute("SELECT id, name FROM club")
clubs = cursor.fetchall()
for club in clubs:
    club_id, club_name = club
    print(f"النادي: {club_name} (ID: {club_id})")
    
    # الحصول على المستخدمين المرتبطين بالنادي
    cursor.execute("SELECT u.id, u.username, u.name, u.is_admin FROM user u JOIN user_clubs uc ON u.id = uc.user_id WHERE uc.club_id = ?", (club_id,))
    users = cursor.fetchall()
    print(f"المستخدمين المرتبطين: {len(users)}")
    for user in users:
        user_id, username, name, is_admin = user
        print(f"  - {name} (ID: {user_id}, اسم المستخدم: {username}, مسؤول: {is_admin})")
    print("---")

conn.close()
