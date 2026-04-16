from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from pipeline.scrapers.youtube import YouTubeScraper


FAKE_RAW = [
    {
        "id": "yt_vid_xyz",
        "url": "https://www.youtube.com/watch?v=yt_vid_xyz",
        "title": "فيديو ترند عربي",
        "description": "محتوى رائع جداً #ترند",
        "publishedAt": "2026-04-15T08:00:00Z",
        "viewCount": 2000000,
        "likes": 80000,
        "commentsCount": 12000,
        "channelName": "ArabChannel",
        "numberOfSubscribers": 500000,
    }
]


@pytest.fixture
def scraper():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = FAKE_RAW
    return YouTubeScraper(mock_apify)


def test_returns_post_list(scraper):
    posts = scraper.fetch(queries=["ترند عربي"], max_results=10)
    assert len(posts) == 1


def test_platform_is_youtube(scraper):
    posts = scraper.fetch(queries=["ترند عربي"], max_results=10)
    assert posts[0].platform == "youtube"


def test_fields_mapped_correctly(scraper):
    posts = scraper.fetch(queries=["ترند عربي"], max_results=10)
    p = posts[0]
    assert p.post_id == "yt_vid_xyz"
    assert p.url == "https://www.youtube.com/watch?v=yt_vid_xyz"
    assert p.author == "ArabChannel"
    assert p.followers == 500000
    assert p.views == 2000000
    assert p.likes == 80000
    assert p.comments == 12000
    assert p.content_type == "video"


def test_hashtags_extracted_from_description(scraper):
    posts = scraper.fetch(queries=["ترند عربي"], max_results=10)
    assert "ترند" in posts[0].hashtags


def test_empty_raw_returns_empty_list():
    mock_apify = MagicMock()
    mock_apify.run_actor.return_value = []
    s = YouTubeScraper(mock_apify)
    assert s.fetch(queries=["ترند"], max_results=10) == []
