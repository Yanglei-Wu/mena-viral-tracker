from datetime import datetime, timezone
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import Post

ACTOR_ID = "apify/instagram-hashtag-scraper"


class InstagramScraper:
    def __init__(self, apify: ApifyWrapper):
        self._apify = apify

    def fetch(self, hashtags: list[str], max_results: int = 200) -> list[Post]:
        run_input = {
            "hashtags": hashtags,
            "resultsType": "posts",
            "resultsLimit": max_results,
        }
        raw = self._apify.run_actor(ACTOR_ID, run_input, max_items=max_results)
        scraped_at = datetime.now(timezone.utc)
        posts = []
        for item in raw:
            try:
                posts.append(_normalize(item, scraped_at))
            except (KeyError, TypeError):
                continue
        return posts


def _normalize(item: dict, scraped_at: datetime) -> Post:
    ts = item.get("timestamp")
    posted_at = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
    raw_type = item.get("type", "")
    content_type = "reel" if raw_type == "Video" else "image"
    short_code = item.get("shortCode", "")
    url = f"https://www.instagram.com/p/{short_code}/" if short_code else ""
    hashtags = item.get("hashtags", [])
    if hashtags and isinstance(hashtags[0], dict):
        hashtags = [h.get("name", "") for h in hashtags]

    return Post(
        platform="instagram",
        post_id=str(item["id"]),
        url=url,
        author=item.get("ownerUsername", ""),
        followers=int(item.get("followersCount", 0)),
        views=int(item.get("videoViewCount", 0) or item.get("likesCount", 0)),
        likes=int(item.get("likesCount", 0)),
        comments=int(item.get("commentsCount", 0)),
        shares=0,  # Instagram does not expose share count via API
        caption=item.get("caption", ""),
        hashtags=hashtags,
        content_type=content_type,
        posted_at=posted_at,
        scraped_at=scraped_at,
    )
