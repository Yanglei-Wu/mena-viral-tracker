import gspread
from google.oauth2.service_account import Credentials
from datetime import date
from pipeline.processor import Post
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Platform", "Author", "Views", "Likes", "Comments", "Shares",
    "Engagement Rate", "Virality Score", "Content Type", "Posted At", "URL",
]


def _get_worksheet(sheet_name: str = "Daily Digest") -> gspread.Worksheet:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID)
    try:
        return sheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return sheet.add_worksheet(title=sheet_name, rows=10000, cols=20)


def push_daily_digest(posts: list[Post], run_date: date) -> int:
    """Append top posts for the day to the Daily Digest tab. Returns row count pushed."""
    ws = _get_worksheet("Daily Digest")

    # Date separator row
    ws.append_row([f"=== {run_date.isoformat()} ==="] + [""] * (len(HEADERS) - 1))
    # Column headers
    ws.append_row(HEADERS)

    for post in posts:
        ws.append_row(_post_to_row(post))

    return len(posts)


def _post_to_row(post: Post) -> list:
    engagement_rate = (
        round((post.likes + post.comments + post.shares) / post.views * 100, 2)
        if post.views > 0 else 0.0
    )
    posted_str = post.posted_at.strftime("%Y-%m-%d %H:%M") if post.posted_at else ""
    return [
        post.platform,
        post.author,
        post.views,
        post.likes,
        post.comments,
        post.shares,
        f"{engagement_rate}%",
        round(post.virality_score, 2),
        post.content_type,
        posted_str,
        post.url,
    ]
