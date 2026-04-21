import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from whybroke.config import CONFIG_DIR

DEFAULT_DB_PATH = CONFIG_DIR / "history.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_input TEXT,
    ast_context TEXT,
    exception_type TEXT,
    confidence_score INTEGER,
    llm_response_json TEXT,
    comments TEXT DEFAULT ''
);
"""


@dataclass(frozen=True)
class Session:
    id: int
    timestamp: str
    raw_input: str
    ast_context: str
    exception_type: str | None
    confidence_score: int | None
    llm_response: dict
    comments: str = ""


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        if "comments" not in cols:
            conn.execute("ALTER TABLE sessions ADD COLUMN comments TEXT DEFAULT ''")
            conn.commit()


def save_session(
    raw_input: str,
    ast_context: str,
    llm_response: dict,
    comments: str = "",
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO sessions "
            "(raw_input, ast_context, exception_type, confidence_score, llm_response_json, comments) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                raw_input,
                ast_context,
                llm_response.get("exception_type"),
                llm_response.get("confidence_score"),
                json.dumps(llm_response),
                comments,
            ),
        )
        conn.commit()
        return int(cur.lastrowid or 0)


def clear_history(db_path: Path = DEFAULT_DB_PATH) -> int:
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM sessions")
        count = int(cur.fetchone()[0])
        conn.execute("DELETE FROM sessions")
        try:
            conn.execute("DELETE FROM sqlite_sequence WHERE name='sessions'")
        except sqlite3.OperationalError:
            pass
        conn.commit()
    return count


def update_comment(
    session_id: int, comment: str, db_path: Path = DEFAULT_DB_PATH
) -> bool:
    init_db(db_path)
    with _connect(db_path) as conn:
        cur = conn.execute(
            "UPDATE sessions SET comments = ? WHERE id = ?",
            (comment, session_id),
        )
        conn.commit()
        return cur.rowcount > 0


def get_session(session_id: int, db_path: Path = DEFAULT_DB_PATH) -> Session | None:
    init_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
    return _row_to_session(row) if row else None


def list_recent(
    limit: int = 10, db_path: Path = DEFAULT_DB_PATH
) -> list[Session]:
    init_db(db_path)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_session(r) for r in rows]


def _row_to_session(row: sqlite3.Row) -> Session:
    raw_json = row["llm_response_json"] or "{}"
    try:
        response = json.loads(raw_json)
    except json.JSONDecodeError:
        response = {}
    try:
        comments = row["comments"] or ""
    except (IndexError, KeyError):
        comments = ""
    return Session(
        id=row["id"],
        timestamp=row["timestamp"],
        raw_input=row["raw_input"] or "",
        ast_context=row["ast_context"] or "",
        exception_type=row["exception_type"],
        confidence_score=row["confidence_score"],
        llm_response=response,
        comments=comments,
    )
