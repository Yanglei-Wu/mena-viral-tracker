from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from pipeline.processor import Post
from pipeline.sheets import push_daily_digest, _post_to_row, HEADERS


def make_post(post_id="p1", platform="tiktok", virality_score=1.5) -> Post:
    return Post(
        platform=platform,
        post_id=post_id,
        url=f"https://example.com/{post_id}",
        author="testuser",
        followers=100000,
        views=500000,
        likes=20000,
        comments=3000,
        shares=1000,
        caption="test",
        hashtags=["ترند"],
        content_type="video",
        posted_at=datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        scraped_at=datetime(2026, 4, 16, 7, 0, tzinfo=timezone.utc),
        virality_score=virality_score,
    )


def test_post_to_row_has_correct_columns():
    post = make_post()
    row = _post_to_row(post)
    assert len(row) == len(HEADERS)


def test_post_to_row_url_in_row():
    post = make_post(post_id="abc")
    row = _post_to_row(post)
    assert "https://example.com/abc" in row


def test_post_to_row_virality_score_formatted():
    post = make_post(virality_score=1.7654)
    row = _post_to_row(post)
    assert "1.77" in str(row)


@patch("pipeline.sheets.gspread")
@patch("pipeline.sheets.Credentials")
def test_push_daily_digest_returns_row_count(mock_creds, mock_gspread):
    mock_ws = MagicMock()
    mock_gspread.authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_ws

    posts = [make_post(f"p{i}") for i in range(5)]
    count = push_daily_digest(posts, date(2026, 4, 16))
    assert count == 5


@patch("pipeline.sheets.gspread")
@patch("pipeline.sheets.Credentials")
def test_push_daily_digest_appends_header_row(mock_creds, mock_gspread):
    mock_ws = MagicMock()
    mock_gspread.authorize.return_value.open_by_key.return_value.worksheet.return_value = mock_ws

    posts = [make_post("p1")]
    push_daily_digest(posts, date(2026, 4, 16))

    appended_calls = mock_ws.append_row.call_args_list
    # First call should be the date header row
    assert "2026-04-16" in str(appended_calls[0])
