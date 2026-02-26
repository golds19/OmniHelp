"""
SQLite persistence layer for Lifeforge.

Provides two tables:
  - documents   : registry of ingested PDFs
  - query_logs  : every query with its evaluation metrics
"""
import json
import sqlite3
import time
import logging
from pathlib import Path
from typing import Optional

from .config import AppConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    db_path = Path(AppConfig.DATA_DIR) / "lifeforge.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    index_type   TEXT    NOT NULL,
    filename     TEXT    NOT NULL,
    uploaded_at  TEXT    NOT NULL,
    num_chunks   INTEGER,
    num_images   INTEGER
);

CREATE TABLE IF NOT EXISTS query_logs (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id              INTEGER REFERENCES documents(id),
    timestamp                TEXT    NOT NULL,
    query                    TEXT    NOT NULL,
    answer_length            INTEGER,
    num_text_chunks          INTEGER,
    num_images               INTEGER,
    top_similarity           REAL,
    confidence               REAL,
    answer_source_similarity REAL,
    is_hallucination         INTEGER,
    rejected                 INTEGER DEFAULT 0,
    source_pages             TEXT,
    latency_ms               REAL
);
"""


def init_db():
    """Create tables if they don't exist. Safe to call multiple times."""
    with _connect() as conn:
        conn.executescript(_SCHEMA)
    logger.info("SQLite database initialised.")


# ---------------------------------------------------------------------------
# Document registry
# ---------------------------------------------------------------------------

def save_document(
    index_type: str,
    filename: str,
    num_chunks: int,
    num_images: int,
) -> int:
    """Insert a document record and return its new row id."""
    uploaded_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO documents (index_type, filename, uploaded_at, num_chunks, num_images)
            VALUES (?, ?, ?, ?, ?)
            """,
            (index_type, filename, uploaded_at, num_chunks, num_images),
        )
        return cur.lastrowid


def get_all_documents() -> list:
    """Return all document records ordered by most recent first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_latest_document(index_type: str) -> Optional[dict]:
    """Return the most recently ingested document for this index_type."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE index_type = ? ORDER BY id DESC LIMIT 1",
            (index_type,),
        ).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Query logs
# ---------------------------------------------------------------------------

def save_query_log(document_id: Optional[int], entry: dict):
    """
    Persist a query log entry produced by _log_query().

    Expected keys in entry (all optional — defaults to None/0):
        timestamp, query, answer_length, num_text_chunks, num_images,
        top_similarity, confidence, answer_source_similarity,
        is_hallucination, rejected, source_pages (list), latency_ms
    """
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO query_logs (
                document_id, timestamp, query,
                answer_length, num_text_chunks, num_images,
                top_similarity, confidence, answer_source_similarity,
                is_hallucination, rejected, source_pages, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                entry.get("timestamp"),
                entry.get("query"),
                entry.get("answer_length"),
                entry.get("num_text_chunks"),
                entry.get("num_images"),
                entry.get("top_similarity"),
                entry.get("confidence"),
                entry.get("answer_source_similarity"),
                int(entry.get("is_hallucination", False)),
                int(entry.get("rejected", False)),
                json.dumps(entry.get("source_pages", [])),
                entry.get("latency_ms"),
            ),
        )


def get_recent_logs(limit: int = 50) -> list:
    """Return the most recent query log rows."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM query_logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    result = []
    for r in rows:
        row_dict = dict(r)
        if row_dict.get("source_pages"):
            row_dict["source_pages"] = json.loads(row_dict["source_pages"])
        result.append(row_dict)
    return result


# ---------------------------------------------------------------------------
# Evaluation summary
# ---------------------------------------------------------------------------

def get_eval_summary() -> dict:
    """
    Compute aggregate evaluation metrics across all stored query logs.

    Returns a dict with:
        total_queries, hallucination_rate, rejection_rate,
        avg_confidence, avg_top_similarity, avg_answer_source_similarity,
        avg_latency_ms
    """
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                              AS total_queries,
                AVG(is_hallucination)                 AS hallucination_rate,
                AVG(rejected)                         AS rejection_rate,
                AVG(confidence)                       AS avg_confidence,
                AVG(top_similarity)                   AS avg_top_similarity,
                AVG(answer_source_similarity)         AS avg_answer_source_similarity,
                AVG(latency_ms)                       AS avg_latency_ms
            FROM query_logs
            """
        ).fetchone()

    def _r(v):
        return round(v, 4) if v is not None else 0.0

    return {
        "total_queries": row["total_queries"] or 0,
        "hallucination_rate": _r(row["hallucination_rate"]),
        "rejection_rate": _r(row["rejection_rate"]),
        "avg_confidence": _r(row["avg_confidence"]),
        "avg_top_similarity": _r(row["avg_top_similarity"]),
        "avg_answer_source_similarity": _r(row["avg_answer_source_similarity"]),
        "avg_latency_ms": _r(row["avg_latency_ms"]),
    }
