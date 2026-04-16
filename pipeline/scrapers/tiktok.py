from datetime import datetime, timezone
from typing import Optional
from pipeline.apify_client import ApifyWrapper
from pipeline.processor import Post

ACTOR_ID = "clockworks/tiktok-scraper"


class TikTokScraper:
    def __init__(self, apify: ApifyWrapper):
        self._apify = apify

    def fetch(
        self,
        hashtags: list[str],
        max_results: int = 200,
        proxy_countries: Optional[list[str]] = None,
    ) -> list[Post]:
        """
        Fetch TikTok posts by hashtag.
        If proxy_countries is provided, runs one actor call per country
        and merges results — each country gets an equal share of max_results.
        """
        if proxy_countries:
            return self._fetch_by_countries(hashtags, max_results, proxy_countries)
        return self._fetch_one(hashtags, max_results, proxy_country=None)

    def _fetch_by_countries(
        self, hashtags: list[str], max_results: int, proxy_countries: list[str]
    ) -> list[Post]:
        per_country = max(max_results // len(proxy_countries), 10)
        seen_ids: set[str] = set()
        posts = []
        for country in proxy_countries:
            batch = self._fetch_one(hashtags, per_country, proxy_country=country)
            for post in batch:
                if post.post_id not in seen_ids:
                    seen_ids.add(post.post_id)
                    posts.append(post)
        return posts

    def _fetch_one(
        self, hashtags: list[str], max_results: int, proxy_country: Optional[str]
    ) -> list[Post]:
        run_input = {
            "hashtags": hashtags,
            "resultsPerPage": min(max_results, 50),
            "maxResults": max_results,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        }
        if proxy_country:
            run_input["proxyCountryCode"] = proxy_country

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
