import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget
from google import genai

import config
from db.database import Database
from pipeline.processor import Post

log = logging.getLogger(__name__)

TEMP_DIR = Path("/tmp/mena_tracker_videos")
_POLL_TIMEOUT_SECS = 300  # 5 minutes max wait for Gemini file processing

PROMPT_TEMPLATE = """You are a social media analyst specializing in Arabic and MENA content.

Watch this TikTok video. Context:
- Caption: {caption}
- Hashtags: {hashtags}
- Views: {views:,} | Likes: {likes:,} | Comments: {comments:,} | Shares: {shares:,}
- Virality Score: {virality_score:.2f}/2.0

Explain in 4-5 bullet points why this video went viral in the MENA region:
\u2022 Visual hook (first 3 seconds)
\u2022 Content format/style
\u2022 Audio or music
\u2022 Cultural/regional relevance
\u2022 Key engagement trigger

Respond in English. Be specific to what you see in the video."""


def analyze_posts(posts: list[Post], db: Database) -> None:
    if not config.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set — skipping AI analysis.")
        return

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    for post in posts:
        video_path = None
        # Derive scraped_date from the post itself (UTC) to match insert_posts
        scraped_date = (
            post.scraped_at.date().isoformat() if post.scraped_at else
            datetime.now(timezone.utc).date().isoformat()
        )
        try:
            # Remove any stale partial files from prior runs
            for stale in TEMP_DIR.glob(f"{post.post_id}.*"):
                stale.unlink(missing_ok=True)

            video_path = _download(post)
            if not video_path:
                log.warning(f"Download returned nothing for {post.post_id}, skipping.")
                continue
            analysis = _analyze(client, video_path, post)
            analyzed_at = datetime.now(timezone.utc).isoformat()
            db.save_analysis(post.platform, post.post_id, scraped_date, analysis, analyzed_at)
            log.info(f"  Analyzed {post.post_id} (@{post.author})")
        except Exception as e:
            log.error(f"  Analysis failed for {post.post_id}: {e}")
        finally:
            if video_path and video_path.exists():
                video_path.unlink()


def _download(post: Post) -> Optional[Path]:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    base_opts = {
        "outtmpl": str(TEMP_DIR / f"{post.post_id}.%(ext)s"),
        "format": "mp4/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "impersonate": ImpersonateTarget("chrome", None, None, None),
    }
    # Try with Chrome cookies first (works on local dev); fall back without
    # cookies for CI/container environments where the browser profile is absent.
    attempts = [
        {**base_opts, "cookiesfrombrowser": ("chrome",)},
        base_opts,
    ]
    for opts in attempts:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([post.url])
            matches = list(TEMP_DIR.glob(f"{post.post_id}.*"))
            if matches:
                return matches[0]
        except Exception:
            # Clean up any partial file before retrying
            for f in TEMP_DIR.glob(f"{post.post_id}.*"):
                f.unlink(missing_ok=True)
    return None


def _analyze(client: genai.Client, video_path: Path, post: Post) -> str:
    suffix_to_mime = {".mp4": "video/mp4", ".webm": "video/webm"}
    mime = suffix_to_mime.get(video_path.suffix, "video/mp4")

    video_file = client.files.upload(
        file=str(video_path),
        config={"mime_type": mime},
    )

    # Poll with timeout to avoid infinite hang
    max_polls = _POLL_TIMEOUT_SECS // 5
    for _ in range(max_polls):
        if video_file.state.name != "PROCESSING":
            break
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)
    else:
        client.files.delete(name=video_file.name)
        raise RuntimeError(f"Gemini file processing timed out after {_POLL_TIMEOUT_SECS}s")

    if video_file.state.name != "ACTIVE":
        client.files.delete(name=video_file.name)
        raise RuntimeError(f"Gemini file processing failed: {video_file.state.name}")

    prompt = PROMPT_TEMPLATE.format(
        caption=post.caption[:500],
        hashtags=", ".join(post.hashtags[:10]),
        views=post.views,
        likes=post.likes,
        comments=post.comments,
        shares=post.shares,
        virality_score=post.virality_score,
    )
    try:
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[video_file, prompt],
        )
    finally:
        client.files.delete(name=video_file.name)
    return response.text
