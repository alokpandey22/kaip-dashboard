"""
SQLite database layer for KAIP.
Handles review storage, classification storage, and all data access.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional

import pandas as pd

from config.settings import DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Get a database connection with UTF-8 and WAL mode enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA encoding='UTF-8'")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the reviews and classifications tables if they don't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                app_name TEXT,
                rating REAL,
                review_text TEXT,
                review_date TEXT,
                reviewer TEXT,
                country TEXT,
                language TEXT,
                app_version TEXT,
                helpful_count INTEGER DEFAULT 0,
                thumbs_up INTEGER DEFAULT 0,
                source_review_id TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER NOT NULL REFERENCES reviews(id),
                sentiment TEXT,
                category TEXT,
                feature_area TEXT,
                severity TEXT,
                intent TEXT,
                pain_point TEXT,
                competitor_mention TEXT,
                one_line_summary TEXT,
                classified_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_source
            ON reviews(source)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_app_name
            ON reviews(app_name)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_classifications_review_id
            ON classifications(review_id)
        """)
        conn.commit()
    finally:
        conn.close()


def insert_review(review_dict: Dict) -> Optional[int]:
    """
    Insert a review into the database.
    Uses INSERT OR IGNORE to skip duplicates based on source_review_id.
    Returns the row id if inserted, None if skipped.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO reviews
                (source, app_name, rating, review_text, review_date,
                 reviewer, country, language, app_version,
                 helpful_count, thumbs_up, source_review_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_dict.get('source', ''),
            review_dict.get('app_name', ''),
            review_dict.get('rating'),
            review_dict.get('review_text', ''),
            review_dict.get('review_date', ''),
            review_dict.get('reviewer', ''),
            review_dict.get('country', ''),
            review_dict.get('language', ''),
            review_dict.get('app_version', ''),
            review_dict.get('helpful_count', 0),
            review_dict.get('thumbs_up', 0),
            review_dict.get('source_review_id', ''),
        ))
        conn.commit()
        if cursor.rowcount > 0:
            return cursor.lastrowid
        return None
    finally:
        conn.close()


def insert_classification(review_id: int, classification_dict: Dict) -> int:
    """
    Insert a classification for a review.
    Returns the classification row id.
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO classifications
                (review_id, sentiment, category, feature_area, severity,
                 intent, pain_point, competitor_mention, one_line_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            review_id,
            classification_dict.get('sentiment', ''),
            classification_dict.get('category', ''),
            classification_dict.get('feature_area', ''),
            classification_dict.get('severity', ''),
            classification_dict.get('intent', ''),
            classification_dict.get('pain_point', ''),
            classification_dict.get('competitor_mention', ''),
            classification_dict.get('one_line_summary', ''),
        ))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_reviews() -> pd.DataFrame:
    """Return all reviews as a pandas DataFrame."""
    conn = _get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM reviews ORDER BY id", conn)
        return df
    finally:
        conn.close()


def get_all_classified() -> pd.DataFrame:
    """
    Return all reviews joined with their classifications as a DataFrame.
    Only includes reviews that have been classified.
    """
    conn = _get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT
                r.id AS review_id,
                r.source,
                r.app_name,
                r.rating,
                r.review_text,
                r.review_date,
                r.reviewer,
                r.country,
                r.language,
                r.app_version,
                r.helpful_count,
                r.thumbs_up,
                r.source_review_id,
                r.created_at,
                c.sentiment,
                c.category,
                c.feature_area,
                c.severity,
                c.intent,
                c.pain_point,
                c.competitor_mention,
                c.one_line_summary,
                c.classified_at
            FROM reviews r
            INNER JOIN classifications c ON r.id = c.review_id
            ORDER BY r.id
        """, conn)
        return df
    finally:
        conn.close()


def get_unclassified_reviews() -> pd.DataFrame:
    """Return reviews that have not yet been classified."""
    conn = _get_connection()
    try:
        df = pd.read_sql_query("""
            SELECT r.*
            FROM reviews r
            LEFT JOIN classifications c ON r.id = c.review_id
            WHERE c.id IS NULL
            ORDER BY r.id
        """, conn)
        return df
    finally:
        conn.close()


def get_review_count() -> int:
    """Return the total number of reviews in the database."""
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM reviews")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def clear_all() -> None:
    """Delete all data from both tables. Use for re-runs."""
    conn = _get_connection()
    try:
        conn.execute("DELETE FROM classifications")
        conn.execute("DELETE FROM reviews")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('reviews', 'classifications')")
        conn.commit()
    finally:
        conn.close()
