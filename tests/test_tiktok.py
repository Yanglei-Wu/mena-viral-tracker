from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from pipeline.scrapers.tiktok import TikTokScraper


FAKE_RAW = [
    {
        "id": "vid123",
        "webVideoUrl": "https://www.tiktok.com/@testuser/video/vid123",
        "text": "اختبار #ترند #فيروسي",
        "createTime": 1713225600,  # 2024-04-15 12:00 UTC
        "authorMeta": {"name": "testuser", "fans": 250000},
        "diggCount": 15000,
        "shareCount": 3000,
        "playCount": 800000,
        "commentCount": 4500,
        "hashtags": [{"name": "ترند"}, {"name": "فيروسي"}],
    }
]


@pytest.fixture
def scraper():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = FAKE_RAW
    return TikTokScraper(mock_apify)


def test_returns_post_list(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert len(posts) == 1


def test_platform_is_tiktok(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert posts[0].platform == "tiktok"


def test_fields_mapped_correctly(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    p = posts[0]
    assert p.post_id == "vid123"
    assert p.url == "https://www.tiktok.com/@testuser/video/vid123"
    assert p.author == "testuser"
    assert p.followers == 250000
    assert p.views == 800000
    assert p.likes == 15000
    assert p.comments == 4500
    assert p.shares == 3000
    assert p.content_type == "video"
    assert "ترند" in p.hashtags
    assert "فيروسي" in p.hashtags


def test_caption_extracted(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert posts[0].caption == "اختبار #ترند #فيروسي"


def test_empty_raw_returns_empty_list():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = []
    scraper = TikTokScraper(mock_apify)
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert posts == []
