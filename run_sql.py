import os
import sqlite3

# Database path
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')

print(f"Database path: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# SQL to create shumoos table
sql = '''
CREATE TABLE IF NOT EXISTS shumoos (
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
'''

# Execute SQL
cursor.execute(sql)
conn.commit()

print("Shumoos table created successfully!")

# Close connection
conn.close()
