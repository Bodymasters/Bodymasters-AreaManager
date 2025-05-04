import os
import sqlite3

# Database path
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

print(f"Database path: {db_path}")

# Check if shumoos table exists
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [table[0] for table in cursor.fetchall()]
print(f"Tables in database: {tables}")

# Check if shumoos table exists
if 'shumoos' not in tables:
    print("Shumoos table not found. Creating it...")

    # Create shumoos table manually
    cursor.execute('''
    CREATE TABLE shumoos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        club_id INTEGER NOT NULL,
        registered_count INTEGER NOT NULL,
        registration_date DATE NOT NULL,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (club_id) REFERENCES club (id),
        FOREIGN KEY (created_by) REFERENCES user (id)
    );
    ''')
    conn.commit()
    print("Shumoos table created successfully!")
else:
    print("Shumoos table already exists.")

# Close connection
conn.close()

print("Done!")
