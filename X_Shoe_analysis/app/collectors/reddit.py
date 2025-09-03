import os
from typing import List, Dict, Any

import pandas as pd
import praw


def _create_reddit_client() -> praw.Reddit:
	client_id = os.getenv("REDDIT_CLIENT_ID")
	client_secret = os.getenv("REDDIT_CLIENT_SECRET")
	user_agent = os.getenv("REDDIT_USER_AGENT", "x-shoe-analysis/0.1")
	if not client_id or not client_secret:
		raise RuntimeError("Missing Reddit API credentials. Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
	return praw.Reddit(
		client_id=client_id,
		client_secret=client_secret,
		user_agent=user_agent,
	)


def fetch_reddit_posts(query_terms: List[str], subreddits: List[str], limit: int = 200) -> pd.DataFrame:
	reddit = _create_reddit_client()
	rows: List[Dict[str, Any]] = []
	query = " OR ".join(query_terms)
	for subreddit in subreddits:
		subreddit_ref = reddit.subreddit(subreddit)
		for post in subreddit_ref.search(query, limit=limit, sort="relevance", time_filter="year"):
			rows.append(
				{
					"id": post.id,
					"subreddit": subreddit,
					"title": post.title or "",
					"selftext": post.selftext or "",
					"score": int(getattr(post, "score", 0) or 0),
					"num_comments": int(getattr(post, "num_comments", 0) or 0),
					"created_utc": int(getattr(post, "created_utc", 0) or 0),
					"url": post.url,
				}
			)
	return pd.DataFrame(rows)


def fetch_reddit_comments(post_ids: List[str], limit_per_post: int = 200) -> pd.DataFrame:
	reddit = _create_reddit_client()
	rows: List[Dict[str, Any]] = []
	for pid in post_ids:
		post = reddit.submission(id=pid)
		post.comments.replace_more(limit=0)
		for i, comment in enumerate(post.comments.list()):
			if i >= limit_per_post:
				break
			rows.append(
				{
					"post_id": pid,
					"comment_id": comment.id,
					"body": getattr(comment, "body", "") or "",
					"score": int(getattr(comment, "score", 0) or 0),
					"created_utc": int(getattr(comment, "created_utc", 0) or 0),
				}
			)
	return pd.DataFrame(rows)


