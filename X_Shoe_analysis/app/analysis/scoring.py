from typing import Dict, List

import numpy as np
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


def compute_sentiment_scores(texts: List[str]) -> pd.DataFrame:
	analyzer = SentimentIntensityAnalyzer()
	scores = [analyzer.polarity_scores(t or "") for t in texts]
	return pd.DataFrame(scores)


def aggregate_signal(
	reddit_posts: pd.DataFrame,
	reddit_comments: pd.DataFrame,
	yt_videos: pd.DataFrame,
	yt_stats: pd.DataFrame,
	trends_df: pd.DataFrame,
	location_keywords: Dict[str, List[str]],
):
	results: List[Dict[str, float]] = []  # type: ignore
	for place, keywords in location_keywords.items():
		# Reddit
		posts_mask = reddit_posts["title"].str.contains("|".join(keywords), case=False, na=False) | reddit_posts["selftext"].str.contains("|".join(keywords), case=False, na=False)
		posts_subset = reddit_posts.loc[posts_mask]
		post_engagement = float(posts_subset["score"].sum() + posts_subset["num_comments"].sum())
		post_sent = compute_sentiment_scores((posts_subset["title"] + ". " + posts_subset["selftext"]).tolist()) if not posts_subset.empty else pd.DataFrame()
		post_sentiment = float(post_sent["compound"].mean()) if not post_sent.empty else 0.0

		# Comments
		if not reddit_comments.empty:
			comments_mask = reddit_comments["body"].str.contains("|".join(keywords), case=False, na=False)
			comments_subset = reddit_comments.loc[comments_mask]
			comment_engagement = float(comments_subset["score"].sum())
			comment_sent = compute_sentiment_scores(comments_subset["body"].tolist()) if not comments_subset.empty else pd.DataFrame()
			comment_sentiment = float(comment_sent["compound"].mean()) if not comment_sent.empty else 0.0
		else:
			comment_engagement = 0.0
			comment_sentiment = 0.0

		# YouTube
		if not yt_videos.empty:
			yt_mask = yt_videos["title"].str.contains("|".join(keywords), case=False, na=False) | yt_videos["description"].str.contains("|".join(keywords), case=False, na=False)
			videos_subset = yt_videos.loc[yt_mask]
			stats_subset = yt_stats[yt_stats["video_id"].isin(videos_subset["video_id"])]
			views = float(stats_subset["view_count"].sum())
			likes = float(stats_subset["like_count"].sum())
			comments_count = float(stats_subset["comment_count"].sum())
		else:
			views = likes = comments_count = 0.0

		# Trends
		trend_score = 0.0
		if not trends_df.empty:
			# Average all trend columns that exist for this keyword set
			candidate_cols = [c for c in trends_df.columns if c not in ("date",)]
			if candidate_cols:
				trend_score = float(trends_df[candidate_cols].mean().mean())

		# Combined normalized score (heuristic)
		reddit_engagement = post_engagement + comment_engagement
		youtube_engagement = views * 0.001 + likes * 0.01 + comments_count * 0.1
		engagement = reddit_engagement + youtube_engagement
		sentiment = post_sentiment * 0.6 + comment_sentiment * 0.4
		score = np.tanh(engagement / 10000.0) * 0.6 + ((sentiment + 1) / 2.0) * 0.2 + (trend_score / 100.0) * 0.2
		results.append({
			"place": place,
			"score": float(score),
			"engagement": float(engagement),
			"reddit_engagement": float(reddit_engagement),
			"youtube_engagement": float(youtube_engagement),
			"sentiment": float(sentiment),
			"trend": float(trend_score),
		})

	return pd.DataFrame(results).sort_values("score", ascending=False)


def summarize_for_ppt(result_df: pd.DataFrame) -> Dict[str, str]:
	if result_df.empty:
		return {"headline": "Insufficient data", "support": "Please run the analysis to populate results."}
	best = result_df.iloc[0]
	second = result_df.iloc[1] if len(result_df) > 1 else None
	headline = f"Recommendation: {best['place']} first"
	support = f"Highest composite fit score ({best['score']:.2f}), driven by engagement ({best['engagement']:.0f}) and positive sentiment ({best['sentiment']:.2f})."
	if second is not None:
		support += f" Next best: {second['place']} ({second['score']:.2f})."
	return {"headline": headline, "support": support}


