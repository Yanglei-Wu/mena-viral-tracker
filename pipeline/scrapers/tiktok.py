from datetime import datetime, timezone
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import Post

ACTOR_ID = "clockworks/tiktok-scraper"


class TikTokScraper:
    def __init__(self, apify: ApifyWrapper):
        self._apify = apify

    def fetch(self, hashtags: list[str], max_results: int = 200) -> list[Post]:
        run_input = {
            "hashtags": hashtags,
            "resultsPerPage": min(max_results, 50),
            "maxResults": max_results,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
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
    author_meta = item.get("authorMeta", {})
    hashtags = [h["name"] for h in item.get("hashtags", []) if "name" in h]
    create_time = item.get("createTime")
    posted_at = (
        datetime.fromtimestamp(create_time, tz=timezone.utc) if create_time else None
    )
    return Post(
        platform="tiktok",
        post_id=str(item["id"]),
        url=item.get("webVideoUrl", ""),
        author=author_meta.get("name", ""),
        followers=int(author_meta.get("fans", 0)),
        views=int(item.get("playCount", 0)),
        likes=int(item.get("diggCount", 0)),
        comments=int(item.get("commentCount", 0)),
        shares=int(item.get("shareCount", 0)),
        caption=item.get("text", ""),
        hashtags=hashtags,
        content_type="video",
        posted_at=posted_at,
        scraped_at=scraped_at,
    )
