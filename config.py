import os
from dotenv import load_dotenv

load_dotenv()

# Apify
APIFY_API_TOKEN = os.environ["APIFY_API_TOKEN"]

# Actor IDs
TIKTOK_ACTOR_ID = "clockworks/tiktok-scraper"
INSTAGRAM_ACTOR_ID = "apify/instagram-hashtag-scraper"
YOUTUBE_ACTOR_ID = "streamers/youtube-scraper"

# Posts to fetch per platform per run (controls Apify cost)
MAX_POSTS_PER_PLATFORM = 200

# Arabic + pan-MENA hashtags to scrape
TIKTOK_HASHTAGS = [
    "ترند", "فيروسي", "مشهور", "تيك_توك", "viral", "trending",
    "السعودية", "مصر", "الإمارات", "العراق", "المغرب",
]
INSTAGRAM_HASHTAGS = [
    "ترند", "فيروسي", "ريلز", "انستقرام", "viral", "trending",
    "السعودية", "مصر", "الإمارات",
]
YOUTUBE_SEARCH_QUERIES = [
    "ترند عربي", "فيديو فيروسي", "أكثر مشاهدة", "عربي 2026",
    "arabic trending", "viral arabic",
]

# Google Sheets
GOOGLE_CREDENTIALS_PATH = os.environ["GOOGLE_CREDENTIALS_PATH"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SHEETS_TOP_N = 20  # posts pushed to Google Sheets per daily run

# Database
DB_PATH = os.getenv("DB_PATH", "data/tracker.db")
