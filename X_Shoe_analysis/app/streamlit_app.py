import os
import sys
from typing import Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Ensure both project root and app dir are on sys.path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
for p in [PROJECT_ROOT, CURRENT_DIR]:
	if p not in sys.path:
		sys.path.insert(0, p)

try:
	from app.collectors.reddit import fetch_reddit_posts, fetch_reddit_comments
	from app.collectors.youtube import search_youtube_videos, fetch_video_stats
	from app.collectors.trends import fetch_trends
	from app.analysis.scoring import aggregate_signal
	from app.viz.charts import bar_scores, radar_components, bar_components, donut_components, stacked_engagement, sentiment_density
except ModuleNotFoundError:
	from collectors.reddit import fetch_reddit_posts, fetch_reddit_comments
	from collectors.youtube import search_youtube_videos, fetch_video_stats
	from collectors.trends import fetch_trends
	from analysis.scoring import aggregate_signal
	from viz.charts import bar_scores, radar_components, bar_components, donut_components, stacked_engagement, sentiment_density


load_dotenv()

st.set_page_config(page_title="X Shoe Store: Chennai Entry Analysis", layout="wide")
st.title("X Shoe Store – Chennai Location Decision")

st.sidebar.header("Controls")
mall_keywords = [
	"Phoenix Marketcity Chennai",
	"VR Chennai",
	"Express Avenue",
	"Forum Vijaya Mall",
]
high_street_keywords = [
	"T Nagar",
	"Nungambakkam",
	"Khader Nawaz Khan Road",
	"Anna Nagar",
]

default_queries = ["sneakers", "running shoes", "basketball shoes", "sportswear", "streetwear", "athleisure"]

query_terms: List[str] = st.sidebar.multiselect("Search topics", default_queries, default=default_queries)
geo = st.sidebar.selectbox("Google Trends geo", ["IN-TN", "IN-TN-CH"], index=0)
reddit_subs = st.sidebar.text_input("Reddit subs (comma)", value="bangalore,mumbai,chennai,india,IndianStreetWear,Sneakers")
limit = st.sidebar.slider("Results per source", 50, 300, 150, step=50)
auto_run = st.sidebar.checkbox("Auto-run on load (once)", value=True)
use_cached = st.sidebar.checkbox("Use cached CSVs in data/ if available", value=True)
run_button = st.sidebar.button("Run Analysis")

# Trigger once on first load if auto_run is enabled and credentials exist
has_keys = bool(os.getenv("YOUTUBE_API_KEY") and os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET"))
if "_first_load_done" not in st.session_state:
	st.session_state["_first_load_done"] = False
run_trigger = run_button or (auto_run and not st.session_state["_first_load_done"] and has_keys)
if run_trigger and not st.session_state["_first_load_done"]:
	st.session_state["_first_load_done"] = True

placeholder = st.empty()

if run_trigger:
	with st.spinner("Collecting data..."):
		data_dir = os.path.join(PROJECT_ROOT, "data")
		os.makedirs(data_dir, exist_ok=True)

		# Reddit
		posts_csv = os.path.join(data_dir, "reddit_posts.csv")
		comments_csv = os.path.join(data_dir, "reddit_comments.csv")
		if use_cached and os.path.exists(posts_csv):
			posts = pd.read_csv(posts_csv)
			comments = pd.read_csv(comments_csv) if os.path.exists(comments_csv) else pd.DataFrame()
		else:
			try:
				posts = fetch_reddit_posts(query_terms=query_terms, subreddits=[s.strip() for s in reddit_subs.split(",") if s.strip()], limit=limit)
				comments = fetch_reddit_comments(posts["id"].tolist()[:20]) if not posts.empty else pd.DataFrame()
				posts.to_csv(posts_csv, index=False)
				if not comments.empty:
					comments.to_csv(comments_csv, index=False)
			except Exception as e:
				st.warning(f"Reddit collection failed: {e}")
				posts, comments = pd.DataFrame(), pd.DataFrame()

		# YouTube
		ytv_csv = os.path.join(data_dir, "youtube_videos.csv")
		yts_csv = os.path.join(data_dir, "youtube_stats.csv")
		if use_cached and os.path.exists(ytv_csv):
			ytv = pd.read_csv(ytv_csv)
			yts = pd.read_csv(yts_csv) if os.path.exists(yts_csv) else pd.DataFrame()
		else:
			try:
				yt_df_list = []
				for q in query_terms:
					yt_df_list.append(search_youtube_videos(f"{q} Chennai", max_results=min(50, limit)))
				ytv = pd.concat(yt_df_list, ignore_index=True) if yt_df_list else pd.DataFrame()
				yts = fetch_video_stats(ytv["video_id"].dropna().unique().tolist()) if not ytv.empty else pd.DataFrame()
				if not ytv.empty:
					ytv.to_csv(ytv_csv, index=False)
				if not yts.empty:
					yts.to_csv(yts_csv, index=False)
			except Exception as e:
				st.warning(f"YouTube collection failed: {e}")
				ytv, yts = pd.DataFrame(), pd.DataFrame()

		# Trends
		trends_csv = os.path.join(data_dir, "trends.csv")
		if use_cached and os.path.exists(trends_csv):
			trends = pd.read_csv(trends_csv)
		else:
			try:
				trends = fetch_trends(queries=query_terms, geo=geo)
				if not trends.empty:
					trends.to_csv(trends_csv, index=False)
			except Exception as e:
				st.warning(f"Trends collection failed: {e}")
				trends = pd.DataFrame()

		# Scoring
		places: Dict[str, List[str]] = {
			"Malls": mall_keywords,
			"High Streets": high_street_keywords,
		}
		result = aggregate_signal(reddit_posts=posts, reddit_comments=comments, yt_videos=ytv, yt_stats=yts, trends_df=trends, location_keywords=places)

		st.subheader("Fit Score: Malls vs High Streets")
		fig = bar_scores(result)
		if fig:
			st.plotly_chart(fig, use_container_width=True)

		st.subheader("Signal Components")
		chart_type = st.selectbox("Component chart type", ["Radar", "Bar", "Donut"], index=1)
		if chart_type == "Radar":
			fig2 = radar_components(result)
		elif chart_type == "Bar":
			fig2 = bar_components(result)
		else:
			fig2 = donut_components(result)
		if fig2:
			st.plotly_chart(fig2, use_container_width=True)

		st.subheader("Engagement Breakdown")
		fig3 = stacked_engagement(result)
		if fig3:
			st.plotly_chart(fig3, use_container_width=True)

		st.subheader("Sentiment Overview")
		fig4 = sentiment_density(result)
		if fig4:
			st.plotly_chart(fig4, use_container_width=True)

		st.subheader("Data Snapshots")
		col1, col2, col3 = st.columns(3)
		with col1:
			st.caption("Reddit posts")
			st.dataframe(posts.head(20))
		with col2:
			st.caption("YouTube videos")
			st.dataframe(ytv.head(20))
		with col3:
			st.caption("Google Trends")
			st.dataframe(trends.tail(10))

		# Insight
		st.subheader("Sharp Insight")
		if not result.empty:
			best = result.iloc[0]
			insight = f"{best['place']} show the strongest composite signal driven by engagement ({best['engagement']:.0f}) and sentiment ({best['sentiment']:.2f})."
			st.success(insight)

		st.subheader("Authentic Launch Suggestions")
		st.markdown(
			"- Collaborate with local sneaker and streetwear communities in Chennai for pop-ups and UGC.\n"
			"- Influencer runs from T Nagar to EA Mall showcasing everyday-to-premium product transitions.\n"
			"- Limited-edition Chennai colorway drop tied to local sports culture (CSK/Marina)."
		)

if not (os.getenv("YOUTUBE_API_KEY") and os.getenv("REDDIT_CLIENT_ID") and os.getenv("REDDIT_CLIENT_SECRET")):
	st.info("Set environment variables YOUTUBE_API_KEY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, and optionally REDDIT_USER_AGENT. Then run: streamlit run app/streamlit_app.py")


