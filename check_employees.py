import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# الحصول على جميع النوادي
cursor.execute("SELECT id, name FROM club")
clubs = cursor.fetchall()

print("=== الموظفين في كل نادي ===")
for club in clubs:
    club_id, club_name = club
    
    # الحصول على الموظفين في النادي
    cursor.execute("SELECT id, name, employee_id, position, role FROM employee WHERE club_id = ?", (club_id,))
    employees = cursor.fetchall()
    
    print(f"النادي: {club_name} (ID: {club_id})")
    print(f"عدد الموظفين: {len(employees)}")
    
    for employee in employees:
        emp_id, name, employee_id, position, role = employee
        print(f"  - {name} (ID: {emp_id}, الرقم الوظيفي: {employee_id}, الوظيفة: {position}, الدور: {role})")
    
    print("---")

conn.close()
