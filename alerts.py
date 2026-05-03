import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import json

# Cache for historical data
_hist_cache = {}
_cache_time = {}

# ============================================================
# TRADINGVIEW DATA FETCHER (More accurate than yfinance)
# ============================================================

TV_INTERVALS = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "1h": "60",
    "4h": "240",
    "1d": "1D",
}

def fetch_tradingview_data(ticker, interval="5m", count=100):
    """
    Fetch OHLCV data from TradingView's unofficial REST API.
    More accurate and faster than yfinance for intraday data.
    """
    cache_key = f"tv_{ticker}_{interval}"
    
    # Cache for 20 seconds
    if cache_key in _cache_time:
        if (datetime.now() - _cache_time[cache_key]).seconds < 20:
            return _hist_cache.get(cache_key)
    
    try:
        # Map ticker to TradingView format
        tv_symbol = _to_tv_symbol(ticker)
        tv_interval = TV_INTERVALS.get(interval, "5")
        
        # TradingView chart data endpoint
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
        }
        
        url = f"https://chartdata.tradingview.com/symbols/{tv_symbol}/bars?resolution={tv_interval}&from={int((datetime.now() - timedelta(days=3)).timestamp())}&to={int(datetime.now().timestamp())}&countback={count}"
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            return _fallback_to_yfinance(ticker, interval)
        
        data = response.json()
        
        if not data or "bars" not in data:
            return _fallback_to_yfinance(ticker, interval)
        
        # Parse into DataFrame
        bars = data["bars"]
        records = []
        for bar in bars:
            records.append({
                "Open": float(bar["open"]),
                "High": float(bar["high"]),
                "Low": float(bar["low"]),
                "Close": float(bar["close"]),
                "Volume": float(bar["volume"]),
                "Datetime": pd.to_datetime(bar["time"], unit="s"),
            })
        
        df = pd.DataFrame(records)
        df.set_index("Datetime", inplace=True)
        df.sort_index(inplace=True)
        
        _hist_cache[cache_key] = df
        _cache_time[cache_key] = datetime.now()
        return df
        
    except Exception:
        return _fallback_to_yfinance(ticker, interval)

def _to_tv_symbol(ticker):
    """Map stock ticker to TradingView symbol format"""
    exchange_map = {
        "TSM": "NYSE:TSM",
        "SMCI": "NASDAQ:SMCI",
        "ARM": "NASDAQ:ARM",
    }
    if ticker in exchange_map:
        return exchange_map[ticker]
    return ticker

def _fallback_to_yfinance(ticker, interval="5m"):
    """Fallback to yfinance when TradingView fails"""
    cache_key = f"yf_{ticker}_{interval}"
    
    if cache_key in _cache_time:
        if (datetime.now() - _cache_time[cache_key]).seconds < 60:
            return _hist_cache.get(cache_key)
    
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d", interval=interval)
        if hist is not None and not hist.empty:
            _hist_cache[cache_key] = hist
            _cache_time[cache_key] = datetime.now()
            return hist
    except:
        pass
    return None

def get_tradingview_volume_analysis(ticker):
    """Get volume analysis directly from TradingView"""
    try:
        df = fetch_tradingview_data(ticker, interval="5m", count=50)
        if df is None or len(df) < 10:
            return None
        
        recent_5 = df["Volume"].iloc[-5:].mean()
        avg_5 = df["Volume"].iloc[:-5].mean()
        
        if avg_5 <= 0:
            return None
        
        ratio = recent_5 / avg_5
        
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        price_change = ((last_candle["Close"] - prev_candle["Close"]) / prev_candle["Close"]) * 100
        
        return {
            "ticker": ticker,
            "source": "TradingView",
            "recent_avg_volume": int(recent_5),
            "overall_avg_volume": int(avg_5),
            "volume_ratio": round(ratio, 1),
            "price_change_5m": round(price_change, 2),
            "last_price": round(last_candle["Close"], 2),
            "last_volume": int(last_candle["Volume"]),
            "total_volume_today": int(df["Volume"].sum()),
        }
    except:
        return None


# ============================================================
# MARKET HOURS CHECK (US Stock Market)
# ============================================================

def is_market_open():
    """Check if US stock market is currently in session"
    Returns: (is_active, session_type)
    Session types: "Regular Hours", "Pre-Market", "After-Hours", "Closed"
    """
    now = datetime.now()
    
    if now.weekday() >= 5:
        return False, "Weekend"
    
    # US Eastern Time approximate (UTC-4 for EDT)
    utc_hour = now.hour
    utc_minute = now.minute
    
    # Regular market hours: 9:30 AM - 4:00 PM ET = 13:30 - 20:00 UTC (EDT)
    # Pre-market: 4:00 AM - 9:30 AM ET = 8:00 - 13:30 UTC
    # After-hours: 4:00 PM - 8:00 PM ET = 20:00 - 00:00 UTC
    
    pre_market_start = 8       # 4:00 AM ET
    market_open = 13           # 9:30 AM ET approx
    market_close = 20          # 4:00 PM ET approx
    after_hours_end = 24       # 8:00 PM ET approx
    
    if now.weekday() < 5:
        if utc_hour >= market_open and utc_hour < market_close:
            return True, "Regular Hours"
        elif utc_hour >= pre_market_start and utc_hour < market_open:
            return True, "Pre-Market"  # Treat as active for alerts
        elif utc_hour >= market_close and utc_hour < after_hours_end:
            return True, "After-Hours"  # Treat as active for alerts
        else:
            return False, "Closed (Night)"
    
    return False, "Closed"

def get_alerts(tickers, threshold_volume=2.0, threshold_price=2.0):
    """
    Detect alerts for all stocks.
    Uses TradingView data FIRST, falls back to yfinance.
    Only generates alerts when market is open.
    """
    market_open, session = is_market_open()
    alerts = {}
    
    if not market_open:
        return alerts
    
    for ticker in tickers:
        ticker_alerts = []
        
        try:
            # Try TradingView first for 5m data
            intraday = fetch_tradingview_data(ticker, interval="5m", count=80)
            
            # Fallback to yfinance if TradingView fails
            if intraday is None:
                intraday = _get_intraday_data_yf(ticker)
            
            if intraday is not None and not intraday.empty:
                # Volume Spike
                vol_alert = _check_volume_spike(intraday, threshold_volume)
                if vol_alert:
                    ticker_alerts.append(vol_alert)
                
                # Sudden Price Move
                price_alert = _check_price_spike(intraday, threshold_price)
                if price_alert:
                    ticker_alerts.append(price_alert)
                
                # Unusual Bar
                bar_alert = _check_unusual_bar(intraday, ticker)
                if bar_alert:
                    ticker_alerts.append(bar_alert)
            
            # Daily Volume vs Average
            daily_alert = _check_daily_volume(ticker, threshold_volume)
            if daily_alert:
                ticker_alerts.append(daily_alert)
                
        except Exception:
            pass
        
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
            "label": "Market Open",
            "session": session,
            "color": "#22c55e"
        }
    else:
        return {
            "status": "closed",
            "label": "Market Closed",
            "session": session,
            "color": "#ef4444"
        }

def _get_intraday_data_yf(ticker, interval="5m", period="2d"):
    """Fetch intraday data via yfinance"""
    cache_key = f"yf_{ticker}_{interval}"
    
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
    
    # Only today's data
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    recent_volume = recent_data["Volume"].iloc[-3:].mean()
    avg_volume = recent_data["Volume"].iloc[:-3].mean()
    
    if avg_volume <= 0 or recent_volume < 1000:
        return None
    
    ratio = recent_volume / avg_volume if avg_volume > 0 else 0
    
    if ratio >= threshold and recent_volume > 10000:
        severity = "high" if ratio >= 3.0 else "medium"
        return {
            "type": "volume_spike",
            "message": f"🚨 Volume spike! {ratio:.1f}x average ({int(recent_volume):,} vs {int(avg_volume):,})",
            "detail": f"Intraday bars (TradingView)",
            "severity": severity,
            "time": datetime.now().strftime("%H:%M"),
        }
    
    return None

def _check_price_spike(intraday, threshold=2.0):
    """Check for sudden price movements"""
    if len(intraday) < 3:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    recent = recent_data.iloc[-1]
    prev = recent_data.iloc[-2]
    
    if prev["Close"] <= 0:
        return None
    
    candle_change = ((recent["Close"] - prev["Close"]) / prev["Close"]) * 100
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
    """Check for unusually large candles"""
    if len(intraday) < 5:
        return None
    
    today = datetime.now().strftime("%Y-%m-%d")
    recent_data = intraday[intraday.index >= today] if today in intraday.index.strftime("%Y-%m-%d").values else intraday
    
    if len(recent_data) < 3:
        return None
    
    recent = recent_data.iloc[-1]
    recent_vol = recent["Volume"]
    recent_range = ((recent["High"] - recent["Low"]) / recent["Open"]) * 100 if recent["Open"] else 0
    
    avg_vol = recent_data["Volume"].iloc[:-1].mean()
    avg_range = ((recent_data["High"].iloc[:-1] - recent_data["Low"].iloc[:-1]) / recent_data["Open"].iloc[:-1]).mean() * 100 if any(recent_data["Open"].iloc[:-1] > 0) else 0
    
    if avg_vol <= 0 or recent_vol < 1000:
        return None
    
    vol_ratio = recent_vol / avg_vol
    range_ratio = recent_range / avg_range if avg_range > 0 else 1
    
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
    """Check today's volume vs 10-day average"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2mo")
        
        if hist is None or len(hist) < 10:
            return None
        
        today = datetime.now().strftime("%Y-%m-%d")
        today_data = hist[hist.index.strftime("%Y-%m-%d") == today]
        
        if today_data.empty or today_data["Volume"].iloc[-1] < 100000:
            return None
        
        today_volume = today_data["Volume"].iloc[-1]
        
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
    """Get quick volume status indicator"""
    market_open, _ = is_market_open()
    
    if not market_open:
        return {"level": "normal", "ratio": 1.0, "label": "Market Closed"}
    
    if intraday is None:
        intraday = fetch_tradingview_data(ticker, interval="5m", count=50)
    
    if intraday is None or len(intraday) < 5:
        return {"level": "normal", "ratio": 1.0, "label": "Normal"}
    
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
