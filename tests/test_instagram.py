from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from pipeline.scrapers.instagram import InstagramScraper


FAKE_RAW = [
    {
        "id": "ig_post_001",
        "shortCode": "ABC123",
        "caption": "محتوى رائع #ترند",
        "timestamp": "2026-04-15T10:00:00.000Z",
        "likesCount": 25000,
        "commentsCount": 1200,
        "videoViewCount": 500000,
        "ownerUsername": "arabcreator",
        "followersCount": 180000,
        "type": "Video",
        "hashtags": ["ترند", "انستقرام"],
    }
]


@pytest.fixture
def scraper():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = FAKE_RAW
    return InstagramScraper(mock_apify)


def test_returns_post_list(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert len(posts) == 1


def test_platform_is_instagram(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    assert posts[0].platform == "instagram"


def test_fields_mapped_correctly(scraper):
    posts = scraper.fetch(hashtags=["ترند"], max_results=10)
    p = posts[0]
    assert p.post_id == "ig_post_001"
    assert "ABC123" in p.url
    assert p.author == "arabcreator"
    assert p.followers == 180000
    assert p.views == 500000
    assert p.likes == 25000
    assert p.comments == 1200
    assert p.content_type == "reel"
    assert "ترند" in p.hashtags


def test_image_post_type_mapped(scraper):
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = [{**FAKE_RAW[0], "type": "Image", "videoViewCount": 0}]
    s = InstagramScraper(mock_apify)
    posts = s.fetch(hashtags=["ترند"], max_results=10)
    assert posts[0].content_type == "image"


def test_empty_raw_returns_empty_list():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = []
    s = InstagramScraper(mock_apify)
    assert s.fetch(hashtags=["ترند"], max_results=10) == []
