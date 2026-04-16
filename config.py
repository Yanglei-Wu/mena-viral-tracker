import os
from dotenv import load_dotenv

load_dotenv()

# Apify
APIFY_API_TOKEN = os.environ["APIFY_API_TOKEN"]

# Actor IDs
TIKTOK_ACTOR_ID = "clockworks/tiktok-scraper"

# TikTok: top N videos per country × 5 MENA countries
TIKTOK_TOP_N_PER_COUNTRY = 10
TIKTOK_MAX_POSTS = TIKTOK_TOP_N_PER_COUNTRY * 5  # 50 total

# MENA proxy countries for TikTok (ISO 3166-1 alpha-2 codes)
# Each country gets an equal share of MAX_POSTS_PER_PLATFORM
TIKTOK_PROXY_COUNTRIES = ["SA", "EG", "AE", "IQ", "MA"]  # Saudi, Egypt, UAE, Iraq, Morocco

# Arabic + pan-MENA hashtags to scrape
TIKTOK_HASHTAGS = [
    "ترند", "فيروسي", "مشهور", "تيك_توك", "viral", "trending",
    "السعودية", "مصر", "الإمارات", "العراق", "المغرب",
]
# Google Sheets
GOOGLE_CREDENTIALS_PATH = os.environ["GOOGLE_CREDENTIALS_PATH"]
GOOGLE_SHEET_ID = os.environ["GOOGLE_SHEET_ID"]
SHEETS_TOP_N = 20  # posts pushed to Google Sheets per daily run

# Database
DB_PATH = os.getenv("DB_PATH", "data/tracker.db")

# Gemini AI Analysis
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # empty string = skip analysis gracefully
GEMINI_MODEL = "gemini-2.5-flash-lite"
