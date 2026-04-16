CREATE TABLE IF NOT EXISTS posts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    platform       TEXT    NOT NULL,
    post_id        TEXT    NOT NULL,
    url            TEXT,
    author         TEXT,
    followers      INTEGER,
    views          INTEGER,
    likes          INTEGER,
    comments       INTEGER,
    shares         INTEGER,
    caption        TEXT,
    hashtags       TEXT,
    content_type   TEXT,
    posted_at      TEXT,
    scraped_at     TEXT,
    scraped_date   TEXT,
    virality_score REAL,
    UNIQUE(platform, post_id, scraped_date)
);

CREATE TABLE IF NOT EXISTS runs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date      TEXT    NOT NULL,
    platform      TEXT    NOT NULL,
    posts_fetched INTEGER,
    status        TEXT,
    error         TEXT
);

CREATE TABLE IF NOT EXISTS sheets_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date    TEXT    NOT NULL,
    rows_pushed INTEGER,
    pushed_at   TEXT    NOT NULL
);
