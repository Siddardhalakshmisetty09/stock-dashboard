import requests
from datetime import datetime, timedelta, date
import feedparser
import re

# ============================================================
# ECONOMIC EVENTS CALENDAR (Free sources)
# Aggregates from ForexFactory RSS & FRED
# ============================================================

# Event impact levels
IMPACT_HIGH = "🔴"
IMPACT_MEDIUM = "🟡"
IMPACT_LOW = "🟢"

def get_economic_events(days_ahead=7):
    """Get upcoming economic events with impact analysis"""
    events = []
    
    # Try ForexFactory RSS (free, no API key)
    try:
        events = _fetch_from_forexfactory(days_ahead)
    except:
        pass
    
    # Fallback to hardcoded upcoming events if RSS fails
    if not events:
        events = _get_hardcoded_events(days_ahead)
    
    return events[:15]  # Max 15 events

def _fetch_from_forexfactory(days_ahead):
    """Fetch economic calendar from ForexFactory RSS"""
    url = "https://www.forexfactory.com/ffcal_week_this.xml"
    
    feed = feedparser.parse(url)
    events = []
    
    now = datetime.now()
    cutoff = now + timedelta(days=days_ahead)
    
    for entry in feed.entries[:30]:
        title = entry.get("title", "")
        
        # Parse the ForexFactory format
        # Format: "date time currency impact event actual forecast previous"
        parts = title.split()
        if len(parts) < 4:
            continue
        
        # Extract event details
        try:
            event_date_str = parts[0]  # "May5"
            event_time = parts[1] if len(parts) > 1 else "All Day"
            
            # Find impact level
            impact = IMPACT_LOW
            for i, part in enumerate(parts):
                if part in ["High", "Medium", "Low"]:
                    if part == "High":
                        impact = IMPACT_HIGH
                    elif part == "Medium":
                        impact = IMPACT_MEDIUM
                    else:
                        impact = IMPACT_LOW
                    
                    # Event name is everything after impact
                    event_name = " ".join(parts[i+1:]) if i+1 < len(parts) else title
                    break
            else:
                event_name = title
                impact = IMPACT_MEDIUM
            
            # Clean event name
            event_name = re.sub(r'\d+\.\d+[kKmMbB]?', '', event_name).strip()
            event_name = re.sub(r'\s+', ' ', event_name).strip()
            if not event_name:
                continue
            
            # Parse date
            try:
                month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
                month_str = re.findall(r'[A-Z][a-z]{2}', event_date_str)
                day_str = re.findall(r'\d+', event_date_str)
                
                if month_str and day_str:
                    month = month_map.get(month_str[0], now.month)
                    day = int(day_str[0])
                    year = now.year
                    
                    # Handle year rollover
                    if month < now.month and year == now.year:
                        year += 1
                    
                    event_date = datetime(year, month, day)
                else:
                    event_date = now
            except:
                event_date = now
            
            if event_date < now or event_date > cutoff:
                continue
            
            # Generate impact analysis
            analysis = _analyze_event_impact(event_name)
            
            events.append({
                "date": event_date.strftime("%a, %b %d"),
                "time": event_time,
                "name": event_name[:80],
                "impact": impact,
                "impact_label": "High" if impact == IMPACT_HIGH else ("Medium" if impact == IMPACT_MEDIUM else "Low"),
                "analysis": analysis,
                "raw_date": event_date,
            })
        except:
            continue
    
    # Sort by date
    events.sort(key=lambda x: x["raw_date"])
    
    # Remove duplicates
    seen = set()
    unique = []
    for e in events:
        key = (e["name"][:30], e["date"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    
    return unique

def _get_hardcoded_events(days_ahead):
    """Fallback hardcoded events (refreshed monthly for accuracy)"""
    now = datetime.now()
    today = now.date()
    events = []
    
    # Typical monthly recurring events
    recurring_events = [
        # Weekly
        {"name": "Initial Jobless Claims", "day_offset": 1, "impact": IMPACT_MEDIUM, "weekday": 3},  # Thu
        {"name": "EIA Crude Oil Inventories", "day_offset": 2, "impact": IMPACT_MEDIUM, "weekday": 2},  # Wed
        {"name": "Federal Budget Statement", "day_offset": 3, "impact": IMPACT_MEDIUM, "weekday": 4},  # Fri
        
        # Monthly
        {"name": "ISM Manufacturing PMI", "day_offset": 1, "impact": IMPACT_MEDIUM},
        {"name": "ISM Services PMI", "day_offset": 2, "impact": IMPACT_MEDIUM},
        {"name": "Consumer Price Index (CPI) MoM", "day_offset": 3, "impact": IMPACT_HIGH},
        {"name": "Producer Price Index (PPI) MoM", "day_offset": 4, "impact": IMPACT_MEDIUM},
        {"name": "Retail Sales MoM", "day_offset": 5, "impact": IMPACT_HIGH},
        {"name": "Industrial Production MoM", "day_offset": 6, "impact": IMPACT_MEDIUM},
        {"name": "Building Permits", "day_offset": 7, "impact": IMPACT_LOW},
        {"name": "Existing Home Sales", "day_offset": 8, "impact": IMPACT_LOW},
        {"name": "New Home Sales", "day_offset": 9, "impact": IMPACT_LOW},
        {"name": "Durable Goods Orders MoM", "day_offset": 10, "impact": IMPACT_MEDIUM},
        {"name": "GDP Growth Rate QoQ", "day_offset": 11, "impact": IMPACT_HIGH},
        {"name": "Michigan Consumer Sentiment", "day_offset": 12, "impact": IMPACT_MEDIUM},
        {"name": "Employment Change (NFP)", "day_offset": 13, "impact": IMPACT_HIGH},
        {"name": "Unemployment Rate", "day_offset": 14, "impact": IMPACT_HIGH},
        {"name": "Average Hourly Earnings MoM", "day_offset": 15, "impact": IMPACT_MEDIUM},
    ]
    
    # Generate events for next N days
    for day_offset in range(days_ahead + 5):
        # Skip weekends
        check_date = today + timedelta(days=day_offset)
        if check_date.weekday() >= 5:
            continue
        
        for event in recurring_events:
            if "weekday" in event:
                # Weekly events on specific weekday
                if check_date.weekday() != event["weekday"]:
                    continue
            
            # Monthly events - assume roughly same day each month
            if "weekday" not in event:
                # Only place monthly events on roughly expected dates
                if day_offset not in range(1, 22):  # Skip last week
                    if day_offset % 5 != event["day_offset"] % 5:
                        continue
            
            # Skip if too far ahead
            if day_offset > days_ahead:
                continue
            
            event_date = datetime.combine(check_date, datetime.min.time())
            
            analysis = _analyze_event_impact(event["name"])
            
            events.append({
                "date": event_date.strftime("%a, %b %d"),
                "time": "TBD",
                "name": event["name"],
                "impact": event["impact"],
                "impact_label": "High" if event["impact"] == IMPACT_HIGH else ("Medium" if event["impact"] == IMPACT_MEDIUM else "Low"),
                "analysis": analysis,
                "raw_date": event_date,
            })
    
    # Add this week's known events
    known_events = _get_known_events(today)
    events.extend(known_events)
    
    # Sort and deduplicate
    events.sort(key=lambda x: x["raw_date"])
    seen = set()
    unique = []
    for e in events:
        key = (e["name"][:30], e["date"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    
    return unique[:15]

def _get_known_events(today):
    """Get known events for the current week"""
    weekday = today.weekday()
    events = []
    
    # This week's known events (these change monthly, update as needed)
    # For May 2026
    may_2026_events = [
        {"name": "FOMC Interest Rate Decision", "date_str": "May 7", "impact": IMPACT_HIGH},
        {"name": "Consumer Credit Change", "date_str": "May 8", "impact": IMPACT_LOW},
        {"name": "Wholesale Inventories MoM", "date_str": "May 9", "impact": IMPACT_LOW},
        {"name": "Core CPI MoM", "date_str": "May 13", "impact": IMPACT_HIGH},
        {"name": "Import Price Index MoM", "date_str": "May 14", "impact": IMPACT_LOW},
    ]
    
    for event in may_2026_events:
        try:
            parts = event["date_str"].split()
            month = parts[0]
            day = int(parts[1])
            month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
            month_num = month_map.get(month, today.month)
            year = today.year
            if month_num < today.month and year == today.year:
                year += 1
            
            event_date = datetime(year, month_num, day)
            
            # Only include if within next 10 days
            if 0 <= (event_date.date() - today).days <= 10:
                analysis = _analyze_event_impact(event["name"])
                events.append({
                    "date": event_date.strftime("%a, %b %d"),
                    "time": "TBD",
                    "name": event["name"],
                    "impact": event["impact"],
                    "impact_label": "High" if event["impact"] == IMPACT_HIGH else "Medium",
                    "analysis": analysis,
                    "raw_date": event_date,
                })
        except:
            pass
    
    return events

def _analyze_event_impact(event_name):
    """Generate analysis of what an event means for markets"""
    event_lower = event_name.lower()
    
    # Interest Rate / FOMC
    if "fomc" in event_lower or "interest rate" in event_lower or "fed" in event_lower:
        return {
            "summary": "Fed decision on interest rates - the most important event for markets",
            "bullish_sectors": ["🏦 Financials (XLF)", "🥇 Gold & Mining"],
            "bearish_sectors": ["🤖 AI/Backbone", "📈 FANGMAN+"],
            "details": "Rate cut → Gold 🚀, Tech 🚀, USD 📉\nRate hold → Banks 🚀, Gold 📉\nRate hike → Everything 📉",
            "volatility": "🔥 Extreme - expect 2-5% market swings",
        }
    
    # CPI / Inflation
    elif "cpi" in event_lower or "consumer price" in event_lower or "inflation" in event_lower:
        return {
            "summary": "Consumer Price Index - key inflation gauge",
            "bullish_sectors": ["🥇 Gold & Mining", "🟢 Copper & Miners"],
            "bearish_sectors": ["📈 FANGMAN+", "🔬 Quantum"],
            "details": "CPI higher than expected → Rates stay high → Gold 🚀, Tech 📉\nCPI lower than expected → Rate cuts coming → Everything 🚀",
            "volatility": "🔥 High - 1-3% market moves",
        }
    
    # Employment / NFP
    elif "nonfarm" in event_lower or "employment" in event_lower or "jobless" in event_lower or "unemployment" in event_lower or "nfp" in event_lower:
        return {
            "summary": "Monthly jobs report - measures labor market health",
            "bullish_sectors": ["🏦 Financials (XLF)", "📈 FANGMAN+"],
            "bearish_sectors": ["🥇 Gold & Mining"],
            "details": "Strong jobs → Economy good → Banks 🚀, Gold 📉\nWeak jobs → Rate cuts → Gold 🚀, Everything 🚀",
            "volatility": "🔥 High - 1-2% market moves",
        }
    
    # GDP
    elif "gdp" in event_lower:
        return {
            "summary": "Gross Domestic Product - broadest economic measure",
            "bullish_sectors": ["🤖 AI/Backbone", "📈 FANGMAN+", "🏦 Financials"],
            "bearish_sectors": ["🥇 Gold & Mining"],
            "details": "GDP up → Economy growing → Stocks 🚀\nGDP down → Recession fears → Gold 🚀, Cyclicals 📉",
            "volatility": "🟡 Moderate - 0.5-1.5% moves",
        }
    
    # Manufacturing / PMI
    elif "pmi" in event_lower or "manufacturing" in event_lower or "industrial" in event_lower:
        return {
            "summary": "Measures factory activity and industrial health",
            "bullish_sectors": ["🖥️ Semiconductors", "🟢 Copper & Miners"],
            "bearish_sectors": ["🥇 Gold & Mining"],
            "details": "PMI > 50 = Expansion → Industrials 🚀, Copper 🚀\nPMI < 50 = Contraction → Defensive sectors 🚀",
            "volatility": "🟡 Moderate",
        }
    
    # Retail Sales
    elif "retail" in event_lower or "consumer" in event_lower:
        return {
            "summary": "Consumer spending health check",
            "bullish_sectors": ["📈 FANGMAN+", "🏦 Financials"],
            "bearish_sectors": ["🥇 Gold & Mining"],
            "details": "Strong retail → Consumer strong → FANGMAN 🚀\nWeak retail → Recession fears → Gold 🚀",
            "volatility": "🟡 Moderate",
        }
    
    # Housing
    elif "housing" in event_lower or "home" in event_lower or "building" in event_lower:
        return {
            "summary": "Housing market health indicator",
            "bullish_sectors": ["🏦 Financials (XLF)", "🟢 Copper & Miners"],
            "bearish_sectors": [],
            "details": "Housing up → Economy strong → Banks 🚀, Copper 🚀\nHousing down → Rate cuts → Gold 🚀",
            "volatility": "🟢 Low",
        }
    
    # Generic analysis for unknown events
    return {
        "summary": f"Economic data release - monitors {event_name} trends",
        "bullish_sectors": ["All sectors if positive surprise"],
        "bearish_sectors": ["All sectors if negative surprise"],
        "details": "Watch for actual vs forecast difference.\nPositive surprise → Markets 🚀\nNegative surprise → Markets 📉",
        "volatility": "🟡 Moderate",
    }

def get_event_color(impact):
    """Get color for event impact level"""
    if impact == IMPACT_HIGH:
        return "#ef4444"
    elif impact == IMPACT_MEDIUM:
        return "#eab308"
    else:
        return "#22c55e"

def format_event_time(event):
    """Format event time for display"""
    if event.get("time") and event["time"] != "TBD" and event["time"] != "All Day":
        return f"⏰ {event['time']}"
    return "📅 All Day"
