from dataclasses import dataclass
from datetime import datetime
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
