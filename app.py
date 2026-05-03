import streamlit as st
import pandas as pd
from datetime import datetime
import time
from data_fetcher import (
    get_stock_data, 
    AI_STOCKS, 
    SECTOR_MAP, 
    format_market_cap, 
    format_volume
)
from news_sentiment import (
    get_stock_news,
    get_market_sentiment_summary,
    analyze_sentiment,
    get_mention_counts
)
from alerts import get_alerts, get_volume_status

# Page config
st.set_page_config(
    page_title="AI Backbone Stock Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: #0e1117;
    }
    
    /* Cards styling */
    .stock-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #1e2538 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #2a3040;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stock-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        border-color: #3b82f6;
    }
    
    /* News card */
    .news-card {
        background: #141a26;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border: 1px solid #1f2937;
        border-left: 4px solid;
        transition: background 0.2s;
    }
    .news-card:hover {
        background: #1a2030;
    }
    .news-card.bullish { border-left-color: #22c55e; }
    .news-card.bearish { border-left-color: #ef4444; }
    .news-card.neutral { border-left-color: #eab308; }
    
    .news-title {
        color: #e2e8f0;
        font-size: 0.9em;
        font-weight: 500;
        line-height: 1.4;
    }
    .news-meta {
        color: #6b7280;
        font-size: 0.75em;
        margin-top: 5px;
    }
    .news-source {
        color: #60a5fa;
    }
    
    /* Sentiment badge */
    .sentiment-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.7em;
        font-weight: 600;
    }
    .sentiment-badge.bullish {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .sentiment-badge.bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .sentiment-badge.neutral {
        background: rgba(234, 179, 8, 0.15);
        color: #eab308;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
    
    /* Sentiment meter */
    .sentiment-meter {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #141a26;
        border-radius: 20px;
        padding: 3px;
        border: 1px solid #1f2937;
    }
    .sentiment-bar {
        height: 8px;
        border-radius: 4px;
        transition: width 0.5s;
    }
    
    .ticker {
        color: #60a5fa;
        font-size: 1.4em;
        font-weight: 700;
        letter-spacing: 1px;
    }
    
    .company-name {
        color: #9ca3af;
        font-size: 0.85em;
        margin-top: -5px;
    }
    
    .price {
        font-size: 1.8em;
        font-weight: 700;
        margin: 8px 0;
    }
    .price.up { color: #22c55e; }
    .price.down { color: #ef4444; }
    
    .change {
        font-size: 0.95em;
        font-weight: 500;
    }
    .change.up { color: #22c55e; }
    .change.down { color: #ef4444; }
    
    .section-header {
        color: #f1f5f9;
        font-size: 1.6em;
        font-weight: 700;
        margin: 25px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #2a3040;
    }
    
    .sub-header {
        color: #94a3b8;
        font-size: 0.95em;
        margin-bottom: 20px;
    }
    
    .metric-box {
        background: #141a26;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-label {
        color: #6b7280;
        font-size: 0.75em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        color: #e2e8f0;
        font-size: 1.1em;
        font-weight: 600;
        margin-top: 4px;
    }
    
    .sector-badge {
        display: inline-block;
        background: #1e293b;
        color: #60a5fa;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.7em;
        border: 1px solid #334155;
        margin-top: 5px;
    }
    
    .summary-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 16px;
        padding: 25px;
        border: 1px solid #334155;
    }
    .summary-label {
        color: #64748b;
        font-size: 0.8em;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .summary-value {
        color: #f1f5f9;
        font-size: 2em;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .footer {
        color: #4b5563;
        text-align: center;
        font-size: 0.8em;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #1f2937;
    }
    
    .refresh-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background: #1e293b;
        color: #22c55e;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        border: 1px solid #166534;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    h1, h2, h3 {
        color: #f1f5f9 !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #1a1f2e !important;
        border-radius: 10px !important;
        border: 1px solid #2a3040 !important;
    }
    .streamlit-expanderContent {
        background: #141a26 !important;
        border-radius: 0 0 10px 10px !important;
        border: 1px solid #2a3040 !important;
        border-top: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ---- App Header ----
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h1 style='margin-bottom:0;'>🤖 AI Backbone Stocks</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;margin-top:0;'>The companies powering the Artificial Intelligence revolution</p>", unsafe_allow_html=True)
with col2:
    st.markdown(
        f"<div style='text-align:right;padding-top:15px;'>"
        f"<span class='refresh-badge'>🟢 Live • {datetime.now().strftime('%H:%M:%S')}</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# ---- Sidebar ----
with st.sidebar:
    st.markdown("### ⚙️ Dashboard Controls")
    st.markdown("---")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    # Sector filter
    st.markdown("### 🔍 Filter by Sector")
    sectors = ["All Sectors"] + list(SECTOR_MAP.keys())
    selected_sector = st.selectbox("Select sector", sectors, label_visibility="collapsed")
    
    # Performance filter
    st.markdown("### 📊 Performance Filter")
    perf_filter = st.selectbox(
        "Show stocks that are:",
        ["All", "Gaining 📈", "Declining 📉", "Top 5 Gainers", "Top 5 Losers"],
        label_visibility="collapsed"
    )
    
    # News toggle
    st.markdown("### 📰 News Settings")
    show_news = st.checkbox("Show news & sentiment", value=True)
    
    st.markdown("---")
    st.markdown("### 💡 About")
    st.markdown(
        """
        This dashboard tracks **AI backbone companies** - 
        the critical infrastructure powering the AI revolution.
        
        **Sectors tracked:**
        - 🖥️ Chip Design
        - 🏭 Semiconductor Manufacturing
        - 🔧 Equipment & Memory
        - 🌐 AI Infrastructure
        - 📊 AI Software & Platforms
        
        **Features:**
        - 📈 Real-time stock data
        - 📰 News & sentiment analysis
        - 🏆 Gainers & Losers
        - 📊 Sector performance
        """
    )

# ---- Fetch Data ----
with st.spinner("📡 Fetching live market data & news..."):
    data = get_stock_data()
    
    # Fetch news for each stock if enabled
    all_news = []
    stock_news_cache = {}
    if show_news:
        progress_bar = st.progress(0)
        tickers = list(data.keys())
        for idx, ticker in enumerate(tickers):
            news = get_stock_news(ticker, data[ticker]["name"])
            stock_news_cache[ticker] = news
            all_news.extend(news)
            progress_bar.progress((idx + 1) / len(tickers))
        progress_bar.empty()
    
    sentiment_summary = get_market_sentiment_summary(all_news)
    
    # Fetch alerts
    alerts_data = get_alerts(list(data.keys()))
    total_alerts = sum(len(a) for a in alerts_data.values())
    time.sleep(0.3)

# ---- Apply Filters ----
filtered_tickers = list(data.keys())

# Sector filter
if selected_sector != "All Sectors":
    sector_stocks = SECTOR_MAP.get(selected_sector, [])
    filtered_tickers = [t for t in filtered_tickers if t in sector_stocks]

# Performance filter
if perf_filter == "Gaining 📈":
    filtered_tickers = [t for t in filtered_tickers if data[t]["direction"] == "up"]
elif perf_filter == "Declining 📉":
    filtered_tickers = [t for t in filtered_tickers if data[t]["direction"] == "down"]
elif perf_filter == "Top 5 Gainers":
    sorted_stocks = sorted(filtered_tickers, key=lambda t: data[t]["change_pct"], reverse=True)
    filtered_tickers = sorted_stocks[:5]
elif perf_filter == "Top 5 Losers":
    sorted_stocks = sorted(filtered_tickers, key=lambda t: data[t]["change_pct"])
    filtered_tickers = sorted_stocks[:5]

# ---- NEWS & SENTIMENT OVERVIEW (Top Section) ----
if show_news and all_news:
    st.markdown("<div class='section-header'>📰 Market Sentiment & News</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sentiment_color = "#22c55e" if sentiment_summary["overall"] == "Bullish" else ("#ef4444" if sentiment_summary["overall"] == "Bearish" else "#eab308")
        st.markdown(
            f"<div class='summary-card'>"
            f"<div class='summary-label'>Market Sentiment</div>"
            f"<div class='summary-value' style='color:{sentiment_color}'>{sentiment_summary['emoji']} {sentiment_summary['overall']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"<div class='summary-card'>"
            f"<div class='summary-label'>Bullish Articles</div>"
            f"<div class='summary-value' style='color:#22c55e;'>{sentiment_summary['bullish_pct']:.0f}%</div>"
            f"<div style='margin-top:5px;background:#1f2937;border-radius:10px;height:6px;'>"
            f"<div style='width:{sentiment_summary['bullish_pct']}%;height:6px;background:#22c55e;border-radius:10px;'></div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col3:
        st.markdown(
            f"<div class='summary-card'>"
            f"<div class='summary-label'>Bearish Articles</div>"
            f"<div class='summary-value' style='color:#ef4444;'>{sentiment_summary['bearish_pct']:.0f}%</div>"
            f"<div style='margin-top:5px;background:#1f2937;border-radius:10px;height:6px;'>"
            f"<div style='width:{sentiment_summary['bearish_pct']}%;height:6px;background:#ef4444;border-radius:10px;'></div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col4:
        st.markdown(
            f"<div class='summary-card'>"
            f"<div class='summary-label'>Total Articles</div>"
            f"<div class='summary-value'>{sentiment_summary['total']}</div>"
            f"<div class='summary-label' style='margin-top:5px;'>{len(all_news)} stocks covered</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # Sentiment breakdown bar
    bullish_pct = sentiment_summary["bullish_pct"]
    bearish_pct = sentiment_summary["bearish_pct"]
    neutral_pct = 100 - bullish_pct - bearish_pct
    st.markdown(
        f"<div style='margin-top:10px;background:#1f2937;border-radius:10px;height:10px;display:flex;overflow:hidden;'>"
        f"<div style='width:{max(bullish_pct, 1)}%;height:10px;background:#22c55e;border-radius:10px 0 0 10px;'></div>"
        f"<div style='width:{max(neutral_pct, 1)}%;height:10px;background:#eab308;'></div>"
        f"<div style='width:{max(bearish_pct, 1)}%;height:10px;background:#ef4444;border-radius:0 10px 10px 0;'></div>"
        f"</div>"
        f"<div style='display:flex;justify-content:space-between;color:#6b7280;font-size:0.75em;margin-top:3px;'>"
        f"<span>🟢 Bullish {bullish_pct:.0f}%</span>"
        f"<span>🟡 Neutral {neutral_pct:.0f}%</span>"
        f"<span>🔴 Bearish {bearish_pct:.0f}%</span>"
        f"</div>",
        unsafe_allow_html=True
    )

# ---- MARKET OVERVIEW ----
st.markdown("<div class='section-header'>📈 Market Overview</div>", unsafe_allow_html=True)

# Calculate summary stats
total_market_cap = sum(data[t]["market_cap"] for t in data if data[t]["market_cap"])
avg_change = sum(data[t]["change_pct"] for t in data) / len(data) if data else 0
gainers = sum(1 for t in data if data[t]["direction"] == "up")
decliners = sum(1 for t in data if data[t]["direction"] == "down")
avg_pe = sum(data[t]["pe_ratio"] for t in data if data[t]["pe_ratio"]) / sum(1 for t in data if data[t]["pe_ratio"]) if data else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(
        f"<div class='summary-card'>"
        f"<div class='summary-label'>Total Market Cap</div>"
        f"<div class='summary-value'>{format_market_cap(total_market_cap)}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
with col2:
    st.markdown(
        f"<div class='summary-card'>"
        f"<div class='summary-label'>Avg Change</div>"
        f"<div class='summary-value' style='color:{'#22c55e' if avg_change >= 0 else '#ef4444'}'>{avg_change:+.2f}%</div>"
        f"</div>",
        unsafe_allow_html=True
    )
with col3:
    st.markdown(
        f"<div class='summary-card'>"
        f"<div class='summary-label'>Gainers / Decliners</div>"
        f"<div class='summary-value'><span style='color:#22c55e;'>{gainers}</span> / <span style='color:#ef4444;'>{decliners}</span></div>"
        f"</div>",
        unsafe_allow_html=True
    )
with col4:
    st.markdown(
        f"<div class='summary-card'>"
        f"<div class='summary-label'>Avg P/E Ratio</div>"
        f"<div class='summary-value'>{avg_pe:.1f}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
with col5:
    st.markdown(
        f"<div class='summary-card'>"
        f"<div class='summary-label'>Stocks Tracked</div>"
        f"<div class='summary-value'>{len(data)}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

# ---- STOCK CARDS WITH NEWS (Grid Layout) ----
# ---- ALERTS PANEL ----
if show_news and 'alerts_data' in dir() and alerts_data:
    alert_count = sum(len(a) for a in alerts_data.values())
    if alert_count > 0:
        st.markdown("<div class='section-header'>🔔 Live Alerts</div>", unsafe_allow_html=True)
        
        # Count by severity
        high = sum(1 for alerts in alerts_data.values() for a in alerts if a['severity'] == 'high')
        medium = sum(1 for alerts in alerts_data.values() for a in alerts if a['severity'] == 'medium')
        
        st.markdown(f"<div style='color:#94a3b8;margin-bottom:15px;'>{alert_count} alerts • {'🔴' if high else ''} {high} high • {'🟡' if medium else ''} {medium} medium</div>", unsafe_allow_html=True)
        
        # Show alerts in expandable sections by ticker
        for ticker, alerts in sorted(alerts_data.items()):
            if not alerts:
                continue
            name = data.get(ticker, {}).get('name', ticker)
            with st.expander(f"🚨 {ticker} - {name} ({len(alerts)} alerts)"):
                for alert in alerts:
                    severity_color = "#ef4444" if alert['severity'] == 'high' else "#eab308" if alert['severity'] == 'medium' else "#6b7280"
                    st.markdown(
                        f"<div style='background:#141a26;padding:12px 15px;border-radius:8px;margin:5px 0;border-left:4px solid {severity_color};'>"
                        f"<div style='color:#e2e8f0;font-weight:500;'>{alert['message']}</div>"
                        f"<div style='color:#6b7280;font-size:0.8em;margin-top:3px;'>{alert['detail']} • {alert['time']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

st.markdown("<div class='section-header'>🏢 Stock Details</div>" , unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Showing {len(filtered_tickers)} of {len(data)} stocks</div>", unsafe_allow_html=True)

# Display in rows of 3
for i in range(0, len(filtered_tickers), 3):
    cols = st.columns(3)
    for j, ticker in enumerate(filtered_tickers[i:i+3]):
        stock = data[ticker]
        with cols[j]:
            direction_class = stock["direction"]
            arrow = "▲" if stock["direction"] == "up" else "▼"
            
            # News for this stock
            stock_news = stock_news_cache.get(ticker, [])
            
            st.markdown(
                f"""
                <div class='stock-card'>
                    <div style='display:flex;justify-content:space-between;align-items:start;'>
                        <div>
                            <div class='ticker'>{ticker}</div>
                            <div class='company-name'>{stock['name']}</div>
                            <span class='sector-badge'>{stock['sector']}</span>
                        </div>
                        <div style='text-align:right;'>
                            <div class='price {direction_class}'>${stock['price']:,.2f}</div>
                            <div class='change {direction_class}'>{arrow} {stock['change']:+.2f} ({stock['change_pct']:+.2f}%)</div>
                        </div>
                    </div>
                    <div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:15px;padding-top:15px;border-top:1px solid #1f2937;'>
                        <div class='metric-box'>
                            <div class='metric-label'>Volume</div>
                            <div class='metric-value'>{format_volume(stock['volume'])}</div>
                        </div>
                        <div class='metric-box'>
                            <div class='metric-label'>Market Cap</div>
                            <div class='metric-value'>{format_market_cap(stock['market_cap'])}</div>
                        </div>
                        <div class='metric-box'>
                            <div class='metric-label'>P/E</div>
                            <div class='metric-value'>{f"{stock['pe_ratio']:.1f}" if stock['pe_ratio'] else 'N/A'}</div>
                        </div>
                    </div>
                    {"".join(getattr(st, 'empty', lambda: None)() for _ in range(0))}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # News expander for this stock
            if show_news and stock_news:
                with st.expander(f"📰 News & Sentiment ({len(stock_news)} articles)"):
                    for article in stock_news:
                        sentiment_class = article["sentiment_label"].lower()
                        st.markdown(
                            f"<div class='news-card {sentiment_class}'>"
                            f"<div class='news-title'><a href=\"{article['url']}\" target=\"_blank\" style='color:#e2e8f0;text-decoration:none;' onmouseover=\"this.style.color='#60a5fa'\" onmouseout=\"this.style.color='#e2e8f0'\">{article['title']}</a></div>"
                            f"<div class='news-meta'>"
                            f"<span class='news-source'>{article['source']}</span> • "
                            f"{article['published']} • "
                            f"<span class='sentiment-badge {sentiment_class}'>{article['sentiment_emoji']} {article['sentiment_label']}</span>"
                            f"</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

# ---- SECTOR BREAKDOWN ----
st.markdown("<div class='section-header'>📊 Sector Performance</div>", unsafe_allow_html=True)

sector_data = []
for sector, tickers in SECTOR_MAP.items():
    sector_stocks = [data[t] for t in tickers if t in data]
    if sector_stocks:
        avg_sector_change = sum(s["change_pct"] for s in sector_stocks) / len(sector_stocks)
        sector_market_cap = sum(s["market_cap"] for s in sector_stocks)
        sector_data.append({
            "Sector": sector,
            "Stocks": len(sector_stocks),
            "Avg Change %": f"{avg_sector_change:+.2f}%",
            "Total Market Cap": format_market_cap(sector_market_cap),
            "Direction": "📈" if avg_sector_change >= 0 else "📉"
        })

if sector_data:
    df = pd.DataFrame(sector_data)
    st.dataframe(
        df,
        column_config={
            "Sector": st.column_config.TextColumn("Sector"),
            "Stocks": st.column_config.NumberColumn("Stocks"),
            "Avg Change %": st.column_config.TextColumn("Avg Change %"),
            "Total Market Cap": st.column_config.TextColumn("Total Market Cap"),
            "Direction": st.column_config.TextColumn("Status"),
        },
        hide_index=True,
        use_container_width=True
    )

# ---- RANKINGS ----
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='section-header' style='font-size:1.3em;'>🏆 Top 5 Gainers</div>", unsafe_allow_html=True)
    sorted_gainers = sorted(data.values(), key=lambda x: x["change_pct"], reverse=True)[:5]
    for i, stock in enumerate(sorted_gainers):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
        st.markdown(
            f"<div style='background:#141a26;padding:10px 15px;border-radius:8px;margin:5px 0;border:1px solid #1f2937;'>"
            f"<span style='font-size:1.2em;'>{medal}</span> "
            f"<strong style='color:#60a5fa;'>{stock['name']}</strong> "
            f"<span style='color:#22c55e;float:right;'>+{stock['change_pct']:.2f}% (${stock['price']:.2f})</span>"
            f"</div>",
            unsafe_allow_html=True
        )

with col2:
    st.markdown("<div class='section-header' style='font-size:1.3em;'>📉 Top 5 Losers</div>", unsafe_allow_html=True)
    sorted_losers = sorted(data.values(), key=lambda x: x["change_pct"])[:5]
    for i, stock in enumerate(sorted_losers):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
        st.markdown(
            f"<div style='background:#141a26;padding:10px 15px;border-radius:8px;margin:5px 0;border:1px solid #1f2937;'>"
            f"<span style='font-size:1.2em;'>{medal}</span> "
            f"<strong style='color:#60a5fa;'>{stock['name']}</strong> "
            f"<span style='color:#ef4444;float:right;'>{stock['change_pct']:.2f}% (${stock['price']:.2f})</span>"
            f"</div>",
            unsafe_allow_html=True
        )

# ---- LATEST SENTIMENT NEWS FEED ----
if show_news and all_news:
    st.markdown("<div class='section-header'>📰 Latest Market News</div>", unsafe_allow_html=True)
    
    # Show top 10 most recent/relevant news across all stocks
    top_news = sorted(all_news, key=lambda x: x.get("published", ""), reverse=True)[:10]
    
    for article in top_news:
        sentiment_class = article["sentiment_label"].lower()
        st.markdown(
            f"<div class='news-card {sentiment_class}'>"
            f"<div class='news-title'><a href=\"{article['url']}\" target=\"_blank\" style='color:#e2e8f0;text-decoration:none;' onmouseover=\"this.style.color='#60a5fa'\" onmouseout=\"this.style.color='#e2e8f0'\">{article['title']}</a></div>"
            f"<div class='news-meta'>"
            f"<span class='news-source'>{article['source']}</span> • "
            f"{article['published']} • "
            f"<span class='sentiment-badge {sentiment_class}'>{article['sentiment_emoji']} {article['sentiment_label']}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )

# ---- Footer ----
st.markdown("<div class='footer'>🤖 AI Backbone Stock Dashboard • Data: Yahoo Finance • News: NewsAPI/Google News • Sentiment: TextBlob</div>", unsafe_allow_html=True)

# ---- Auto-Refresh Logic ----
if auto_refresh:
    st.toast("🔄 Auto-refresh enabled - updating every 30 seconds")
    time.sleep(30)
    st.rerun()
