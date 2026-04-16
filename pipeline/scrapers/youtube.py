import re
from datetime import datetime, timezone
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import Post

ACTOR_ID = "streamers/youtube-scraper"


class YouTubeScraper:
    def __init__(self, apify: ApifyWrapper):
        self._apify = apify

    def fetch(self, queries: list[str], max_results: int = 200) -> list[Post]:
        """Fetch by running one actor call per query and merging results."""
        per_query = max(max_results // len(queries), 10) if queries else max_results
        scraped_at = datetime.now(timezone.utc)
        seen_ids: set[str] = set()
        posts = []

        for query in queries:
            if len(posts) >= max_results:
                break
            run_input = {
                "searchKeywords": query,
                "maxResults": per_query,
            }
            raw = self._apify.run_actor(ACTOR_ID, run_input, max_items=per_query)
            for item in raw:
                if len(posts) >= max_results:
                    break
                try:
                    post = _normalize(item, scraped_at)
                    if post.post_id not in seen_ids:
                        seen_ids.add(post.post_id)
                        posts.append(post)
                except (KeyError, TypeError):
                    continue

        return posts


def _normalize(item: dict, scraped_at: datetime) -> Post:
    ts = item.get("date")
    posted_at = datetime.fromisoformat(ts.replace("Z", "+00:00")) if ts else None
    text = item.get("text", "")
    title = item.get("title", "")
    caption = f"{title}\n{text}".strip()

    # Use actor-provided hashtags list; fall back to regex on text
    raw_hashtags = item.get("hashtags") or []
    if not raw_hashtags and text:
        raw_hashtags = re.findall(r"#(\w+)", text)

    return Post(
        platform="youtube",
        post_id=str(item["id"]),
        url=item.get("url", ""),
        author=item.get("channelName", ""),
        followers=int(item.get("numberOfSubscribers", 0) or 0),
        views=int(item.get("viewCount", 0) or 0),
        likes=int(item.get("likes", 0) or 0),
        comments=int(item.get("commentsCount", 0) or 0),
        shares=0,  # YouTube does not expose share count
        caption=caption,
        hashtags=raw_hashtags,
        content_type="video",
        posted_at=posted_at,
        scraped_at=scraped_at,
    )
