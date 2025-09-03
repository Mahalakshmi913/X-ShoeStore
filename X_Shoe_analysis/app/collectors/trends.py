from typing import List

import pandas as pd
from pytrends.request import TrendReq


def _batch_list(items: List[str], batch_size: int = 5) -> List[List[str]]:
	return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def fetch_trends(queries: List[str], geo: str = "IN-TN", timeframe: str = "today 12-m") -> pd.DataFrame:
	# Pytrends supports up to 5 keywords per request
	batches = _batch_list(queries, 5) if queries else []
	pytrends = TrendReq(hl="en-US", tz=330)
	combined: pd.DataFrame | None = None
	for batch in batches:
		try:
			pytrends.build_payload(kw_list=batch, timeframe=timeframe, geo=geo)
			interest = pytrends.interest_over_time()
		except Exception:
			# Fallback: try wider geo if regional code fails
			try:
				pytrends.build_payload(kw_list=batch, timeframe=timeframe, geo="IN")
				interest = pytrends.interest_over_time()
			except Exception:
				interest = None
		if interest is None or interest.empty:
			continue
		interest = interest.reset_index().rename(columns={"date": "date"})
		# Drop isPartial if present to avoid duplicates on merge
		if "isPartial" in interest.columns:
			interest = interest.drop(columns=["isPartial"])  # type: ignore
		combined = interest if combined is None else pd.merge(combined, interest, on="date", how="outer")
	if combined is None:
		return pd.DataFrame()
	combined = combined.sort_values("date").reset_index(drop=True)
	return combined


