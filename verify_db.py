import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'new_app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Verificar la estructura de la tabla check_item
print("Estructura de la tabla check_item:")
cursor.execute("PRAGMA table_info(check_item);")
columns = cursor.fetchall()
for column in columns:
    print(f"- {column[1]} ({column[2]})")

# Verificar los datos en la tabla check_item
print("\nDatos en la tabla check_item:")
cursor.execute("SELECT * FROM check_item LIMIT 5;")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
