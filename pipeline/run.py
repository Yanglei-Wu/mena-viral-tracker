"""
Entry point for the daily MENA viral content pipeline.
Run manually or via cron: python pipeline/run.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import date, datetime, timezone

import config
from db.database import Database
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import compute_virality_scores
from pipeline.scrapers.instagram import InstagramScraper
from pipeline.scrapers.tiktok import TikTokScraper
from pipeline.scrapers.youtube import YouTubeScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def run_pipeline() -> None:
    today = date.today()
    db = Database(config.DB_PATH)
    db.init()
    apify = ApifyWrapper(config.APIFY_API_TOKEN)

    all_posts = []

    # TikTok
    log.info("Fetching TikTok posts...")
    try:
        scraper = TikTokScraper(apify)
        posts = scraper.fetch(config.TIKTOK_HASHTAGS, config.MAX_POSTS_PER_PLATFORM)
        log.info(f"  TikTok: {len(posts)} posts fetched")
        db.log_run(today, "tiktok", len(posts), "success")
        all_posts.extend(posts)
    except Exception as e:
        log.error(f"  TikTok scrape failed: {e}")
        db.log_run(today, "tiktok", 0, "error", str(e))

    # Instagram
    log.info("Fetching Instagram posts...")
    try:
        scraper = InstagramScraper(apify)
        posts = scraper.fetch(config.INSTAGRAM_HASHTAGS, config.MAX_POSTS_PER_PLATFORM)
        log.info(f"  Instagram: {len(posts)} posts fetched")
        db.log_run(today, "instagram", len(posts), "success")
        all_posts.extend(posts)
    except Exception as e:
        log.error(f"  Instagram scrape failed: {e}")
        db.log_run(today, "instagram", 0, "error", str(e))

    # YouTube
    log.info("Fetching YouTube posts...")
    try:
        scraper = YouTubeScraper(apify)
        posts = scraper.fetch(config.YOUTUBE_SEARCH_QUERIES, config.MAX_POSTS_PER_PLATFORM)
        log.info(f"  YouTube: {len(posts)} posts fetched")
        db.log_run(today, "youtube", len(posts), "success")
        all_posts.extend(posts)
    except Exception as e:
        log.error(f"  YouTube scrape failed: {e}")
        db.log_run(today, "youtube", 0, "error", str(e))

    if not all_posts:
        log.warning("No posts collected. Exiting.")
        return

    # Score + store
    log.info(f"Scoring {len(all_posts)} posts...")
    scored = compute_virality_scores(all_posts)
    db.insert_posts(scored)
    log.info("Posts saved to database.")

    # Push to Google Sheets
    try:
        from pipeline.sheets import push_daily_digest
        top_posts = db.get_top_posts(today, limit=config.SHEETS_TOP_N)
        rows_pushed = push_daily_digest(top_posts, today)
        db.log_sheets_push(today, rows_pushed)
        log.info(f"Google Sheets updated: {rows_pushed} rows pushed.")
    except Exception as e:
        log.error(f"Google Sheets push failed: {e}")

    log.info("Pipeline complete.")


if __name__ == "__main__":
    run_pipeline()
