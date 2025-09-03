import os
from typing import List, Dict, Any

import pandas as pd
from googleapiclient.discovery import build


def _create_youtube_client():
	api_key = os.getenv("YOUTUBE_API_KEY")
	if not api_key:
		raise RuntimeError("Missing YouTube API key. Set YOUTUBE_API_KEY in environment.")
	return build("youtube", "v3", developerKey=api_key)


def search_youtube_videos(query: str, max_results: int = 50) -> pd.DataFrame:
	yt = _create_youtube_client()
	search_response = (
		yt.search()
		.list(q=query, part="id,snippet", type="video", maxResults=min(max_results, 50))
		.execute()
	)
	items = search_response.get("items", [])
	rows: List[Dict[str, Any]] = []
	for it in items:
		video_id = it["id"]["videoId"]
		snippet = it.get("snippet", {})
		rows.append(
			{
				"video_id": video_id,
				"title": snippet.get("title", ""),
				"description": snippet.get("description", ""),
				"channel": snippet.get("channelTitle", ""),
				"published_at": snippet.get("publishedAt", ""),
			}
		)
	return pd.DataFrame(rows)


def fetch_video_stats(video_ids: List[str]) -> pd.DataFrame:
	yt = _create_youtube_client()
	if not video_ids:
		return pd.DataFrame()
	resp = yt.videos().list(part="statistics", id=",".join(video_ids[:50])).execute()
	rows: List[Dict[str, Any]] = []
	for it in resp.get("items", []):
		stats = it.get("statistics", {})
		rows.append(
			{
				"video_id": it["id"],
				"view_count": int(stats.get("viewCount", 0) or 0),
				"like_count": int(stats.get("likeCount", 0) or 0),
				"comment_count": int(stats.get("commentCount", 0) or 0),
			}
		)
	return pd.DataFrame(rows)


