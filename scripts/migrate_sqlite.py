import sqlite3
import os

for db_file in ["brandsentinel.db", "test_brandsentinel.db"]:
    if os.path.exists(db_file):
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()
            c.execute("ALTER TABLE findings ADD COLUMN source VARCHAR DEFAULT 'rule'")
            conn.commit()
            conn.close()
            print(f"Added source column to {db_file}")
        except Exception as e:
            print(f"{db_file}: {e}")
