import sqlite3
import json
from datetime import datetime
import os

class HistoryManager:
    def __init__(self, db_path="cleanup_history.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                files_removed TEXT,
                space_recovered INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def log_cleanup(self, files_removed, space_recovered):
        """
        Logs a cleanup action.
        files_removed: list of file paths
        space_recovered: integer bytes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        files_json = json.dumps(files_removed)
        
        cursor.execute('INSERT INTO history (timestamp, files_removed, space_recovered) VALUES (?, ?, ?)',
                       (timestamp, files_json, space_recovered))
        conn.commit()
        conn.close()

    def get_history(self):
        """
        Returns a list of cleanup records.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp, files_removed, space_recovered FROM history ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'timestamp': row[0],
                'files_removed': json.loads(row[1]),
                'space_recovered': row[2]
            })
        return history
