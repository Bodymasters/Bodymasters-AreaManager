import sqlite3
import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'new_app.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear una tabla temporal con la nueva estructura
cursor.execute('''
CREATE TABLE check_item_new (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL,
    facility_item_id INTEGER NOT NULL,
    is_compliant BOOLEAN DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (check_id) REFERENCES "check"(id),
    FOREIGN KEY (facility_item_id) REFERENCES facility_item(id)
);
''')

# Copiar los datos de la tabla antigua a la nueva
# Asumimos que facility_id + item_id se corresponden con facility_item_id
cursor.execute('''
INSERT INTO check_item_new (id, check_id, facility_item_id, is_compliant, notes)
SELECT ci.id, ci.check_id, fi.id, ci.is_compliant, ci.notes
FROM check_item ci
JOIN facility_item fi ON ci.facility_id = fi.facility_id AND ci.item_id = fi.id
''')

# Eliminar la tabla antigua
cursor.execute('DROP TABLE check_item;')

# Renombrar la tabla nueva
cursor.execute('ALTER TABLE check_item_new RENAME TO check_item;')

# Confirmar los cambios
conn.commit()

# Verificar la nueva estructura
print("Nueva estructura de la tabla check_item:")
cursor.execute("PRAGMA table_info(check_item);")
columns = cursor.fetchall()
for column in columns:
    print(f"- {column[1]} ({column[2]})")

conn.close()

print("\n¡Base de datos actualizada con éxito!")
