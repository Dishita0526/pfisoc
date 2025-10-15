# db.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "clauses.db")

def create_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clauses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clause_text TEXT NOT NULL,
            date_added TEXT
        )
    ''')
    conn.commit()
    conn.close()

def clause_exists(clause_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT 1 FROM clauses WHERE clause_text = ?", (clause_text,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def insert_clause(clause_text):
    if clause_exists(clause_text):
        return  # Skip duplicate

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO clauses (clause_text, date_added) VALUES (?, ?)",
        (clause_text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

def fetch_all_clauses():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, clause_text, date_added FROM clauses ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    return [{"id": row[0], "clause_text": row[1], "date_added": row[2]} for row in rows]

# Auto-create DB on import
create_table()
