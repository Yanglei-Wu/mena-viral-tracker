import re
from datetime import datetime, timezone
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import Post

ACTOR_ID = "streamers/youtube-scraper"


class YouTubeScraper:
    def __init__(self, apify: ApifyWrapper):
        self._apify = apify

    def fetch(self, queries: list[str], max_results: int = 200) -> list[Post]:
        run_input = {
            "searchKeywords": queries,
            "maxResults": max_results,
            "language": "ar",
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
    ts = item.get("publishedAt")
    posted_at = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
    description = item.get("description", "")
    hashtags = re.findall(r"#(\w+)", description)
    title = item.get("title", "")
    caption = f"{title}\n{description}".strip()

    return Post(
        platform="youtube",
        post_id=str(item["id"]),
        url=item.get("url", ""),
        author=item.get("channelName", ""),
        followers=int(item.get("numberOfSubscribers", 0)),
        views=int(item.get("viewCount", 0)),
        likes=int(item.get("likes", 0)),
        comments=int(item.get("commentsCount", 0)),
        shares=0,  # YouTube does not expose share count
        caption=caption,
        hashtags=hashtags,
        content_type="video",
        posted_at=posted_at,
        scraped_at=scraped_at,
    )
