import os
import sqlite3

# Database path
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

print(f"Database path: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [table[0] for table in cursor.fetchall()]
print(f"Tables in database: {tables}")

# Check if shumoos table exists
if 'shumoos' in tables:
    print("Shumoos table exists!")

    # Get table structure
    cursor.execute("PRAGMA table_info(shumoos);")
    columns = cursor.fetchall()
    print("Shumoos table structure:")
    for column in columns:
        print(f"  {column}")
else:
    print("Shumoos table does not exist!")

# Close connection
conn.close()
