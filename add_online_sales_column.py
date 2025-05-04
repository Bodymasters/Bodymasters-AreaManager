import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Verificar si la columna ya existe
cursor.execute("PRAGMA table_info(sales_target)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

if 'online_sales' not in column_names:
    # Agregar la columna online_sales con valor predeterminado 0
    cursor.execute("ALTER TABLE sales_target ADD COLUMN online_sales FLOAT DEFAULT 0")
    print("Se agregó la columna 'online_sales' a la tabla 'sales_target'")
else:
    print("La columna 'online_sales' ya existe en la tabla 'sales_target'")

# Guardar los cambios y cerrar la conexión
conn.commit()
conn.close()

print("Migración completada con éxito")
