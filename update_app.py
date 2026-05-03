# Script to update app.py with clickable links and alerts
import re

with open(r'C:\stock-dashboard\app.py', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Update imports
old_imports = """from news_sentiment import (
    get_stock_news,
    get_market_sentiment_summary,
    analyze_sentiment,
    get_mention_counts
)"""

new_imports = """from news_sentiment import (
    get_stock_news,
    get_market_sentiment_summary,
    analyze_sentiment,
    get_mention_counts
)
from alerts import get_alerts, get_volume_status"""

c = c.replace(old_imports, new_imports)
print("1/4 Imports updated")

# 2. Make news titles clickable in stock expanders
# The old line has: <div class='news-title'>{article['title']}</div>
# Replace with clickable version
old_title = "<div class='news-title'>{article['title']}</div>"
new_title = "<div class='news-title'><a href=\"{article['url']}\" target=\"_blank\" style='color:#e2e8f0;text-decoration:none;' onmouseover=\"this.style.color='#60a5fa'\" onmouseout=\"this.style.color='#e2e8f0'\">{article['title']}</a></div>"
c = c.replace(old_title, new_title)
print("2/4 Stock news titles made clickable")

# 3. Also update the latest market news section (same pattern)
# There might be another instance
c = c.replace(
    "<div class='news-title'>{article['title']}</div>",
    "<div class='news-title'><a href=\"{article['url']}\" target=\"_blank\" style='color:#e2e8f0;text-decoration:none;' onmouseover=\"this.style.color='#60a5fa'\" onmouseout=\"this.style.color='#e2e8f0'\">{article['title']}</a></div>"
)
print("3/4 Market news titles made clickable")

# 4. Add alerts fetching after data fetch
old_after_fetch = "    sentiment_summary = get_market_sentiment_summary(all_news)"
new_after_fetch = """    sentiment_summary = get_market_sentiment_summary(all_news)
    
    # Fetch alerts
    alerts_data = get_alerts(list(data.keys()))
    total_alerts = sum(len(a) for a in alerts_data.values())"""

if old_after_fetch in c:
    c = c.replace(old_after_fetch, new_after_fetch)
    print("4/4 Alerts fetching added")
else:
    # Try without extra spaces
    old_after_fetch2 = "    sentiment_summary = get_market_sentiment_summary(all_news)"
    c = c.replace(old_after_fetch2, new_after_fetch)
    print("4/4 Alerts fetching added (alt)")

# 5. Add alerts panel after market overview section (before stock cards)
old_market = "st.markdown(\"<div class='section-header'>🏢 Stock Details</div>\""
new_market = """# ---- ALERTS PANEL ----
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

st.markdown("<div class='section-header'>🏢 Stock Details</div>" """

c = c.replace(old_market, new_market)
print("5/5 Alerts panel added")

with open(r'C:\stock-dashboard\app.py', 'w', encoding='utf-8') as f:
    f.write(c)

print("\\n✅ All updates applied!")
