from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from pathlib import Path

from pipeline.processor import Post


def make_post():
    return Post(
        platform="tiktok",
        post_id="vid123",
        url="https://tiktok.com/@user/video/vid123",
        author="testuser",
        followers=1000,
        views=100000,
        likes=8000,
        comments=500,
        shares=200,
        caption="test caption",
        hashtags=["ترند"],
        content_type="video",
        posted_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        scraped_at=datetime(2026, 4, 16, tzinfo=timezone.utc),
        virality_score=1.5,
    )


def test_analyze_posts_saves_on_success(monkeypatch):
    import config
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key-for-testing")
    mock_db = MagicMock()
    post = make_post()
    with patch("pipeline.analyzer._download", return_value=Path("/tmp/mena_tracker_videos/vid123.mp4")), \
         patch("pipeline.analyzer._analyze", return_value="• reason1\n• reason2"), \
         patch("google.genai.Client"):
        from pipeline.analyzer import analyze_posts
        analyze_posts([post], mock_db)
    mock_db.save_analysis.assert_called_once()
    args = mock_db.save_analysis.call_args[0]
    assert args[0] == "tiktok"
    assert args[1] == "vid123"
    assert args[2] == "2026-04-16"
    assert args[3] == "• reason1\n• reason2"


def test_analyze_posts_skips_when_no_key(monkeypatch):
    import config
    monkeypatch.setattr(config, "GEMINI_API_KEY", "")
    mock_db = MagicMock()
    from pipeline.analyzer import analyze_posts
    analyze_posts([make_post()], mock_db)
    mock_db.save_analysis.assert_not_called()


def test_analyze_posts_continues_after_failure(monkeypatch):
    import config
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key-for-testing")
    mock_db = MagicMock()
    p1 = make_post()
    p2 = Post(**{**p1.__dict__, "post_id": "vid456"})
    with patch("pipeline.analyzer._download", side_effect=Exception("network error")), \
         patch("google.genai.Client"):
        from pipeline.analyzer import analyze_posts
        analyze_posts([p1, p2], mock_db)  # must not raise
    mock_db.save_analysis.assert_not_called()


def test_analyze_posts_skips_when_download_returns_none(monkeypatch):
    import config
    monkeypatch.setattr(config, "GEMINI_API_KEY", "fake-key-for-testing")
    mock_db = MagicMock()
    post = make_post()
    with patch("pipeline.analyzer._download", return_value=None), \
         patch("google.genai.Client"):
        from pipeline.analyzer import analyze_posts
        analyze_posts([post], mock_db)
    mock_db.save_analysis.assert_not_called()
