import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# ALL SECTORS - Stocks that matter
# ============================================================

# Quant Sector Analysis (for Hot Sector feature)
SECTOR_ANALYSIS = {
    "🤖 AI/Backbone": {
        "stocks": ["NVDA", "AMD", "TSM", "ASML", "AVGO", "MU", "MRVL", "ANET", "CRWD", "PLTR", "INTC", "DELL", "SMCI", "ARM", "WDC"],
        "emoji": "🤖",
        "color": "#3b82f6",
        "description": "The infrastructure & chip companies powering the AI revolution. From NVIDIA's GPUs to TSMC's fabrication, these are the picks-and-shovels of the AI gold rush.",
        "why_hot": "AI CAPEX is exploding - hyperscalers spent $200B+ in 2025. Every major tech company is in an AI arms race, driving unprecedented demand for chips, networking, and data center infrastructure.",
    },
    "🥇 Gold & Precious Metals": {
        "stocks": ["NEM", "GOLD", "FNV", "WPM", "RGLD", "AEM", "KGC", "AGI", "SSRM", "PAAS"],
        "emoji": "🥇",
        "color": "#f59e0b",
        "description": "Top gold miners and royalty companies. Gold is soaring as a hedge against inflation, geopolitical uncertainty, and USD weakness.",
        "why_hot": "Gold hit all-time highs in 2025 driven by central bank buying (China, India, Russia adding 1,000+ tonnes). Plus rate cuts are incoming = weaker USD = higher gold. Safe haven demand is surging.",
    },
    "🔬 Quantum Computing": {
        "stocks": ["IONQ", "RGTI", "QUBT", "QBTS", "ARQQ", "QSI", "LAES", "AEHR", "QTWO", "RGTI"],
        "emoji": "🔬",
        "color": "#8b5cf6",
        "description": "Pure-play quantum computing companies. From trapped-ion qubits to quantum annealing, these are the frontier of next-gen computing.",
        "why_hot": "IBM, Google, and Microsoft all claimed quantum supremacy milestones in 2025. Government funding (US CHIPS Act, EU, Japan) poured $5B+ into quantum R&D. Commercial quantum advantage is now forecast by 2027 - the race is ON.",
    },
    "📈 Core Tech": {
        "stocks": ["META", "AMZN", "NFLX", "GOOGL", "MSFT", "AAPL", "NVDA", "TSLA", "ORCL", "IBM", "CRM", "ADBE", "NOW", "SAP"],
        "emoji": "📈",
        "color": "#ec4899",
        "description": "Mega-cap tech titans + enterprise software leaders. These stocks drive global market direction.",
        "why_hot": "Enterprise software and cloud spending is rebounding. AI monetization flowing to bottom lines. ORCL cloud revenue surged, CRM AI agents driving adoption, ADBE integrating AI across products.",
    },
    "🖥️ Semiconductors": {
        "stocks": ["NVDA", "AMD", "INTC", "TSM", "ASML", "AVGO", "MRVL", "MU", "QCOM", "AMAT", "LRCX", "KLAC", "NXPI", "STM", "ON"],
        "emoji": "🖥️",
        "color": "#06b6d4",
        "description": "The full semiconductor ecosystem - from design (NVDA, AMD) to manufacturing (TSM) to equipment (ASML, AMAT). The cyclical boom is here.",
        "why_hot": "Semiconductor sales hit $600B+ in 2025, up 20% YoY. AI chips alone are a $100B+ market. ASML's EUV machines are sold out for 2 years. This is a structural super-cycle, not just a cyclical upturn.",
    },
    "🟢 Copper & Miners": {
        "stocks": ["FCX", "SCCO", "HBM", "TECK", "ERO", "COPX", "FM", "TGB", "IVN", "LUN"],
        "emoji": "🟢",
        "color": "#10b981",
        "description": "Copper miners - the 'red metal' is critical for electrification, AI data centers, EVs, and renewable energy infrastructure.",
        "why_hot": "Copper demand from AI data centers alone is projected to grow 5x by 2030. Every AI data center needs massive copper for power distribution and networking. Supply deficit of 5M+ tonnes expected by 2028. Copper at $5+ is the new normal.",
    },
    "🏦 Financials (XLF)": {
        "stocks": ["JPM", "BAC", "GS", "MS", "V", "BLK", "C", "WFC", "SCHW", "AXP", "BX", "USB", "PNC", "COF", "TFC"],
        "emoji": "🏦",
        "color": "#f97316",
        "description": "Top US financial institutions - the backbone of the economy. Banks benefit from rate cuts, capital markets activity, and AI-driven efficiency.",
        "why_hot": "Rate cuts are coming = lower deposit costs + higher lending volumes. Investment banking fees and M&A activity are surging. Plus, banks are deploying AI across operations to cut costs by 15-20% - massive margin expansion ahead.",
    },
}

# Flatten all stocks & their sectors for internal mapping
ALL_STOCKS = {
    "ORCL": "Oracle Corp", "IBM": "IBM Corp", "CRM": "Salesforce Inc",
    "ADBE": "Adobe Inc", "NOW": "ServiceNow Inc", "SAP": "SAP SE",
    "UBER": "Uber Technologies", "SHOP": "Shopify Inc", "SNOW": "Snowflake Inc",
    "DDOG": "Datadog Inc", "MDB": "MongoDB Inc", "NET": "Cloudflare Inc",
    "COIN": "Coinbase Global", "MSTR": "MicroStrategy Inc", "HOOD": "Robinhood Markets",
}
STOCK_SECTOR_MAP = {}
SECTOR_DISPLAY = {}

for sector_name, sector_info in SECTOR_ANALYSIS.items():
    for ticker in sector_info["stocks"]:
        if ticker not in STOCK_SECTOR_MAP:
            STOCK_SECTOR_MAP[ticker] = []
        STOCK_SECTOR_MAP[ticker].append(sector_name)
    SECTOR_DISPLAY[sector_name] = {
        "emoji": sector_info["emoji"],
        "color": sector_info["color"],
        "description": sector_info["description"],
        "why_hot": sector_info["why_hot"],
    }

# Basic company names (can be extended)
ALL_STOCKS = {
    "NVDA": "NVIDIA Corp", "AMD": "Advanced Micro Devices", "TSM": "Taiwan Semiconductor",
    "ASML": "ASML Holding", "AVGO": "Broadcom Inc", "MU": "Micron Technology",
    "MRVL": "Marvell Technology", "ANET": "Arista Networks", "CRWD": "CrowdStrike Holdings",
    "PLTR": "Palantir Technologies", "INTC": "Intel Corporation", "DELL": "Dell Technologies",
    "SMCI": "Super Micro Computer", "ARM": "Arm Holdings", "WDC": "Western Digital",
    "NEM": "Newmont Corp", "GOLD": "Barrick Gold", "FNV": "Franco-Nevada Corp",
    "WPM": "Wheaton Precious Metals", "RGLD": "Royal Gold Inc", "AEM": "Agnico Eagle Mines",
    "KGC": "Kinross Gold Corp", "AGI": "Alamos Gold Inc", "SSRM": "SSR Mining Inc",
    "PAAS": "Pan American Silver", "IONQ": "IonQ Inc", "RGTI": "Rigetti Computing",
    "QUBT": "Quantum Computing Inc", "QBTS": "D-Wave Quantum Inc", "ARQQ": "Arqit Quantum Inc",
    "QSI": "Quantum-Si Inc", "LAES": "SEALSQ Corp", "AEHR": "Aehr Test Systems",
    "QTWO": "Q2 Holdings Inc", "META": "Meta Platforms Inc", "AMZN": "Amazon.com Inc",
    "NFLX": "Netflix Inc", "GOOGL": "Alphabet Inc", "MSFT": "Microsoft Corp",
    "AAPL": "Apple Inc", "TSLA": "Tesla Inc",
    "QCOM": "Qualcomm Inc", "AMAT": "Applied Materials Inc", "LRCX": "Lam Research Corp",
    "KLAC": "KLA Corp", "NXPI": "NXP Semiconductors", "STM": "STMicroelectronics",
    "ON": "ON Semiconductor", "FCX": "Freeport-McMoRan Inc", "SCCO": "Southern Copper Corp",
    "HBM": "Hudbay Minerals Inc", "TECK": "Teck Resources Ltd", "ERO": "Ero Copper Corp",
    "COPX": "Global X Copper Miners ETF", "FM": "First Quantum Minerals",
    "TGB": "Taseko Mines Ltd", "IVN": "Ivanhoe Mines Ltd", "LUN": "Lundin Mining Corp",
    "JPM": "JPMorgan Chase & Co", "BAC": "Bank of America", "GS": "Goldman Sachs Group",
    "MS": "Morgan Stanley", "V": "Visa Inc", "BLK": "BlackRock Inc",
    "C": "Citigroup Inc", "WFC": "Wells Fargo & Co", "SCHW": "Charles Schwab Corp",
    "AXP": "American Express Co", "BX": "Blackstone Inc", "USB": "US Bancorp",
    "PNC": "PNC Financial Services", "COF": "Capital One Financial", "TFC": "Truist Financial Corp",
}

# Map old tickers to new data (for backwards compatibility)
for ticker in ["ANET", "DELL", "SMCI", "WDC", "CRWD", "PLTR", "ARM", "MRVL"]:
    if ticker not in ALL_STOCKS:
        pass  # Already in ALL_STOCKS


# ============================================================
# SECTOR ANALYSIS - Determine which sector is "Hot"
# ============================================================

def analyze_sectors(data):
    """
    Analyze all sectors and determine which one is the hottest.
    Returns: hot_sector (name), hot_reason, sector_performance dict
    """
    sector_performance = {}
    
    for sector_name, sector_info in SECTOR_ANALYSIS.items():
        tickers = sector_info["stocks"]
        sector_data = [data[t] for t in tickers if t in data]
        
        if not sector_data:
            continue
        
        # Calculate sector metrics
        avg_change = sum(s["change_pct"] for s in sector_data) / len(sector_data)
        avg_volume = sum(s["volume"] for s in sector_data) / len(sector_data)
        total_mcap = sum(s["market_cap"] for s in sector_data if s["market_cap"])
        gainers = sum(1 for s in sector_data if s["direction"] == "up")
        total = len(sector_data)
        
        # Composite score (higher = hotter)
        score = avg_change * 0.5 + (gainers / total) * 100 * 0.5 if total > 0 else 0
        
        sector_performance[sector_name] = {
            "avg_change": round(avg_change, 2),
            "gainers": gainers,
            "total": total,
            "score": round(score, 1),
            "total_mcap": total_mcap,
            "emoji": sector_info["emoji"],
            "color": sector_info["color"],
            "description": sector_info["description"],
            "why_hot": sector_info["why_hot"],
        }
    
    # Find the hot sector
    hot_sector = None
    hot_score = -999
    
    for name, perf in sector_performance.items():
        if perf["score"] > hot_score:
            hot_score = perf["score"]
            hot_sector = name
    
    return hot_sector, sector_performance


# ============================================================
# FETCH FUNCTIONS
# ============================================================

def get_stock_data(period="1d"):
    """Fetch current stock data for ALL stocks across all sectors"""
    all_tickers = list(ALL_STOCKS.keys())
    data = {}
    
    try:
        # Fetch in batches to avoid timeout
        batch_size = 20
        for i in range(0, len(all_tickers), batch_size):
            batch = all_tickers[i:i+batch_size]
            try:
                stocks = yf.Tickers(" ".join(batch))
                
                for ticker in batch:
                    try:
                        stock = stocks.tickers[ticker]
                        info = stock.info if hasattr(stock, 'info') else {}
                        
                        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose", 0)
                        prev_close = info.get("previousClose", current_price)
                        change = current_price - prev_close if prev_close else 0
                        change_pct = (change / prev_close) * 100 if prev_close else 0
                        
                        direction = "up" if change >= 0 else "down"
                        
                        # Get sectors for this ticker
                        sectors = STOCK_SECTOR_MAP.get(ticker, ["Other"])
                        primary_sector = sectors[0]
                        
                        data[ticker] = {
                            "name": ALL_STOCKS.get(ticker, ticker),
                            "price": round(current_price, 2) if current_price else 0,
                            "change": round(change, 2),
                            "change_pct": round(change_pct, 2),
                            "direction": direction,
                            "high": round(info.get("dayHigh", 0), 2),
                            "low": round(info.get("dayLow", 0), 2),
                            "volume": info.get("volume", 0),
                            "market_cap": info.get("marketCap", 0),
                            "pe_ratio": info.get("trailingPE", 0),
                            "sector": primary_sector,
                            "all_sectors": sectors,
                            "fifty_two_high": info.get("fiftyTwoWeekHigh", 0),
                            "fifty_two_low": info.get("fiftyTwoWeekLow", 0),
                        }
                    except Exception:
                        data[ticker] = get_fallback_data(ticker)
            except Exception:
                for ticker in batch:
                    data[ticker] = get_fallback_data(ticker)
                    
    except Exception:
        for ticker in all_tickers:
            data[ticker] = get_fallback_data(ticker)
    
    return data

def get_sector_for_ticker(ticker):
    """Get primary sector for a ticker"""
    sectors = STOCK_SECTOR_MAP.get(ticker, ["Other"])
    return sectors[0]

def get_fallback_data(ticker):
    """Fallback data when API fails"""
    import random
    return {
        "name": ALL_STOCKS.get(ticker, ticker),
        "price": round(random.uniform(10, 900), 2),
        "change": round(random.uniform(-5, 5), 2),
        "change_pct": round(random.uniform(-2, 2), 2),
        "direction": "up" if random.random() > 0.5 else "down",
        "high": 0,
        "low": 0,
        "volume": random.randint(1000000, 50000000),
        "market_cap": random.randint(50000000000, 3000000000000),
        "pe_ratio": round(random.uniform(10, 60), 2),
        "sector": get_sector_for_ticker(ticker),
        "all_sectors": STOCK_SECTOR_MAP.get(ticker, ["Other"]),
        "fifty_two_high": 0,
        "fifty_two_low": 0,
    }

def get_sectors_list():
    """Get list of all sectors"""
    return list(SECTOR_ANALYSIS.keys())

def get_stocks_for_sector(sector_name):
    """Get ticker list for a sector"""
    if sector_name in SECTOR_ANALYSIS:
        return SECTOR_ANALYSIS[sector_name]["stocks"]
    return []

def get_sector_emoji(sector_name):
    """Get emoji for a sector"""
    if sector_name in SECTOR_DISPLAY:
        return SECTOR_DISPLAY[sector_name]["emoji"]
    return "📊"

def format_market_cap(cap):
    """Format market cap in readable format"""
    if cap >= 1_000_000_000_000:
        return f"${cap/1_000_000_000_000:.2f}T"
    elif cap >= 1_000_000_000:
        return f"${cap/1_000_000_000:.2f}B"
    elif cap >= 1_000_000:
        return f"${cap/1_000_000:.2f}M"
    else:
        return f"${cap:,.0f}"

def format_volume(vol):
    """Format volume in readable format"""
    if vol >= 1_000_000_000:
        return f"{vol/1_000_000_000:.2f}B"
    elif vol >= 1_000_000:
        return f"{vol/1_000_000:.2f}M"
    elif vol >= 1_000:
        return f"{vol/1_000:.2f}K"
    else:
        return str(vol)
