import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from pipeline.processor import Post


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        schema = schema_path.read_text()
        with self._connect() as conn:
            conn.executescript(schema)

    def insert_posts(self, posts: list[Post]) -> None:
        rows = [
            (
                p.platform,
                p.post_id,
                p.url,
                p.author,
                p.followers,
                p.views,
                p.likes,
                p.comments,
                p.shares,
                p.caption,
                json.dumps(p.hashtags, ensure_ascii=False),
                p.content_type,
                p.posted_at.isoformat() if p.posted_at else None,
                p.scraped_at.isoformat() if p.scraped_at else None,
                p.scraped_at.date().isoformat() if p.scraped_at else None,
                p.virality_score,
            )
            for p in posts
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO posts
                  (platform, post_id, url, author, followers, views, likes,
                   comments, shares, caption, hashtags, content_type,
                   posted_at, scraped_at, scraped_date, virality_score)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                rows,
            )

    def get_posts(
        self,
        start: date,
        end: date,
        platform: Optional[str] = None,
    ) -> list[Post]:
        query = """
            SELECT * FROM posts
            WHERE DATE(scraped_at) BETWEEN ? AND ?
        """
        params: list = [start.isoformat(), end.isoformat()]
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY virality_score DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_post(r) for r in rows]

    def get_top_posts(self, run_date: date, limit: int = 20) -> list[Post]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM posts
                WHERE DATE(scraped_at) = ?
                ORDER BY virality_score DESC
                LIMIT ?
                """,
                (run_date.isoformat(), limit),
            ).fetchall()
        return [_row_to_post(r) for r in rows]

    def log_run(
        self,
        run_date: date,
        platform: str,
        posts_fetched: int,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_date, platform, posts_fetched, status, error) VALUES (?,?,?,?,?)",
                (run_date.isoformat(), platform, posts_fetched, status, error),
            )

    def log_sheets_push(self, run_date: date, rows_pushed: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sheets_log (run_date, rows_pushed, pushed_at) VALUES (?,?,?)",
                (run_date.isoformat(), rows_pushed, now),
            )


def _row_to_post(row: sqlite3.Row) -> Post:
    return Post(
        platform=row["platform"],
        post_id=row["post_id"],
        url=row["url"] or "",
        author=row["author"] or "",
        followers=row["followers"] or 0,
        views=row["views"] or 0,
        likes=row["likes"] or 0,
        comments=row["comments"] or 0,
        shares=row["shares"] or 0,
        caption=row["caption"] or "",
        hashtags=json.loads(row["hashtags"]) if row["hashtags"] else [],
        content_type=row["content_type"] or "",
        posted_at=_parse_dt(row["posted_at"]),
        scraped_at=_parse_dt(row["scraped_at"]),
        virality_score=row["virality_score"] or 0.0,
    )


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)
