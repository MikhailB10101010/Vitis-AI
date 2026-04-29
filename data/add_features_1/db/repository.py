# repository.py - Загрузка в БД данных
import sqlite3


def insert_points(points, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT OR IGNORE INTO vineyard_features (osm_id, lat, lon)
        VALUES (?, ?, ?)
    """, points)

    conn.commit()
    conn.close()
