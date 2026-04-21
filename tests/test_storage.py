import sqlite3

from whybroke.storage import (
    clear_history,
    get_session,
    init_db,
    list_recent,
    save_session,
    update_comment,
)

SAMPLE = {
    "exception_type": "TypeError",
    "confidence_score": 92,
    "root_cause": "await on sync function",
    "reasoning": "trace shows await on sync call",
    "evidence_lines": ["user_data = await db.get_user_sync(user_id)"],
    "suggested_fix": "- await x()\n+ x()",
}


def test_save_and_get_roundtrip(tmp_path):
    db = tmp_path / "test.db"
    sid = save_session("raw trace", "def foo(): pass", SAMPLE, db_path=db)
    assert sid >= 1
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.id == sid
    assert session.exception_type == "TypeError"
    assert session.confidence_score == 92
    assert session.llm_response["suggested_fix"].startswith("- await")
    assert session.raw_input == "raw trace"
    assert session.ast_context == "def foo(): pass"


def test_get_session_returns_none_for_missing(tmp_path):
    db = tmp_path / "test.db"
    assert get_session(999, db_path=db) is None


def test_list_recent_orders_by_newest_first(tmp_path):
    db = tmp_path / "test.db"
    ids = []
    for i in range(3):
        ids.append(save_session(f"raw-{i}", "", {**SAMPLE, "confidence_score": i}, db_path=db))

    sessions = list_recent(db_path=db)
    assert [s.id for s in sessions] == list(reversed(ids))


def test_list_recent_respects_limit(tmp_path):
    db = tmp_path / "test.db"
    for i in range(5):
        save_session(f"raw-{i}", "", SAMPLE, db_path=db)
    sessions = list_recent(limit=2, db_path=db)
    assert len(sessions) == 2


def test_list_recent_empty_db(tmp_path):
    db = tmp_path / "test.db"
    assert list_recent(db_path=db) == []


def test_save_with_comment_roundtrips(tmp_path):
    db = tmp_path / "test.db"
    sid = save_session("raw", "", SAMPLE, comments="flaky in CI", db_path=db)
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.comments == "flaky in CI"


def test_save_defaults_comment_empty(tmp_path):
    db = tmp_path / "test.db"
    sid = save_session("raw", "", SAMPLE, db_path=db)
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.comments == ""


def test_update_comment_updates_and_returns_true(tmp_path):
    db = tmp_path / "test.db"
    sid = save_session("raw", "", SAMPLE, db_path=db)
    assert update_comment(sid, "fixed by pinning numpy", db_path=db) is True
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.comments == "fixed by pinning numpy"


def test_update_comment_clear(tmp_path):
    db = tmp_path / "test.db"
    sid = save_session("raw", "", SAMPLE, comments="initial", db_path=db)
    assert update_comment(sid, "", db_path=db) is True
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.comments == ""


def test_update_comment_missing_id_returns_false(tmp_path):
    db = tmp_path / "test.db"
    init_db(db)
    assert update_comment(999, "nope", db_path=db) is False


def test_init_db_migrates_legacy_schema(tmp_path):
    db = tmp_path / "legacy.db"
    legacy_schema = """
    CREATE TABLE sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_input TEXT,
        ast_context TEXT,
        exception_type TEXT,
        confidence_score INTEGER,
        llm_response_json TEXT
    );
    """
    with sqlite3.connect(db) as conn:
        conn.executescript(legacy_schema)
        conn.execute(
            "INSERT INTO sessions (raw_input, ast_context, exception_type, confidence_score, llm_response_json) "
            "VALUES (?, ?, ?, ?, ?)",
            ("old", "", "TypeError", 50, "{}"),
        )
        conn.commit()

    init_db(db)

    with sqlite3.connect(db) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()}
    assert "comments" in cols

    session = get_session(1, db_path=db)
    assert session is not None
    assert session.comments == ""

    assert update_comment(1, "backfilled", db_path=db) is True
    session = get_session(1, db_path=db)
    assert session is not None
    assert session.comments == "backfilled"


def test_clear_history_removes_all_and_returns_count(tmp_path):
    db = tmp_path / "test.db"
    for i in range(3):
        save_session(f"raw-{i}", "", SAMPLE, db_path=db)
    deleted = clear_history(db_path=db)
    assert deleted == 3
    assert list_recent(db_path=db) == []


def test_clear_history_on_empty_db_returns_zero(tmp_path):
    db = tmp_path / "test.db"
    assert clear_history(db_path=db) == 0


def test_clear_history_resets_autoincrement(tmp_path):
    db = tmp_path / "test.db"
    save_session("raw", "", SAMPLE, db_path=db)
    clear_history(db_path=db)
    new_id = save_session("raw2", "", SAMPLE, db_path=db)
    assert new_id == 1


def test_save_handles_missing_optional_fields(tmp_path):
    db = tmp_path / "test.db"
    sparse = {"exception_type": None, "confidence_score": None}
    sid = save_session("raw", "", sparse, db_path=db)
    session = get_session(sid, db_path=db)
    assert session is not None
    assert session.exception_type is None
    assert session.confidence_score is None
