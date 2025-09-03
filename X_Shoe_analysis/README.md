X Shoe Store – Chennai Entry Analysis

Run locally (VS Code or terminal):

1) Create a virtual environment and install dependencies
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2) Set environment variables (Windows PowerShell examples)
```
$env:YOUTUBE_API_KEY="YOUR_YOUTUBE_API_KEY"
$env:REDDIT_CLIENT_ID="YOUR_REDDIT_CLIENT_ID"
$env:REDDIT_CLIENT_SECRET="YOUR_REDDIT_CLIENT_SECRET"
$env:REDDIT_USER_AGENT="x-shoe-analysis/0.1"
```

3) Run Streamlit app
```
streamlit run app/streamlit_app.py
```

What it does
- Collects Reddit, YouTube, and Google Trends signals for sneaker/streetwear interest in Chennai
- Compares composite score for Malls vs High Streets
- Visualizes scores and components; surfaces one sharp insight and launch suggestions


