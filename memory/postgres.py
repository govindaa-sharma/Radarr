import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    postgres_url = os.getenv("POSTGRES_URL")
    if not postgres_url:
        raise RuntimeError("POSTGRES_URL must be set.")
    return psycopg2.connect(postgres_url)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id SERIAL PRIMARY KEY,
            competitor TEXT NOT NULL,
            url TEXT NOT NULL,
            page_type TEXT NOT NULL,
            raw_text TEXT,
            scraped_at TIMESTAMP DEFAULT NOW()
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            competitor TEXT NOT NULL,
            url TEXT NOT NULL,
            page_type TEXT NOT NULL,
            event_type TEXT,
            importance INTEGER,
            summary TEXT,
            raw_diff TEXT,
            analysed_at TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database tables created successfully.")

def save_snapshot(competitor, url, page_type, raw_text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO snapshots (competitor, url, page_type, raw_text)
        VALUES (%s, %s, %s, %s)
    """, (competitor, url, page_type, raw_text))

    conn.commit()
    cursor.close()
    conn.close()

def get_last_snapshot(competitor, url):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT raw_text, scraped_at
        FROM snapshots
        WHERE competitor = %s AND url = %s
        ORDER BY scraped_at DESC, id DESC
        LIMIT 1
    """, (competitor, url))

    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def save_analysis(competitor, url, page_type, event_type, importance, summary, raw_diff):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO analyses (competitor, url, page_type, event_type, importance, summary, raw_diff)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (competitor, url, page_type, event_type, importance, summary, raw_diff))

    conn.commit()
    cursor.close()
    conn.close()

def get_recent_analyses(days=1):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT competitor, page_type, event_type, importance, summary, analysed_at
        FROM analyses
        WHERE analysed_at >= NOW() - (%s * INTERVAL '1 day')
        ORDER BY importance DESC, analysed_at DESC
    """, (days,))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
