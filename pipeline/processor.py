from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Post:
    platform: str
    post_id: str
    url: str
    author: str
    followers: int
    views: int
    likes: int
    comments: int
    shares: int
    caption: str
    hashtags: list[str]
    content_type: str
    posted_at: Optional[datetime]
    scraped_at: Optional[datetime]
    virality_score: float = 0.0


def compute_virality_scores(posts: list[Post]) -> list[Post]:
    """
    Score each post 0–2 using min-max normalized engagement rate + velocity.
    Posts with 0 views or < 1 hour old receive a score of 0 and are excluded
    from normalization so they don't distort the pool.
    """
    now = datetime.now(timezone.utc)
    scoreable = []

    for post in posts:
        if post.views == 0 or post.posted_at is None:
            continue
        posted_at = post.posted_at
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (now - posted_at).total_seconds() / 3600
        if age_hours < 1:
            continue
        scoreable.append(post)

    if len(scoreable) < 2:
        return posts

    eng_rates = [
        (p.likes + p.comments + p.shares) / p.views for p in scoreable
    ]
    velocities = []
    for p in scoreable:
        posted_at = p.posted_at
        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=timezone.utc)
        age_hours = (now - posted_at).total_seconds() / 3600
        velocities.append(p.views / age_hours)

    norm_eng = _min_max_normalize(eng_rates)
    norm_vel = _min_max_normalize(velocities)

    score_map: dict[str, float] = {}
    for post, ne, nv in zip(scoreable, norm_eng, norm_vel):
        score_map[post.post_id] = round(ne + nv, 4)

    for post in posts:
        post.virality_score = score_map.get(post.post_id, 0.0)

    return posts


def _min_max_normalize(values: list[float]) -> list[float]:
    min_v = min(values)
    max_v = max(values)
    if max_v == min_v:
        return [0.0] * len(values)
    return [(v - min_v) / (max_v - min_v) for v in values]
