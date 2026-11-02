# Database layer: creates the SQLite tables and handles saving/reading records.
import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # lets us read columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables if they don't exist yet."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            source TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auction_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            head_count INTEGER NOT NULL,
            total_kilos REAL NOT NULL,
            price_per_kilo REAL NOT NULL,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            message TEXT,
            detected_intent TEXT,
            confidence REAL,
            response TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def get_dataset_id(name):
    conn = get_connection()
    row = conn.execute("SELECT id FROM datasets WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row["id"] if row else None


def list_datasets():
    conn = get_connection()
    rows = conn.execute("SELECT id, name, source FROM datasets ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_dataset(dataset_id):
    conn = get_connection()
    conn.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    conn.commit()
    conn.close()


def create_dataset_with_records(name, source, df):
    """Save a dataset and all its records in one go. Returns the new dataset id."""
    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO datasets (name, source) VALUES (?, ?)", (name, source))
        dataset_id = cur.lastrowid
        rows = [
            (dataset_id, r.date, int(r.head_count), float(r.total_kilos), float(r.price_per_kilo))
            for r in df.itertuples(index=False)
        ]
        conn.executemany(
            "INSERT INTO auction_records (dataset_id, date, head_count, total_kilos, price_per_kilo) "
            "VALUES (?, ?, ?, ?, ?)", rows)
        conn.commit()
        return dataset_id
    except Exception:
        conn.rollback()      # nothing is saved if anything fails
        raise
    finally:
        conn.close()


def get_records(dataset_id, start_date=None, end_date=None):
    """Read records of ONE dataset only (tabs never mix). Dates are 'YYYY-MM-DD'."""
    query = "SELECT date, head_count, total_kilos, price_per_kilo FROM auction_records WHERE dataset_id = ?"
    params = [dataset_id]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_date(dataset_id):
    """Date of the newest record in ONE dataset (None if it has no records)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT MAX(date) AS latest FROM auction_records WHERE dataset_id = ?",
        (dataset_id,)).fetchone()
    conn.close()
    return row["latest"]


def save_chat_log(dataset_id, message, intent, confidence, response):
    """Save one question and its answer in the chat_logs table."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_logs (dataset_id, message, detected_intent, confidence, response) "
        "VALUES (?, ?, ?, ?, ?)",
        (dataset_id, message, intent, confidence, response))
    conn.commit()
    conn.close()
