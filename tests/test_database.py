import sqlite3
from datetime import date, datetime, timezone
import pytest
from db.database import Database
from pipeline.processor import Post


def make_post(**kwargs) -> Post:
    defaults = dict(
        platform="tiktok",
        post_id="abc123",
        url="https://tiktok.com/@user/video/abc123",
        author="testuser",
        followers=10000,
        views=50000,
        likes=3000,
        comments=500,
        shares=200,
        caption="Test post #ترند",
        hashtags=["ترند", "viral"],
        content_type="video",
        posted_at=datetime(2026, 4, 16, 6, 0, tzinfo=timezone.utc),
        scraped_at=datetime(2026, 4, 16, 7, 0, tzinfo=timezone.utc),
        virality_score=1.4,
    )
    defaults.update(kwargs)
    return Post(**defaults)


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    database = Database(db_path)
    database.init()
    return database


def test_init_creates_tables(db):
    conn = sqlite3.connect(db.db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert {"posts", "runs", "sheets_log"} == tables


def test_insert_and_retrieve_posts(db):
    post = make_post()
    db.insert_posts([post])
    results = db.get_posts(date(2026, 4, 16), date(2026, 4, 16))
    assert len(results) == 1
    assert results[0].post_id == "abc123"
    assert results[0].platform == "tiktok"
    assert results[0].author == "testuser"
    assert results[0].virality_score == pytest.approx(1.4)


def test_insert_duplicate_ignored(db):
    post = make_post()
    db.insert_posts([post])
    db.insert_posts([post])  # same post_id + platform + date — should be ignored
    results = db.get_posts(date(2026, 4, 16), date(2026, 4, 16))
    assert len(results) == 1


def test_filter_by_platform(db):
    tiktok_post = make_post(platform="tiktok", post_id="t1")
    tt_post2 = make_post(platform="tiktok", post_id="t2")
    db.insert_posts([tiktok_post, tt_post2])
    results = db.get_posts(date(2026, 4, 16), date(2026, 4, 16), platform="tiktok")
    assert len(results) == 2
    assert all(r.platform == "tiktok" for r in results)


def test_get_top_posts_ordered_by_virality(db):
    low = make_post(post_id="low", virality_score=0.5)
    high = make_post(post_id="high", virality_score=1.9)
    mid = make_post(post_id="mid", virality_score=1.1)
    db.insert_posts([low, high, mid])
    top = db.get_top_posts(date(2026, 4, 16), limit=3)
    assert [p.post_id for p in top] == ["high", "mid", "low"]


def test_log_run(db):
    db.log_run(date(2026, 4, 16), "tiktok", 150, "success")
    conn = sqlite3.connect(db.db_path)
    row = conn.execute("SELECT * FROM runs").fetchone()
    conn.close()
    assert row[2] == "tiktok"
    assert row[3] == 150
    assert row[4] == "success"


def test_log_sheets_push(db):
    db.log_sheets_push(date(2026, 4, 16), 20)
    conn = sqlite3.connect(db.db_path)
    row = conn.execute("SELECT * FROM sheets_log").fetchone()
    conn.close()
    assert row[2] == 20
