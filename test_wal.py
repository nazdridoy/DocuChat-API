import sqlite3
import time
import os

print("Current directory:", os.getcwd())
print("Database file exists:", os.path.exists("data.db"))

# Connect to the database
conn = sqlite3.connect("data.db")
conn.execute("PRAGMA journal_mode = WAL")

# Create a test table if it doesn't exist
conn.execute("""
CREATE TABLE IF NOT EXISTS test_wal (
    id INTEGER PRIMARY KEY,
    value TEXT
)
""")

# Insert some data
conn.execute("INSERT INTO test_wal (value) VALUES (?)", ("test_value",))

# Commit but keep the connection open
conn.commit()

print("Inserted data and committed")
print("Check for WAL files now...")
print("Press Ctrl+C to exit and close the connection")

# Keep the connection open
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nClosing connection")
    conn.close()
    print("Connection closed") 