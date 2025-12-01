# db.py
import sqlite3, os
DB_PATH = os.environ.get("ARCH_DB", "arch_threads.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    # --- tables ---
    cur.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS threads(
      id TEXT PRIMARY KEY,
      title TEXT,
      location TEXT,
      year TEXT,
      notes TEXT,
      promoted INTEGER DEFAULT 0,
      created_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS posts(
      id TEXT PRIMARY KEY,
      thread_id TEXT REFERENCES threads(id) ON DELETE CASCADE,
      author TEXT,
      text TEXT,
      created_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS assets(
      id TEXT PRIMARY KEY,
      post_id TEXT REFERENCES posts(id) ON DELETE CASCADE,
      url TEXT,
      sha256 TEXT,
      exif_json TEXT
    );

    /* fast lookups for continuity chains by SHA */
    CREATE INDEX IF NOT EXISTS idx_assets_sha ON assets(sha256);
    CREATE INDEX IF NOT EXISTS idx_posts_thread ON posts(thread_id);
    """)
    conn.commit(); conn.close()
