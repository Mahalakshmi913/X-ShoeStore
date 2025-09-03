import pandas as pd
import plotly.express as px
import plotly.io as pio


def bar_scores(df: pd.DataFrame):
	if df.empty:
		return None
	return px.bar(df, x="place", y="score", title="Location Fit Scores")


def radar_components(df: pd.DataFrame):
	if df.empty:
		return None
	sub = df.melt(id_vars=["place"], value_vars=["engagement", "sentiment", "trend"], var_name="metric", value_name="value")
	fig = px.line_polar(sub, r="value", theta="metric", color="place", line_close=True, title="Signal Components by Location")
	fig.update_traces(fill="toself")
	return fig


def bar_components(df: pd.DataFrame):
	if df.empty:
		return None
	sub = df.melt(id_vars=["place"], value_vars=["engagement", "sentiment", "trend"], var_name="metric", value_name="value")
	return px.bar(sub, x="metric", y="value", color="place", barmode="group", title="Signal Components (Bar)")


def donut_components(df: pd.DataFrame):
	if df.empty:
		return None
	# Share of each component within each place
	rows = []
	for _, row in df.iterrows():
		total = float(row["engagement"] + row["sentiment"] + row["trend"]) or 1.0
		for metric in ["engagement", "sentiment", "trend"]:
			rows.append({"place": row["place"], "metric": metric, "share": float(row[metric]) / total})
	sub = pd.DataFrame(rows)
	fig = px.pie(sub, names="metric", values="share", facet_col="place", hole=0.6, title="Signal Components Share (Donut)")
	return fig


def stacked_engagement(df: pd.DataFrame):
	if df.empty:
		return None
	# Stacked bar of Reddit vs YouTube engagement by place
	sub = df.melt(id_vars=["place"], value_vars=["reddit_engagement", "youtube_engagement"], var_name="source", value_name="value")
	return px.bar(sub, x="place", y="value", color="source", barmode="stack", title="Engagement Sources by Location")


def sentiment_density(df: pd.DataFrame):
	if df.empty:
		return None
	# Sentiment distribution proxy (bar per place). If more granular data available, this can be a KDE.
	return px.bar(df, x="place", y="sentiment", title="Average Sentiment by Location", range_y=[-1, 1])


def save_fig(fig, path: str):
	if fig is None:
		return
	pio.write_image(fig, path, scale=2, width=1200, height=700)


