import sqlite3
import json


class Cache:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self._create()

    def _create(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)

    def make_key(self, lat, lon):
        return f"{round(lat, 4)}_{round(lon, 4)}"

    def get(self, lat, lon):
        key = self.make_key(lat, lon)
        cur = self.conn.execute("SELECT value FROM cache WHERE key=?", (key,))
        row = cur.fetchone()
        return json.loads(row[0]) if row else None

    def set(self, lat, lon, value):
        key = self.make_key(lat, lon)
        self.conn.execute(
            "INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)",
            (key, json.dumps(value))
        )
        self.conn.commit()
