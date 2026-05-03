import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# Cache for historical data
_hist_cache = {}
_cache_time = {}

def get_alerts(tickers, threshold_volume=2.0, threshold_price=2.0):
    """
    Detect alerts for all stocks:
    1. Volume spikes (>2x average volume)
    2. Sudden price moves (>2% in recent period)
    3. Intraday unusual activity
    
    Returns dict of ticker -> list of alerts
    """
    alerts = {}
    
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
                
        except Exception as e:
            pass  # Skip if data unavailable
        
        # Sort alerts by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        ticker_alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        if ticker_alerts:
            alerts[ticker] = ticker_alerts
    
    return alerts

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
    
    # Last 3 bars vs average of all bars
    recent_volume = intraday["Volume"].iloc[-3:].mean()
    avg_volume = intraday["Volume"].iloc[:-3].mean()
    
    if avg_volume <= 0:
        return None
    
    ratio = recent_volume / avg_volume
    
    if ratio >= threshold:
        severity = "high" if ratio >= 3.0 else "medium"
        bar_count = min(3, len(intraday))
        return {
            "type": "volume_spike",
            "message": f"🚨 Volume spike! {ratio:.1f}x average ({int(recent_volume):,} vs {int(avg_volume):,})",
            "detail": f"Volume spiked in last {bar_count} bars",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_price_spike(intraday, threshold=2.0):
    """Check for sudden price movements"""
    if len(intraday) < 3:
        return None
    
    # Last 5-minute candle change
    recent = intraday.iloc[-1]
    prev = intraday.iloc[-2]
    
    if prev["Open"] <= 0:
        return None
    
    candle_change = ((recent["Close"] - prev["Close"]) / prev["Close"]) * 100
    
    # Also check high-low range of recent bar
    bar_range = ((recent["High"] - recent["Low"]) / recent["Close"]) * 100 if recent["Close"] else 0
    
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
    
    # Recent bar stats
    recent = intraday.iloc[-1]
    recent_vol = recent["Volume"]
    recent_range = ((recent["High"] - recent["Low"]) / recent["Open"]) * 100 if recent["Open"] else 0
    
    # Historical averages
    avg_vol = intraday["Volume"].iloc[:-1].mean()
    avg_range = ((intraday["High"].iloc[:-1] - intraday["Low"].iloc[:-1]) / intraday["Open"].iloc[:-1]).mean() * 100 if any(intraday["Open"].iloc[:-1] > 0) else 0
    
    if avg_vol <= 0:
        return None
    
    vol_ratio = recent_vol / avg_vol
    range_ratio = recent_range / avg_range if avg_range > 0 else 1
    
    # Unusual when both volume and range are elevated
    if vol_ratio >= 1.5 and range_ratio >= 1.5:
        severity = "high" if (vol_ratio >= 3 and range_ratio >= 2) else "medium"
        alert_type = "unusual_bar"
        
        return {
            "type": alert_type,
            "message": f"⚡ Unusual bar detected! Vol: {vol_ratio:.1f}x, Range: {range_ratio:.1f}x average",
            "detail": f"Volume: {int(recent_vol):,} | Range: {recent_range:.1f}%",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_daily_volume(ticker, threshold=2.0):
    """Check today's volume vs 10-day average"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2mo")
        
        if hist is None or len(hist) < 10:
            return None
        
        # Last 2 days vs 10-day average before that
        recent = hist["Volume"].iloc[-2:].mean() if len(hist) >= 2 else hist["Volume"].iloc[-1]
        avg = hist["Volume"].iloc[:-10].mean() if len(hist) > 10 else hist["Volume"].mean()
        
        if avg <= 0:
            return None
        
        ratio = recent / avg
        
        if ratio >= threshold:
            severity = "high" if ratio >= 4.0 else "medium"
            return {
                "type": "daily_volume",
                "message": f"📊 Daily volume {ratio:.1f}x 10-day average!",
                "detail": f"Recent: {int(recent):,} | Avg: {int(avg):,}",
                "severity": severity,
                "time": datetime.now().strftime("%H:%M"),
            }
    except:
        pass
    
    return None

def get_volume_status(ticker, intraday=None):
    """Get quick volume status indicator"""
    if intraday is None:
        intraday = _get_intraday_data(ticker)
    
    if intraday is None or len(intraday) < 5:
        return {"level": "normal", "ratio": 1.0, "label": "Normal"}
    
    recent = intraday["Volume"].iloc[-3:].mean()
    avg = intraday["Volume"].iloc[:-3].mean()
    
    if avg <= 0:
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
