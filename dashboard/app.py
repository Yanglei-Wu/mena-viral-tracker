"""
Run locally: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

import config
from db.database import Database

st.set_page_config(
    page_title="MENA Viral Tracker",
    page_icon="📊",
    layout="wide",
)

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.title("Filters")

today = date.today()
start_date, end_date = st.sidebar.date_input(
    "Date range",
    value=(today - timedelta(days=7), today),
    max_value=today,
)

platform_options = ["All", "tiktok", "instagram", "youtube"]
selected_platform = st.sidebar.selectbox("Platform", platform_options)
min_score = st.sidebar.slider("Min virality score", 0.0, 2.0, 0.0, step=0.1)

platform_filter = None if selected_platform == "All" else selected_platform

# ── Load data ────────────────────────────────────────────────────────────────
db = Database(config.DB_PATH)
db.init()
posts = db.get_posts(start_date, end_date, platform=platform_filter)
posts = [p for p in posts if p.virality_score >= min_score]

if not posts:
    st.warning("No posts found for the selected filters.")
    st.stop()

df = pd.DataFrame([{
    "platform": p.platform,
    "author": p.author,
    "views": p.views,
    "likes": p.likes,
    "comments": p.comments,
    "shares": p.shares,
    "virality_score": p.virality_score,
    "content_type": p.content_type,
    "posted_at": p.posted_at,
    "scraped_at": p.scraped_at,
    "url": p.url,
    "caption": p.caption[:120] + "..." if p.caption and len(p.caption) > 120 else p.caption,
    "engagement_rate": round((p.likes + p.comments + p.shares) / p.views * 100, 2) if p.views > 0 else 0,
    "ai_analysis": p.ai_analysis,
} for p in posts])

# ── View: Today's Trends ─────────────────────────────────────────────────────
st.title("MENA Viral Content Tracker")
st.subheader("Today's Trends")

latest_date = df["scraped_at"].apply(lambda x: x.date() if x else None).max()
today_df = df[df["scraped_at"].apply(lambda x: x.date() if x else None) == latest_date]
top10 = today_df.nlargest(10, "virality_score")

if top10.empty:
    st.info("No posts from the latest run.")
else:
    cols = st.columns(2)
    for i, (_, row) in enumerate(top10.iterrows()):
        col = cols[i % 2]
        with col:
            platform_emoji = {"tiktok": "🎵", "instagram": "📸", "youtube": "▶️"}.get(row["platform"], "🌐")
            st.markdown(f"""
**{platform_emoji} {row['platform'].capitalize()}** — score: `{row['virality_score']}`

👤 @{row['author']} · 👁 {row['views']:,} views · ❤️ {row['likes']:,} likes

_{row['caption']}_

[Open post]({row['url']})
""")
            if row.get("ai_analysis"):
                with st.expander("🤖 Why it went viral"):
                    st.markdown(row["ai_analysis"])
            st.divider()

# ── View: Leaderboard ────────────────────────────────────────────────────────
st.subheader("Leaderboard")

leaderboard = df[[
    "platform", "author", "views", "likes", "comments",
    "engagement_rate", "virality_score", "url",
]].sort_values("virality_score", ascending=False).reset_index(drop=True)

st.dataframe(
    leaderboard,
    use_container_width=True,
    column_config={
        "url": st.column_config.LinkColumn("Link"),
        "virality_score": st.column_config.NumberColumn("Score", format="%.2f"),
        "engagement_rate": st.column_config.NumberColumn("Eng. Rate %", format="%.2f"),
        "views": st.column_config.NumberColumn("Views", format="%d"),
    },
)

ai_posts = [p for p in posts if p.ai_analysis]
if ai_posts:
    st.markdown("#### AI Analysis Details")
    for post in ai_posts:
        with st.expander(f"🤖 @{post.author} — score {post.virality_score:.2f}"):
            st.markdown(post.ai_analysis)

# ── View: Platform Breakdown ─────────────────────────────────────────────────
st.subheader("Platform Breakdown")

col1, col2 = st.columns(2)

with col1:
    avg_score = df.groupby("platform")["virality_score"].mean().reset_index()
    fig = px.bar(avg_score, x="platform", y="virality_score",
                 title="Avg Virality Score by Platform",
                 color="platform", color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    post_counts = df.groupby("platform").size().reset_index(name="post_count")
    fig2 = px.bar(post_counts, x="platform", y="post_count",
                  title="Posts Tracked by Platform",
                  color="platform", color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig2, use_container_width=True)

# ── View: Trend Over Time ────────────────────────────────────────────────────
st.subheader("Trend Over Time")

df["scrape_date"] = df["scraped_at"].apply(lambda x: x.date() if x else None)
trend = df.groupby(["scrape_date", "platform"])["virality_score"].mean().reset_index()
trend.columns = ["date", "platform", "avg_virality_score"]

fig3 = px.line(trend, x="date", y="avg_virality_score", color="platform",
               title="Daily Avg Virality Score per Platform",
               markers=True,
               color_discrete_sequence=px.colors.qualitative.Set2)
st.plotly_chart(fig3, use_container_width=True)
