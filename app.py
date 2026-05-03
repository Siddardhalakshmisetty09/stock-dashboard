import streamlit as st
import pandas as pd
from datetime import datetime
import time
from data_fetcher import (
    get_stock_data, 
    ALL_STOCKS, 
    SECTOR_ANALYSIS, 
    STOCK_SECTOR_MAP,
    SECTOR_DISPLAY,
    format_market_cap, 
    format_volume,
    analyze_sectors,
    get_sectors_list,
    get_stocks_for_sector,
    get_sector_emoji
)
from news_sentiment import (
    get_stock_news,
    get_market_sentiment_summary,
    analyze_sentiment,
    get_mention_counts
)
from alerts import get_alerts, get_volume_status, get_market_status
from economics import get_economic_events, get_event_color
from correlations import get_correlations, get_stock_summary, search_stocks, get_sector_context

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="GGP - God Given Patterns",
    page_icon="🪐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get market status early
mkt_status = get_market_status()

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: #080b12; }
    
    /* HEADER */
    .ggp-header {
        background: linear-gradient(135deg, #0f1320 0%, #141a2e 100%);
        border-radius: 16px;
        padding: 15px 25px;
        margin-bottom: 15px;
        border: 1px solid #1f2940;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .ggp-logo {
        font-size: 1.5em;
        font-weight: 700;
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .ggp-logo span { font-size: 1.8em; -webkit-text-fill-color: initial; }
    .ggp-tagline {
        color: #64748b;
        font-size: 0.75em;
        letter-spacing: 3px;
        text-transform: uppercase;
        margin-top: -2px;
    }
    
    /* SEARCH */
    .search-container {
        position: relative;
        width: 100%;
        max-width: 400px;
    }
    .search-input {
        width: 100%;
        padding: 10px 15px 10px 40px;
        background: #1a1f30;
        border: 1px solid #2a3045;
        border-radius: 30px;
        color: #e2e8f0;
        font-size: 0.9em;
        outline: none;
        transition: border-color 0.2s;
    }
    .search-input:focus { border-color: #818cf8; }
    .search-icon {
        position: absolute;
        left: 14px;
        top: 50%;
        transform: translateY(-50%);
        color: #64748b;
        font-size: 1em;
    }
    
    /* SEARCH RESULTS */
    .search-result {
        background: #1a1f30;
        border: 1px solid #2a3045;
        border-radius: 12px;
        padding: 12px 15px;
        margin: 3px 0;
        cursor: pointer;
        transition: background 0.2s;
    }
    .search-result:hover { background: #222840; border-color: #818cf8; }
    .search-ticker {
        color: #818cf8;
        font-weight: 700;
        font-size: 1.1em;
    }
    .search-name {
        color: #94a3b8;
        font-size: 0.8em;
        margin-left: 8px;
    }
    .search-desc {
        color: #cbd5e1;
        font-size: 0.8em;
        margin-top: 3px;
    }
    .search-meta {
        color: #64748b;
        font-size: 0.7em;
        margin-top: 2px;
    }
    
    /* HOT SECTOR */
    .hot-hero {
        background: linear-gradient(135deg, #0f1320 0%, #141a2e 100%);
        border-radius: 20px;
        padding: 30px;
        margin: 15px 0;
        border: 2px solid;
        position: relative;
        overflow: hidden;
    }
    .hot-label {
        display: inline-block;
        background: linear-gradient(135deg, #ef4444, #f97316);
        color: white;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 0.75em;
        font-weight: 600;
        letter-spacing: 1px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
        70% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    }
    
    /* SECTOR CARDS */
    .sector-grid {
        display: flex;
        gap: 10px;
        overflow-x: auto;
        padding: 5px 0 15px 0;
        margin: 15px 0;
    }
    .sector-card {
        min-width: 120px;
        background: #141a28;
        border-radius: 14px;
        padding: 15px 12px;
        text-align: center;
        border: 1px solid #1f2940;
        transition: all 0.2s;
        cursor: pointer;
        flex-shrink: 0;
    }
    .sector-card:hover {
        transform: translateY(-3px);
        border-color: #818cf8;
        background: #1a2035;
    }
    .sector-card.hot {
        border: 2px solid #ef4444;
        animation: glow 1.5s infinite;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); }
        50% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.5); }
        100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); }
    }
    .sector-card.selected {
        border-color: #818cf8;
        background: #1a2035;
    }
    
    /* STOCK CARDS */
    .stock-card {
        background: linear-gradient(135deg, #141a28 0%, #181e30 100%);
        border-radius: 14px;
        padding: 18px;
        margin: 8px 0;
        border: 1px solid #1f2940;
        transition: all 0.2s;
    }
    .stock-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        border-color: #818cf8;
    }
    
    /* EVENTS */
    .event-card {
        background: #141a28;
        border-radius: 12px;
        padding: 15px;
        margin: 8px 0;
        border: 1px solid #1f2940;
        border-left: 4px solid;
    }
    .event-card:hover { background: #1a2035; }
    
    /* CORRELATION BADGE */
    .corr-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(129, 140, 248, 0.1);
        color: #818cf8;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.7em;
        border: 1px solid rgba(129, 140, 248, 0.2);
    }
    
    /* SECTION HEADERS */
    .section-header {
        color: #f1f5f9;
        font-size: 1.4em;
        font-weight: 700;
        margin: 25px 0 10px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #1f2940;
    }
    .sub-header { color: #64748b; font-size: 0.85em; margin-bottom: 15px; }
    
    /* MARKET STATUS */
    .mkt-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 500;
    }
    
    /* SCROLL CONTAINER */
    .scroll-x {
        overflow-x: auto;
        display: flex;
        gap: 12px;
        padding: 5px 0 10px 0;
        scrollbar-width: thin;
        scrollbar-color: #1f2940 transparent;
    }
    .scroll-x::-webkit-scrollbar { height: 4px; }
    .scroll-x::-webkit-scrollbar-thumb { background: #1f2940; border-radius: 2px; }
    
    /* NEWS */
    .news-card {
        background: #141a28;
        border-radius: 10px;
        padding: 12px 15px;
        margin: 6px 0;
        border: 1px solid #1f2940;
        border-left: 4px solid;
    }
    .news-card:hover { background: #1a2035; }
    
    /* GENERAL */
    .footer {
        color: #334155;
        text-align: center;
        font-size: 0.75em;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #1a1f30;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* SECTOR CONTEXT */
    .sector-context {
        background: linear-gradient(135deg, #0f1320, #141a28);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid #1f2940;
    }
    .driver-item {
        padding: 8px 12px;
        margin: 4px 0;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER WITH SEARCH
# ============================================================
col_logo, col_search, col_status = st.columns([1, 2, 1])

with col_logo:
    st.markdown(
        f"""
        <div>
            <div class='ggp-logo'><span>🪐</span> GGP</div>
            <div class='ggp-tagline'>GOD GIVEN PATTERNS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_search:
    # Search bar
    search_query = st.text_input("", placeholder="🔍  Search any stock (NVDA, AMD, Gold...)", label_visibility="collapsed", key="search")
    
    # Search results
    if search_query and len(search_query) >= 1:
        # Fetch data if not already fetched
        if 'data' not in st.session_state:
            st.session_state.search_data = get_stock_data()
        search_data = st.session_state.get('search_data', {})
        results = search_stocks(search_query, data=search_data)
        
        if results:
            for r in results[:8]:
                direction = "up" if r["change_pct"] >= 0 else "down"
                arrow = "▲" if direction == "up" else "▼"
                color = "#22c55e" if direction == "up" else "#ef4444"
                st.markdown(
                    f"<div class='search-result'>"
                    f"<div><span class='search-ticker'>{r['ticker']}</span>"
                    f"<span class='search-name'>{r['name'][:35]}</span>"
                    f"<span style='float:right;color:{color};font-weight:600;'>${r['price']:,.2f} {arrow} {r['change_pct']:+.2f}%</span></div>"
                    f"<div class='search-desc'>{r['description']}</div>"
                    f"<div class='search-meta'>📊 Avg Vol: {r['volume_str']}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("<div style='color:#64748b;text-align:center;padding:15px;'>No results found. Try a different ticker.</div>", unsafe_allow_html=True)

with col_status:
    status_icon = "🟢" if mkt_status["status"] == "open" else "🔴"
    # Show selected market session in badge
    session_display = market_session if 'market_session' in dir() else mkt_status['session']
    st.markdown(
        f"<div style='text-align:right;'>"
        f"<div class='mkt-badge' style='background:{'rgba(34,197,94,0.1)' if mkt_status['status']=='open' else 'rgba(239,68,68,0.1)'};color:{mkt_status['color']};border:1px solid {mkt_status['color']}40;'>"
        f"{status_icon} {mkt_status['label']} • {session_display}"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Controls")
    st.markdown("---")
    
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
    
    st.markdown("### 🔍 Filter by Sector")
    sectors_list = ["All Sectors"] + get_sectors_list()
    selected_sector = st.selectbox("Select sector", sectors_list, label_visibility="collapsed", key="sector_select")
    
    st.markdown("### 📊 Performance Filter")
    perf_filter = st.selectbox(
        "Show:",
        ["All", "Gaining 📈", "Declining 📉", "Top 5 Gainers", "Top 5 Losers"],
        label_visibility="collapsed"
    )
    
    st.markdown("### 📰 Show News")
    show_news = st.checkbox("News & Sentiment", value=True)
    show_events = st.checkbox("📅 Economic Events", value=True)
    
    st.markdown("### 🕐 Market Session")
    market_session = st.selectbox(
        "Show data for:",
        ["Regular Hours", "Pre-Market", "After-Hours"],
        label_visibility="collapsed"
    )
    # Update market status to include session
    if market_session != "Regular Hours":
        mkt_status["session"] = market_session
    
    st.markdown("---")
    st.markdown("### 💡 About")
    st.markdown("""
    **GGP - God Given Patterns** 🪐
    
    Your edge in the markets:
    - 🔥 Hot sector spotlight
    - 📰 Real-time news & sentiment
    - 🔔 Volume & price alerts
    - 📅 Economic event calendar
    - 🤝 Stock correlation engine
    
    **7 Sectors Tracked:**
    - 🤖 AI/Backbone (15 stocks)
    - 🥇 Gold & Precious Metals (10)
    - 🔬 Quantum Computing (10)
    - 📈 FANGMAN+ (8 mega-caps)
    - 🖥️ Semiconductors (15)
    - 🟢 Copper & Miners (10)
    - 🏦 Financials / XLF (15)
    """)

# ============================================================
# FETCH DATA
# ============================================================
# Fast loading with caching
if "cached_data" in st.session_state and "cached_time" in st.session_state:
    cache_age = (datetime.now() - st.session_state.cached_time).seconds
    if cache_age < 60:  # 1 min cache
        data = st.session_state.cached_data
    else:
        cache_age = 999  # Force refresh
else:
    cache_age = 999

if cache_age > 60:
    with st.spinner("🪐 Loading market data..."):
        data = get_stock_data()
        st.session_state.cached_data = data
        st.session_state.cached_time = datetime.now()
else:
    data = st.session_state.cached_data

st.session_state.search_data = data

# Only fetch news if needed
all_news = []
stock_news_cache = {}
if show_news:
    # Check if news is cached
    if "cached_news" in st.session_state:
        all_news, stock_news_cache = st.session_state.cached_news
    else:
        tickers = list(data.keys())[:15]  # Limit for speed
        for idx, ticker in enumerate(tickers):
            news = get_stock_news(ticker, data[ticker]["name"])
            stock_news_cache[ticker] = news
            all_news.extend(news)
        st.session_state.cached_news = (all_news, stock_news_cache)
    stock_news_cache = {}
    if show_news:
        progress_bar = st.progress(0)
        tickers = list(data.keys())[:20]  # Limit to first 20 to avoid rate limits
        for idx, ticker in enumerate(tickers):
            news = get_stock_news(ticker, data[ticker]["name"])
            stock_news_cache[ticker] = news
            all_news.extend(news)
            progress_bar.progress((idx + 1) / len(tickers))
        progress_bar.empty()
    
    sentiment_summary = get_market_sentiment_summary(all_news)
    
    # Fetch alerts
    alerts_data = get_alerts(list(data.keys()))
    mkt_status = get_market_status()
    
    # Get economic events
    if show_events:
        economic_events = get_economic_events(days_ahead=7)
    
    time.sleep(0.2)

# ============================================================
# APPLY FILTERS
# ============================================================
filtered_tickers = list(data.keys())

if selected_sector != "All Sectors":
    sector_stocks = get_stocks_for_sector(selected_sector)
    filtered_tickers = [t for t in filtered_tickers if t in sector_stocks]

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

# ============================================================
# HOT SECTOR SPOTLIGHT
# ============================================================
hot_sector, sector_perf = analyze_sectors(data)

if hot_sector and hot_sector in sector_perf:
    hot = sector_perf[hot_sector]
    
    st.markdown("<div class='section-header'>🔥 Hot Sector Spotlight</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2.5, 1])
    with col1:
        st.markdown(
            f"<div class='hot-hero' style='border-color:{hot['color']}30;'>"
            f"<span class='hot-label'>🔥 HOT SECTOR</span>"
            f"<div style='font-size:2em;font-weight:800;margin:10px 0 5px 0;color:{hot['color']};'>{hot['emoji']} {hot_sector}</div>"
            f"<div style='color:#94a3b8;font-size:0.9em;margin:5px 0 10px 0;'>{hot['description'][:150]}...</div>"
            f"<div style='background:rgba(0,0,0,0.3);border-radius:10px;padding:15px;border-left:3px solid {hot['color']};'>"
            f"<strong style='color:#f1f5f9;'>🔥 Why it's hot:</strong> "
            f"<span style='color:#cbd5e1;'>{hot['why_hot']}</span></div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f"<div style='background:#141a28;border-radius:16px;padding:20px;border:1px solid #1f2940;height:100%;'>"
            f"<div style='text-align:center;padding:10px;background:rgba(0,0,0,0.2);border-radius:10px;'>"
            f"<div style='color:#64748b;font-size:0.7em;text-transform:uppercase;letter-spacing:1px;'>Avg Change</div>"
            f"<div style='font-size:2em;font-weight:700;color:{'#22c55e' if hot['avg_change'] >= 0 else '#ef4444'};'>{hot['avg_change']:+.2f}%</div></div>"
            f"<div style='display:flex;gap:10px;margin-top:10px;'>"
            f"<div style='flex:1;text-align:center;padding:10px;background:rgba(0,0,0,0.2);border-radius:10px;'>"
            f"<div style='color:#64748b;font-size:0.65em;text-transform:uppercase;'>Gainers</div>"
            f"<div style='font-size:1.3em;font-weight:700;color:#22c55e;'>{hot['gainers']}/{hot['total']}</div></div>"
            f"<div style='flex:1;text-align:center;padding:10px;background:rgba(0,0,0,0.2);border-radius:10px;'>"
            f"<div style='color:#64748b;font-size:0.65em;text-transform:uppercase;'>Mkt Cap</div>"
            f"<div style='font-size:1em;font-weight:700;'>{format_market_cap(hot['total_mcap'])}</div></div>"
            f"</div></div>",
            unsafe_allow_html=True
        )
    
    # Sector comparison row
    st.markdown("<div style='color:#64748b;font-size:0.8em;margin:10px 0 5px 0;'>📊 All Sectors Ranked by Performance</div>", unsafe_allow_html=True)
    
    sorted_sectors = sorted(sector_perf.items(), key=lambda x: x[1]['score'], reverse=True)
    cols = st.columns(len(sorted_sectors))
    for idx, (sector_name, perf) in enumerate(sorted_sectors):
        with cols[idx]:
            is_hot = sector_name == hot_sector
            hot_class = "hot" if is_hot else ""
            change_color = "#22c55e" if perf['avg_change'] >= 0 else "#ef4444"
            change_arrow = "▲" if perf['avg_change'] >= 0 else "▼"
            
            # Short name for display
            short = sector_name.split("(")[0].replace(" &", "").strip()
            if len(short) > 10:
                short = short.split()[0]
            
            st.markdown(
                f"<div class='sector-card {hot_class}' onclick=''>"
                f"<div style='font-size:1.8em;'>{perf['emoji']}</div>"
                f"<div style='color:#e2e8f0;font-size:0.75em;font-weight:600;margin:3px 0;'>{short}</div>"
                f"<div style='font-size:1em;font-weight:700;color:{change_color};'>{change_arrow} {perf['avg_change']:+.2f}%</div>"
                f"<div style='color:#64748b;font-size:0.65em;margin-top:2px;'>{perf['gainers']}/{perf['total']} up</div>"
                f"</div>",
                unsafe_allow_html=True
            )

# ============================================================
# ECONOMIC EVENTS CALENDAR
# ============================================================
if show_events and economic_events:
    st.markdown("<div class='section-header'>📅 Economic Calendar</div>", unsafe_allow_html=True)
    
    events_today = [e for e in economic_events if "Today" in e.get("date", "") or datetime.now().strftime("%b %d") in e.get("date", "")]
    events_upcoming = [e for e in economic_events if e not in events_today]
    
    # Show events in expander
    with st.expander(f"📅 {len(economic_events)} Upcoming Economic Events", expanded=True):
        for event in economic_events[:8]:
            impact_color = get_event_color(event["impact"])
            
            st.markdown(
                f"<div class='event-card' style='border-left-color:{impact_color};'>"
                f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                f"<div>"
                f"<span style='font-size:0.75em;'>{event['impact']}</span> "
                f"<strong style='color:#e2e8f0;font-size:0.85em;'>{event['name']}</strong>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<div style='color:#64748b;font-size:0.75em;'>{event['date']}</div>"
                f"<div style='color:#818cf8;font-size:0.7em;'>{event.get('time', '')}</div>"
                f"</div>"
                f"</div>"
                f"<div style='margin-top:8px;padding:10px;background:rgba(0,0,0,0.2);border-radius:8px;'>"
                f"<div style='color:#cbd5e1;font-size:0.8em;'>{event['analysis']['summary']}</div>"
                f"<div style='color:#64748b;font-size:0.75em;margin-top:5px;'>"
                f"📈 <strong style='color:#22c55e;'>Bullish:</strong> {', '.join(event['analysis']['bullish_sectors'][:3])}<br>"
                f"📉 <strong style='color:#ef4444;'>Bearish:</strong> {', '.join(event['analysis']['bearish_sectors'][:3])}"
                f"</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True
            )

# ============================================================
# SELECTED SECTOR CONTEXT
# ============================================================
if selected_sector != "All Sectors":
    context = get_sector_context(selected_sector, data)
    if context:
        st.markdown(f"<div class='section-header'>{get_sector_emoji(selected_sector)} {selected_sector} - Sector Context</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(
                f"<div class='sector-context'>"
                f"<div style='display:flex;gap:20px;margin-bottom:10px;'>"
                f"<div><span style='color:#64748b;font-size:0.75em;'>Mood:</span> "
                f"<span style='color:{'#22c55e' if context['avg_change'] >= 0 else '#ef4444'};font-weight:600;'>{context['mood']}</span></div>"
                f"<div><span style='color:#64748b;font-size:0.75em;'>Change:</span> "
                f"<span style='color:{'#22c55e' if context['avg_change'] >= 0 else '#ef4444'};font-weight:600;'>{context['avg_change']:+.2f}%</span></div>"
                f"<div><span style='color:#64748b;font-size:0.75em;'>Gainers:</span> "
                f"<span style='color:#22c55e;font-weight:600;'>{context['gainers']}</span></div>"
                f"</div>"
                f"<div style='color:#94a3b8;font-size:0.85em;margin-bottom:10px;'>{context['description'][:200]}</div>"
                f"<div style='font-size:0.8em;font-weight:600;color:#e2e8f0;margin-bottom:5px;'>Key Drivers Today:</div>"
                + "".join(f"<div class='driver-item'>• {d}</div>" for d in context['key_drivers']) +
                f"</div>",
                unsafe_allow_html=True
            )
        with col2:
            if context["why_hot"]:
                st.markdown(
                    f"<div class='sector-context'>"
                    f"<div style='font-size:0.9em;font-weight:600;color:#f97316;'>🔥 Why This Sector</div>"
                    f"<div style='color:#cbd5e1;font-size:0.85em;margin-top:8px;line-height:1.5;'>{context['why_hot']}</div>"
                    f"<div style='margin-top:12px;padding:10px;background:rgba(0,0,0,0.3);border-radius:8px;'>"
                    f"<span style='color:#64748b;font-size:0.75em;'>Top Mover: </span>"
                    f"<span style='color:#818cf8;font-weight:600;'>{context['top_mover']['ticker']}</span> "
                    f"<span style='color:{'#22c55e' if context['top_mover']['change'] >= 0 else '#ef4444'};'>({context['top_mover']['change']:+.2f}%)</span>"
                    f"</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

# ============================================================
# NEWS & SENTIMENT OVERVIEW
# ============================================================
if show_news and all_news:
    st.markdown("<div class='section-header'>📰 Market Sentiment & News</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        s_color = "#22c55e" if sentiment_summary["overall"] in ["Bullish", "Slightly Bullish"] else ("#ef4444" if sentiment_summary["overall"] in ["Bearish", "Slightly Bearish"] else "#eab308")
        st.markdown(f"<div class='hot-hero' style='border-color:{s_color}30;padding:15px;text-align:center;'><div class='summary-label'>Sentiment</div><div class='summary-value' style='color:{s_color}'>{sentiment_summary['emoji']} {sentiment_summary['overall']}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='hot-hero' style='border-color:#22c55e30;padding:15px;text-align:center;'><div class='summary-label'>Bullish</div><div class='summary-value' style='color:#22c55e;'>{sentiment_summary.get('bullish_pct', 0):.0f}%</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='hot-hero' style='border-color:#ef444430;padding:15px;text-align:center;'><div class='summary-label'>Bearish</div><div class='summary-value' style='color:#ef4444;'>{sentiment_summary.get('bearish_pct', 0):.0f}%</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='hot-hero' style='border-color:#818cf830;padding:15px;text-align:center;'><div class='summary-label'>Articles</div><div class='summary-value'>{sentiment_summary['total']}</div></div>", unsafe_allow_html=True)

# ============================================================
# MARKET OVERVIEW
# ============================================================
st.markdown("<div class='section-header'>📈 Market Overview</div>", unsafe_allow_html=True)

total_market_cap = sum(data[t]["market_cap"] for t in data if data[t]["market_cap"])
avg_change = sum(data[t]["change_pct"] for t in data) / len(data) if data else 0
gainers = sum(1 for t in data if data[t]["direction"] == "up")
decliners = sum(1 for t in data if data[t]["direction"] == "down")
avg_pe = sum(data[t]["pe_ratio"] for t in data if data[t]["pe_ratio"]) / sum(1 for t in data if data[t]["pe_ratio"]) if any(data[t]["pe_ratio"] for t in data) else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.markdown(f"<div class='hot-hero' style='border-color:#818cf830;padding:18px;text-align:center;'><div class='summary-label'>Total Market Cap</div><div class='summary-value' style='font-size:1.6em;'>{format_market_cap(total_market_cap)}</div></div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='hot-hero' style='border-color:{'#22c55e30' if avg_change>=0 else '#ef444430'};padding:18px;text-align:center;'><div class='summary-label'>Avg Change</div><div class='summary-value' style='font-size:1.6em;color:{'#22c55e' if avg_change>=0 else '#ef4444'}'>{avg_change:+.2f}%</div></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='hot-hero' style='border-color:#1f2940;padding:18px;text-align:center;'><div class='summary-label'>Gainers / Decliners</div><div class='summary-value' style='font-size:1.6em;'><span style='color:#22c55e;'>{gainers}</span> / <span style='color:#ef4444;'>{decliners}</span></div></div>", unsafe_allow_html=True)
with col4: st.markdown(f"<div class='hot-hero' style='border-color:#1f2940;padding:18px;text-align:center;'><div class='summary-label'>Avg P/E</div><div class='summary-value' style='font-size:1.6em;'>{avg_pe:.1f}</div></div>", unsafe_allow_html=True)
with col5: st.markdown(f"<div class='hot-hero' style='border-color:#1f2940;padding:18px;text-align:center;'><div class='summary-label'>Stocks</div><div class='summary-value' style='font-size:1.6em;'>{len(data)}</div></div>", unsafe_allow_html=True)

# ============================================================
# ALERTS PANEL
# ============================================================
if show_news and 'alerts_data' in dir() and alerts_data and mkt_status['status'] == 'open':
        alert_count = sum(len(a) for a in alerts_data.values())
        if alert_count > 0:
            st.markdown("<div class='section-header'>🔔 Live Alerts</div>", unsafe_allow_html=True)
            high = sum(1 for alerts in alerts_data.values() for a in alerts if a['severity'] == 'high')
            medium = sum(1 for alerts in alerts_data.values() for a in alerts if a['severity'] == 'medium')
            st.markdown(f"<div style='color:#64748b;margin-bottom:10px;font-size:0.85em;'>{'🔴 ' if high else ''}{high} high • {'🟡 ' if medium else ''}{medium} medium • {alert_count} total</div>", unsafe_allow_html=True)
            
            for ticker, alerts in sorted(alerts_data.items()):
                if not alerts: continue
                name = data.get(ticker, {}).get('name', ticker)
                with st.expander(f"🚨 {ticker} - {name} ({len(alerts)} alerts)"):
                    for alert in alerts:
                        severity_color = "#ef4444" if alert['severity'] == 'high' else "#eab308" if alert['severity'] == 'medium' else "#6b7280"
                        st.markdown(
                            f"<div style='background:rgba(0,0,0,0.2);padding:10px 15px;border-radius:8px;margin:4px 0;border-left:3px solid {severity_color};'>"
                            f"<div style='color:#e2e8f0;font-size:0.85em;font-weight:500;'>{alert['message']}</div>"
                            f"<div style='color:#64748b;font-size:0.75em;margin-top:2px;'>{alert['detail']} • {alert['time']}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

# ============================================================
# STOCK DETAILS
# ============================================================
st.markdown("<div class='section-header'>🏢 Stock Details</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-header'>Showing {len(filtered_tickers)} of {len(data)} stocks</div>", unsafe_allow_html=True)

for i in range(0, len(filtered_tickers), 3):
    cols = st.columns(3)
    for j, ticker in enumerate(filtered_tickers[i:i+3]):
        stock = data[ticker]
        with cols[j]:
            direction_class = stock["direction"]
            arrow = "▲" if stock["direction"] == "up" else "▼"
            stock_news = stock_news_cache.get(ticker, [])
            
            st.markdown(
                f"<div class='stock-card'>"
                f"<div style='display:flex;justify-content:space-between;align-items:start;'>"
                f"<div><div style='color:#818cf8;font-size:1.3em;font-weight:700;'>{ticker}</div>"
                f"<div style='color:#64748b;font-size:0.8em;margin-top:-3px;'>{stock['name']}</div>"
                f"<div style='display:inline-block;background:#1a1f30;color:#818cf8;padding:1px 8px;border-radius:8px;font-size:0.65em;border:1px solid #1f2940;margin-top:3px;'>{stock['sector']}</div>"
                f"</div>"
                f"<div style='text-align:right;'>"
                f"<div style='font-size:1.6em;font-weight:700;color:{'#22c55e' if stock['direction']=='up' else '#ef4444'};'>${stock['price']:,.2f}</div>"
                f"<div style='font-size:0.9em;font-weight:500;color:{'#22c55e' if stock['direction']=='up' else '#ef4444'};'>{arrow} {stock['change']:+.2f} ({stock['change_pct']:+.2f}%)</div>"
                f"</div></div>"
                f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px;padding-top:12px;border-top:1px solid #1a1f30;'>"
                f"<div style='background:rgba(0,0,0,0.2);border-radius:8px;padding:8px;text-align:center;'><div style='color:#64748b;font-size:0.65em;text-transform:uppercase;'>Volume</div><div style='color:#e2e8f0;font-size:0.9em;font-weight:600;margin-top:2px;'>{format_volume(stock['volume'])}</div></div>"
                f"<div style='background:rgba(0,0,0,0.2);border-radius:8px;padding:8px;text-align:center;'><div style='color:#64748b;font-size:0.65em;text-transform:uppercase;'>Market Cap</div><div style='color:#e2e8f0;font-size:0.9em;font-weight:600;margin-top:2px;'>{format_market_cap(stock['market_cap'])}</div></div>"
                f"<div style='background:rgba(0,0,0,0.2);border-radius:8px;padding:8px;text-align:center;'><div style='color:#64748b;font-size:0.65em;text-transform:uppercase;'>P/E</div><div style='color:#e2e8f0;font-size:0.9em;font-weight:600;margin-top:2px;'>{f'{stock['pe_ratio']:.1f}' if stock['pe_ratio'] else 'N/A'}</div></div>"
                f"</div></div>",
                unsafe_allow_html=True
            )
            
            # Correlations
            corrs = get_correlations(ticker)
            if corrs:
                with st.expander(f"🤝 Correlations ({len(corrs)} stocks)"):
                    for corr_ticker, corr_info in list(corrs.items())[:5]:
                        strength = corr_info["strength"]
                        bar_color = "#22c55e" if strength >= 0.7 else "#eab308" if strength >= 0.55 else "#64748b"
                        st.markdown(
                            f"<div style='display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid #1a1f30;'>"
                            f"<div><strong style='color:#818cf8;'>{corr_ticker}</strong> "
                            f"<span style='color:#64748b;font-size:0.75em;'>| {corr_info['reason'][:50]}</span></div>"
                            f"<div style='display:flex;align-items:center;gap:8px;'>"
                            f"<span style='font-size:0.8em;font-weight:600;color:{bar_color};'>{strength:.0%}</span>"
                            f"<div style='width:60px;height:6px;background:#1a1f30;border-radius:3px;'>"
                            f"<div style='width:{strength*100}%;height:6px;background:{bar_color};border-radius:3px;'></div></div></div></div>",
                            unsafe_allow_html=True
                        )
            
            # News
            if show_news and stock_news:
                with st.expander(f"📰 News ({len(stock_news)} articles)"):
                    for article in stock_news:
                        bc = "#22c55e" if article["sentiment_label"] == "Bullish" else "#ef4444" if article["sentiment_label"] == "Bearish" else "#eab308"
                    st.markdown(
                        f"<div class='news-card' style='border-left-color:{bc};'>",
                    )

# ============================================================
# SECTOR PERFORMANCE TABLE
# ============================================================
st.markdown("<div class='section-header'>📊 Sector Performance</div>", unsafe_allow_html=True)

sector_data = []
for sector_name in get_sectors_list():
    tickers = get_stocks_for_sector(sector_name)
    sector_stocks_list = [data[t] for t in tickers if t in data]
    if sector_stocks_list:
        avg_sector_change = sum(s["change_pct"] for s in sector_stocks_list) / len(sector_stocks_list)
        sector_market_cap = sum(s["market_cap"] for s in sector_stocks_list)
        sector_data.append({
            "Sector": sector_name,
            "Stocks": len(sector_stocks_list),
            "Avg Change %": f"{avg_sector_change:+.2f}%",
            "Total Market Cap": format_market_cap(sector_market_cap),
            "Direction": "📈" if avg_sector_change >= 0 else "📉"
        })

if sector_data:
    df = pd.DataFrame(sector_data)
    st.dataframe(df, column_config={
        "Sector": st.column_config.TextColumn("Sector"),
        "Stocks": st.column_config.NumberColumn("Stocks"),
        "Avg Change %": st.column_config.TextColumn("Avg Change %"),
        "Total Market Cap": st.column_config.TextColumn("Total Market Cap"),
        "Direction": st.column_config.TextColumn("Status"),
    }, hide_index=True, use_container_width=True)

# ============================================================
# RANKINGS
# ============================================================
col1, col2 = st.columns(2)
with col1:
    st.markdown("<div class='section-header' style='font-size:1.2em;'>🏆 Top 5 Gainers</div>", unsafe_allow_html=True)
    sorted_gainers = sorted(data.values(), key=lambda x: x["change_pct"], reverse=True)[:5]
    for i, stock in enumerate(sorted_gainers):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
        st.markdown(f"<div style='background:#141a28;padding:10px 15px;border-radius:8px;margin:4px 0;border:1px solid #1f2940;'><span style='font-size:1em;'>{medal}</span> <strong style='color:#818cf8;'>{stock['name'][:25]}</strong> <span style='color:#22c55e;float:right;'>+{stock['change_pct']:.2f}% (${stock['price']:.2f})</span></div>", unsafe_allow_html=True)
with col2:
    st.markdown("<div class='section-header' style='font-size:1.2em;'>📉 Top 5 Losers</div>", unsafe_allow_html=True)
    sorted_losers = sorted(data.values(), key=lambda x: x["change_pct"])[:5]
    for i, stock in enumerate(sorted_losers):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
        st.markdown(f"<div style='background:#141a28;padding:10px 15px;border-radius:8px;margin:4px 0;border:1px solid #1f2940;'><span style='font-size:1em;'>{medal}</span> <strong style='color:#818cf8;'>{stock['name'][:25]}</strong> <span style='color:#ef4444;float:right;'>{stock['change_pct']:.2f}% (${stock['price']:.2f})</span></div>", unsafe_allow_html=True)

# ============================================================
# LATEST NEWS FEED
# ============================================================
if show_news and all_news:
    st.markdown("<div class='section-header'>📰 Latest Market News</div>", unsafe_allow_html=True)
    top_news = sorted(all_news, key=lambda x: x.get("published", ""), reverse=True)[:10]
    for article in top_news:
        bc = "#22c55e" if article["sentiment_label"] == "Bullish" else "#ef4444" if article["sentiment_label"] == "Bearish" else "#eab308"
        _url = article["url"]
        _title = article["title"]
        _source = article["source"]
        _pub = article.get("published", "")
        _emoji = article["sentiment_emoji"]
        _label = article["sentiment_label"]
        st.markdown(
            f"<div class='news-card' style='border-left-color:{bc};'>"
            f"<div style='font-size:0.85em;color:#e2e8f0;'><a href='{_url}' target='_blank' style='color:#e2e8f0;text-decoration:none;' onmouseover='this.style.color="#818cf8"' onmouseout='this.style.color="#e2e8f0"'>{_title}</a></div>"
            f"<div style='color:#64748b;font-size:0.7em;margin-top:4px;'><span style='color:#818cf8;'>{_source}</span> • {_pub} • <span style='color:{bc};'>{_emoji} {_label}</span></div>"
            f"</div>",
            unsafe_allow_html=True
        )
# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='footer'>🪐 GGP - God Given Patterns • 7 Sectors • 80+ Stocks • AI-Powered Analytics • Data: Yahoo Finance + TradingView + NewsAPI</div>", unsafe_allow_html=True)

# ============================================================
# AUTO-REFRESH
# ============================================================
if auto_refresh:
    st.toast("🔄 Auto-refresh enabled - updating every 30 seconds")
    time.sleep(30)
    st.rerun()
