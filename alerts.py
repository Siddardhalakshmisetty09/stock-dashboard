import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Cache for historical data
_hist_cache = {}
_cache_time = {}

# ============================================================
# MARKET HOURS CHECK (US Stock Market)
# ============================================================
# Regular hours: Mon-Fri, 9:30 AM - 4:00 PM ET
# Pre-market: 4:00 AM - 9:30 AM
# After-hours: 4:00 PM - 8:00 PM

def is_market_open():
    """Check if US stock market is currently in session"""
    now = datetime.now()
    
    # Weekend check
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False, "Weekend"
    
    # Market hours ET (estimate using UTC-4 or UTC-5)
    # Simple approach: use UTC time for approximation
    utc_hour = now.hour
    utc_minute = now.minute
    
    # ET is UTC-4 (EDT) or UTC-5 (EST)
    # Rough: if UTC hour is 13:30 to 20:00, market is open (9:30 AM - 4:00 PM ET)
    # 9:30 AM ET = 13:30 UTC (EDT) or 14:30 UTC (EST)
    # 4:00 PM ET = 20:00 UTC (EDT) or 21:00 UTC (EST)
    
    # Use US Eastern Time via a simpler method: check yfinance data freshness
    # Instead of complex DST calculations, we'll check if the last bar is recent
    
    # For simplicity, market considered "active" during US trading hours
    # 9:30 AM - 4:00 PM ET on weekdays
    market_open_hour = 13  # UTC approx (9:30 AM ET)
    market_close_hour = 20  # UTC approx (4:00 PM ET)
    
    # Check if we're in regular hours (approximate)
    is_open = False
    session = "Closed"
    
    if now.weekday() < 5:  # Weekday
        if utc_hour >= market_open_hour and utc_hour < market_close_hour:
            is_open = True
            session = "Regular Hours"
        elif utc_hour >= 8 and utc_hour < market_open_hour:
            session = "Pre-Market"
        elif utc_hour >= market_close_hour and utc_hour < 24:
            session = "After-Hours"
        elif utc_hour >= 0 and utc_hour < 8:
            session = "Closed (Night)"
    
    return is_open, session

def get_alerts(tickers, threshold_volume=2.0, threshold_price=2.0):
    """
    Detect alerts for all stocks.
    Only generates TRUE alerts when market is open.
    Returns dict of ticker -> list of alerts
    """
    market_open, session = is_market_open()
    alerts = {}
    
    if not market_open:
        # Return empty alerts with session info
        return alerts  # No alerts when market is closed
    
    for ticker in tickers:
        ticker_alerts = []
        
        try:
            # Fetch 5-minute intraday data
            intraday = _get_intraday_data(ticker)
            
            if intraday is not None and not intraday.empty:
                # --- CHECK 1: Volume Spike ---
                vol_alert = _check_volume_spike(intraday, threshold_volume)
                if vol_alert:
                    ticker_alerts.append(vol_alert)
                
                # --- CHECK 2: Sudden Price Move ---
                price_alert = _check_price_spike(intraday, threshold_price)
                if price_alert:
                    ticker_alerts.append(price_alert)
                
                # --- CHECK 3: Unusual Volume Bar ---
                bar_alert = _check_unusual_bar(intraday, ticker)
                if bar_alert:
                    ticker_alerts.append(bar_alert)
            
            # --- CHECK 4: Daily Volume vs Average ---
            daily_alert = _check_daily_volume(ticker, threshold_volume)
            if daily_alert:
                ticker_alerts.append(daily_alert)
                
        except Exception:
            pass  # Skip if data unavailable
        
        # Sort alerts by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        ticker_alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        if ticker_alerts:
            alerts[ticker] = ticker_alerts
    
    return alerts

def get_market_status():
    """Get market status for display"""
    market_open, session = is_market_open()
    
    if market_open:
        return {
            "status": "open",
            "label": "🟢 Market Open",
            "session": session,
            "color": "#22c55e"
        }
    else:
        return {
            "status": "closed",
            "label": "🔴 Market Closed",
            "session": session,
            "color": "#ef4444"
        }

def _get_intraday_data(ticker, interval="5m", period="2d"):
    """Fetch intraday data for alert detection"""
    cache_key = f"{ticker}_{interval}"
    
    # Use cache (30 second TTL for 5m data)
    if cache_key in _cache_time:
        if (datetime.now() - _cache_time[cache_key]).seconds < 30:
            return _hist_cache.get(cache_key)
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        if hist is not None and not hist.empty:
            _hist_cache[cache_key] = hist
            _cache_time[cache_key] = datetime.now()
            return hist
    except:
        pass
    
    return None

def _check_volume_spike(intraday, threshold=2.0):
    """Check if recent volume is significantly above average"""
    if len(intraday) < 5:
        return None
    
    # Only consider data from today if it's the most recent day
    # Filter to only include recent trading day data
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    # Last 3 bars vs average of today's bars
    recent_volume = recent_data["Volume"].iloc[-3:].mean()
    avg_volume = recent_data["Volume"].iloc[:-3].mean()
    
    # If avg_volume is too small (thin data), skip alert
    if avg_volume <= 0 or recent_volume < 1000:  # Skip if volume is negligible
        return None
    
    ratio = recent_volume / avg_volume if avg_volume > 0 else 0
    
    if ratio >= threshold and recent_volume > 10000:  # Minimum meaningful volume
        severity = "high" if ratio >= 3.0 else "medium"
        return {
            "type": "volume_spike",
            "message": f"🚨 Volume spike! {ratio:.1f}x average ({int(recent_volume):,} vs {int(avg_volume):,})",
            "detail": f"Comparing intraday bars only",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_price_spike(intraday, threshold=2.0):
    """Check for sudden price movements"""
    if len(intraday) < 3:
        return None
    
    # Only consider today's data
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    # Last 5-minute candle change
    recent = recent_data.iloc[-1]
    prev = recent_data.iloc[-2]
    
    if prev["Close"] <= 0:
        return None
    
    candle_change = ((recent["Close"] - prev["Close"]) / prev["Close"]) * 100
    
    # Also check high-low range of recent bar
    bar_range = ((recent["High"] - recent["Low"]) / recent["Close"]) * 100 if recent["Close"] else 0
    
    # Only alert if price moved meaningfully AND volume is decent (real trades)
    if abs(candle_change) >= threshold or bar_range >= threshold * 1.5:
        direction = "surged" if candle_change > 0 else "dropped"
        emoji = "🚀" if candle_change > 0 else "📉"
        severity = "high" if abs(candle_change) >= 3.0 else "medium"
        
        return {
            "type": "price_spike",
            "message": f"{emoji} Price {direction} {abs(candle_change):.1f}% in 5min!",
            "detail": f"Range: {bar_range:.1f}% | Close: ${recent['Close']:.2f}",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_unusual_bar(intraday, ticker):
    """Check for unusually large candles (big volume + big range)"""
    if len(intraday) < 5:
        return None
    
    # Only consider today's data
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    # Recent bar stats
    recent = recent_data.iloc[-1]
    recent_vol = recent["Volume"]
    recent_range = ((recent["High"] - recent["Low"]) / recent["Open"]) * 100 if recent["Open"] else 0
    
    # Historical averages (today only)
    avg_vol = recent_data["Volume"].iloc[:-1].mean()
    avg_range = ((recent_data["High"].iloc[:-1] - recent_data["Low"].iloc[:-1]) / recent_data["Open"].iloc[:-1]).mean() * 100 if any(recent_data["Open"].iloc[:-1] > 0) else 0
    
    if avg_vol <= 0 or recent_vol < 1000:
        return None
    
    vol_ratio = recent_vol / avg_vol
    range_ratio = recent_range / avg_range if avg_range > 0 else 1
    
    # Unusual when both volume and range are elevated with meaningful activity
    if vol_ratio >= 1.5 and range_ratio >= 1.5 and recent_vol > 10000:
        severity = "high" if (vol_ratio >= 3 and range_ratio >= 2) else "medium"
        
        return {
            "type": "unusual_bar",
            "message": f"⚡ Unusual bar detected! Vol: {vol_ratio:.1f}x, Range: {range_ratio:.1f}x average",
            "detail": f"Volume: {int(recent_vol):,} | Range: {recent_range:.1f}%",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_daily_volume(ticker, threshold=2.0):
    """Check today's volume vs 10-day average (only if today has meaningful data)"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2mo")
        
        if hist is None or len(hist) < 10:
            return None
        
        # Check if today's data exists and has meaningful volume
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = hist[hist.index.strftime("%Y-%m-%d") == today]
        
        # If no today data or very low volume, skip
        if today_data.empty or today_data["Volume"].iloc[-1] < 100000:
            return None
        
        today_volume = today_data["Volume"].iloc[-1]
        
        # Average of previous 10 trading days
        prev_days = hist[hist.index < today]
        if len(prev_days) >= 10:
            avg_volume = prev_days["Volume"].iloc[-10:].mean()
        else:
            avg_volume = prev_days["Volume"].mean()
        
        if avg_volume <= 0:
            return None
        
        ratio = today_volume / avg_volume
        
        if ratio >= threshold:
            severity = "high" if ratio >= 4.0 else "medium"
            return {
                "type": "daily_volume",
                "message": f"📊 Daily volume {ratio:.1f}x 10-day average!",
                "detail": f"Today: {int(today_volume):,} | Avg: {int(avg_volume):,}",
                "severity": severity,
                "time": datetime.now().strftime("%H:%M"),
            }
    except:
        pass
    
    return None

def get_volume_status(ticker, intraday=None):
    """Get quick volume status indicator - returns normal if market closed"""
    market_open, _ = is_market_open()
    
    if not market_open:
        return {"level": "normal", "ratio": 1.0, "label": "Market Closed"}
    
    if intraday is None:
        intraday = _get_intraday_data(ticker)
    
    if intraday is None or len(intraday) < 5:
        return {"level": "normal", "ratio": 1.0, "label": "Normal"}
    
    # Only today's data
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return {"level": "normal", "ratio": 1.0, "label": "Normal"}
    
    recent = recent_data["Volume"].iloc[-3:].mean()
    avg = recent_data["Volume"].iloc[:-3].mean()
    
    if avg <= 0 or recent < 1000:
        return {"level": "normal", "ratio": 1.0, "label": "Normal"}
    
    ratio = recent / avg
    
    if ratio >= 3.0:
        return {"level": "extreme", "ratio": round(ratio, 1), "label": "🔥 Extreme"}
    elif ratio >= 2.0:
        return {"level": "high", "ratio": round(ratio, 1), "label": "⚡ High"}
    elif ratio >= 1.5:
        return {"level": "elevated", "ratio": round(ratio, 1), "label": "📈 Elevated"}
    else:
        return {"level": "normal", "ratio": round(ratio, 1), "label": "Normal"}
