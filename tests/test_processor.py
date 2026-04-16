from datetime import datetime, timedelta, timezone
import pytest
from pipeline.processor import Post, compute_virality_scores


def make_post(post_id="p1", views=10000, likes=500, comments=100, shares=50,
              hours_old=5) -> Post:
    now = datetime.now(timezone.utc)
    return Post(
        platform="tiktok",
        post_id=post_id,
        url="https://example.com",
        author="user",
        followers=10000,
        views=views,
        likes=likes,
        comments=comments,
        shares=shares,
        caption="test",
        hashtags=[],
        content_type="video",
        posted_at=now - timedelta(hours=hours_old),
        scraped_at=now,
        virality_score=0.0,
    )


def test_virality_score_assigned_to_all_posts():
    posts = [make_post("p1"), make_post("p2"), make_post("p3")]
    result = compute_virality_scores(posts)
    assert all(isinstance(p.virality_score, float) for p in result)


def test_higher_engagement_gets_higher_score():
    low = make_post("low", views=10000, likes=100, comments=10, shares=5)
    high = make_post("high", views=10000, likes=5000, comments=1000, shares=500)
    result = compute_virality_scores([low, high])
    scores = {p.post_id: p.virality_score for p in result}
    assert scores["high"] > scores["low"]


def test_scores_bounded_between_0_and_2():
    posts = [make_post(f"p{i}", views=i * 1000, likes=i * 50) for i in range(1, 6)]
    result = compute_virality_scores(posts)
    assert all(0.0 <= p.virality_score <= 2.0 for p in result)


def test_posts_less_than_1_hour_old_excluded():
    fresh = make_post("fresh", hours_old=0)
    old = make_post("old", hours_old=24)
    result = compute_virality_scores([fresh, old])
    fresh_result = next(p for p in result if p.post_id == "fresh")
    assert fresh_result.virality_score == 0.0


def test_single_post_gets_score_of_0():
    posts = [make_post("only")]
    result = compute_virality_scores(posts)
    assert result[0].virality_score == 0.0


def test_zero_views_post_excluded_from_scoring():
    zero_views = make_post("zero", views=0)
    normal = make_post("normal", views=50000)
    result = compute_virality_scores([zero_views, normal])
    zero_result = next(p for p in result if p.post_id == "zero")
    assert zero_result.virality_score == 0.0
