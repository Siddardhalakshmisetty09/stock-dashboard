import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# STOCK CORRELATION ENGINE
# Shows which stocks move together and their relationships
# ============================================================

# Predefined strong correlations (known relationships)
KNOWN_CORRELATIONS = {
    "NVDA": {
        "AMD": {"strength": 0.72, "reason": "Both are AI chip designers - direct competitors"},
        "TSM": {"strength": 0.68, "reason": "TSM manufactures NVDA's chips"},
        "AVGO": {"strength": 0.65, "reason": "Both benefit from AI networking & compute"},
        "SMCI": {"strength": 0.70, "reason": "SMCI builds NVDA-based AI servers"},
    },
    "AMD": {
        "NVDA": {"strength": 0.72, "reason": "Direct AI chip competitors"},
        "INTC": {"strength": 0.55, "reason": "CPU competitors - both x86"},
        "TSM": {"strength": 0.62, "reason": "TSM manufactures AMD chips"},
    },
    "TSM": {
        "NVDA": {"strength": 0.68, "reason": "NVDA's primary chip manufacturer"},
        "AMD": {"strength": 0.62, "reason": "AMD's chip manufacturer"},
        "ASML": {"strength": 0.60, "reason": "ASML supplies chip-making machines"},
    },
    "ASML": {
        "TSM": {"strength": 0.60, "reason": "TSM is ASML's biggest customer"},
        "INTC": {"strength": 0.55, "reason": "Intel uses ASML's EUV machines"},
        "AMAT": {"strength": 0.56, "reason": "Both are semiconductor equipment makers"},
    },
    "AVGO": {
        "NVDA": {"strength": 0.65, "reason": "Both power AI data centers"},
        "MRVL": {"strength": 0.61, "reason": "Competitors in networking & custom chips"},
        "ANET": {"strength": 0.58, "reason": "Arista uses Broadcom chips in switches"},
    },
    "MU": {
        "NVDA": {"strength": 0.60, "reason": "HBM memory supplier for NVIDIA GPUs"},
        "WDC": {"strength": 0.52, "reason": "Memory & storage competitors"},
    },
    "META": {
        "NVDA": {"strength": 0.64, "reason": "Meta is NVIDIA's largest customer for AI"},
        "GOOGL": {"strength": 0.55, "reason": "Direct competitors in digital ads"},
        "AMZN": {"strength": 0.58, "reason": "Cloud & AI competitors"},
    },
    "GOOGL": {
        "META": {"strength": 0.55, "reason": "Digital ad competitors"},
        "MSFT": {"strength": 0.52, "reason": "Cloud & AI competitors"},
        "NVDA": {"strength": 0.50, "reason": "Google uses NVIDIA for cloud AI"},
    },
    "MSFT": {
        "GOOGL": {"strength": 0.52, "reason": "Cloud competitors (Azure vs GCP)"},
        "AMZN": {"strength": 0.50, "reason": "Cloud competitors (Azure vs AWS)"},
        "NVDA": {"strength": 0.62, "reason": "Microsoft's biggest AI infrastructure partner"},
    },
    "AMZN": {
        "MSFT": {"strength": 0.50, "reason": "Cloud competitors"},
        "META": {"strength": 0.58, "reason": "Digital ad & cloud competitors"},
        "NVDA": {"strength": 0.60, "reason": "AWS uses NVIDIA for AI inference"},
    },
    "NEM": {
        "GOLD": {"strength": 0.78, "reason": "Both are top gold miners"},
        "FNV": {"strength": 0.65, "reason": "Franco-Nevada finances mining operations"},
        "AEM": {"strength": 0.72, "reason": "Canadian gold miners"},
    },
    "GOLD": {
        "NEM": {"strength": 0.78, "reason": "Top gold mining competitors"},
        "KGC": {"strength": 0.70, "reason": "Both operate in Americas"},
    },
    "FCX": {
        "SCCO": {"strength": 0.68, "reason": "Both are major copper producers"},
        "TECK": {"strength": 0.62, "reason": "Copper mining peers"},
        "HBM": {"strength": 0.55, "reason": "Copper producers"},
    },
    "JPM": {
        "BAC": {"strength": 0.82, "reason": "Biggest US banks - move together"},
        "GS": {"strength": 0.70, "reason": "Investment banking peers"},
        "MS": {"strength": 0.68, "reason": "Wall Street peers"},
    },
    "BAC": {
        "JPM": {"strength": 0.82, "reason": "Top US banks"},
        "WFC": {"strength": 0.75, "reason": "Large cap US banks"},
        "C": {"strength": 0.72, "reason": "Money center banks"},
    },
}

# Stock descriptions (1-liner)
STOCK_DESCRIPTIONS = {
    "NVDA": "World leader in AI chips & GPUs - powers 90% of AI training",
    "AMD": "Intel & NVIDIA's biggest competitor in CPUs, GPUs, and AI accelerators",
    "TSM": "World's largest semiconductor foundry - makes chips for NVDA, AMD, AAPL",
    "ASML": "Monopoly on EUV lithography machines - essential for making advanced chips",
    "AVGO": "Data center & networking chip giant - ASICs for AI, switches, storage",
    "MU": "Leading memory chip maker - HBM memory critical for AI GPUs",
    "MRVL": "Custom silicon & data infrastructure chips for AI & cloud",
    "ANET": "Top AI data center networking switches - used by hyperscalers",
    "CRWD": "AI-powered cybersecurity leader - cloud-native endpoint protection",
    "PLTR": "AI data platforms for government & enterprise - Gotham & Foundry",
    "INTC": "Legacy CPU giant pivoting to AI chips & foundry services",
    "DELL": "Top AI server manufacturer - powers enterprise AI deployments",
    "SMCI": "High-growth AI server maker - liquid cooling leader for data centers",
    "ARM": "UK chip designer - 99% of smartphone CPUs, expanding to AI & servers",
    "WDC": "Data storage leader - HDDs & SSDs for AI data centers",
    "NEM": "World's largest gold miner - operations across Americas, Africa",
    "GOLD": "Major gold miner with low-cost operations in Americas & Africa",
    "FNV": "Gold royalty & streaming giant - funds miners in exchange for gold",
    "WPM": "Precious metals streaming company - buys gold/silver from miners",
    "RGLD": "Gold royalty company with diversified precious metals portfolio",
    "AEM": "Canadian gold miner with high-margin operations in Canada & Finland",
    "KGC": "Mid-tier gold miner with growing production in Americas",
    "AGI": "Canadian gold miner with assets in Americas & Turkey",
    "PAAS": "Top silver & gold miner with operations in Americas",
    "IONQ": "Trapped-ion quantum computing leader - first public pure-play quantum",
    "RGTI": "Superconducting quantum computing - building scalable quantum systems",
    "QUBT": "Quantum computing hardware & software for optimization problems",
    "QBTS": "D-Wave - quantum annealing pioneer for commercial applications",
    "META": "Social media giant betting big on AI - largest Llama model developer",
    "AMZN": "E-commerce & cloud leader - AWS AI growing 40%+ annually",
    "NFLX": "Streaming giant using AI for content recommendations and production",
    "GOOGL": "Search giant with Gemini AI - competing aggressively in AI race",
    "MSFT": "Software giant with OpenAI partnership - Azure AI is main growth driver",
    "AAPL": "Consumer tech giant - building AI into iPhone ecosystem (Apple Intelligence)",
    "TSLA": "EV & autonomous driving leader - Dojo AI supercomputer for self-driving",
    "QCOM": "Mobile chip leader - AI chips in phones, auto, IoT",
    "AMAT": "Largest semiconductor equipment maker - supplies all chip fabs",
    "LRCX": "Semiconductor etching equipment leader",
    "KLAC": "Semiconductor inspection & measurement equipment leader",
    "FCX": "World's largest public copper producer - Freeport-McMoRan",
    "SCCO": "Low-cost copper producer with operations in Peru & Mexico",
    "HBM": "Copper & gold miner with growing production in Americas",
    "TECK": "Diversified miner - copper, steelmaking coal, zinc",
    "JPM": "Largest US bank by assets - diversified financial powerhouse",
    "BAC": "Second largest US bank - massive consumer & corporate banking",
    "GS": "Top investment bank - trading, M&A advisory, wealth management",
    "MS": "Leading investment bank & wealth manager - institutional focus",
    "V": "Global payments network - processes 65% of non-cash transactions",
    "BLK": "World's largest asset manager - $10T+ AUM on Aladdin platform",
}

# Stock details for popup
STOCK_DETAILS = {
    ticker: {
        "description": desc,
        "sector_hint": "Check dashboard for full data",
    }
    for ticker, desc in STOCK_DESCRIPTIONS.items()
}

def get_correlations(ticker, data=None):
    """Get known correlations for a stock"""
    known = KNOWN_CORRELATIONS.get(ticker, {})
    
    if not known:
        # Try to find if any other stock has this as a correlated pair
        for stock, corrs in KNOWN_CORRELATIONS.items():
            if ticker in corrs:
                known[stock] = corrs[ticker]
    
    return known

def get_stock_summary(ticker, data=None):
    """Get a concise 1-line summary + avg volume for a stock"""
    desc = STOCK_DESCRIPTIONS.get(ticker, "No description available")
    
    avg_vol = ""
    avg_volume_num = 0
    
    if data and ticker in data:
        price = data[ticker].get("price", 0)
        change = data[ticker].get("change_pct", 0)
        volume = data[ticker].get("volume", 0)
        
        # Format volume
        if volume >= 1_000_000_000:
            avg_vol = f"{volume/1_000_000_000:.1f}B"
            avg_volume_num = volume
        elif volume >= 1_000_000:
            avg_vol = f"{volume/1_000_000:.1f}M"
            avg_volume_num = volume
        elif volume >= 1_000:
            avg_vol = f"{volume/1_000:.1f}K"
            avg_volume_num = volume
        else:
            avg_vol = str(volume)
            avg_volume_num = volume
        
        return {
            "description": desc,
            "price": price,
            "change_pct": change,
            "volume_str": avg_vol,
            "volume_num": avg_volume_num,
        }
    
    return {
        "description": desc,
        "price": 0,
        "change_pct": 0,
        "volume_str": "N/A",
        "volume_num": 0,
    }

def search_stocks(query, data=None):
    """Search for stocks by ticker or name"""
    query = query.upper().strip()
    if not query or len(query) < 1:
        return []
    
    results = []
    
    # Search by ticker
    for ticker, name in STOCK_DESCRIPTIONS.items():
        if query in ticker.upper() or query in name.upper():
            summary = get_stock_summary(ticker, data)
            results.append({
                "ticker": ticker,
                "name": name,
                "description": summary["description"],
                "price": summary["price"],
                "change_pct": summary["change_pct"],
                "volume_str": summary["volume_str"],
            })
    
    # Sort by relevance (exact match first)
    results.sort(key=lambda x: (
        0 if x["ticker"] == query else 1 if x["ticker"].startswith(query) else 2 if query in x["ticker"] else 3
    ))
    
    return results[:10]  # Max 10 results

def get_sector_context(sector_name, data=None):
    """Get context about why a sector is up or down"""
    from data_fetcher import SECTOR_ANALYSIS, get_stocks_for_sector, format_market_cap
    
    if sector_name not in SECTOR_ANALYSIS:
        return None
    
    sector_info = SECTOR_ANALYSIS[sector_name]
    tickers = sector_info["stocks"]
    
    sector_data = [data[t] for t in tickers if t in data]
    if not sector_data:
        return None
    
    avg_change = sum(s["change_pct"] for s in sector_data) / len(sector_data)
    gainers = sum(1 for s in sector_data if s["direction"] == "up")
    top_stock = max(sector_data, key=lambda s: abs(s["change_pct"]))
    
    # Generate context
    if avg_change > 0:
        mood = "🚀 Bullish"
        reason = "green energy across the sector"
    else:
        mood = "📉 Pullback"
        reason = "profit-taking or market-wide selling"
    
    context = {
        "mood": mood,
        "avg_change": avg_change,
        "gainers": f"{gainers}/{len(sector_data)}",
        "description": sector_info["description"],
        "why_hot": sector_info.get("why_hot", ""),
        "top_mover": {
            "ticker": top_stock["name"].split()[0] if top_stock else "",
            "change": top_stock["change_pct"],
        },
        "key_drivers": _get_sector_drivers(sector_name, avg_change),
    }
    
    return context

def _get_sector_drivers(sector_name, avg_change):
    """Get specific reasons for sector movement"""
    drivers = []
    
    if "Gold" in sector_name or "gold" in sector_name:
        if avg_change > 0:
            drivers = [
                "📈 Gold prices rising on rate cut expectations",
                "🏦 Central banks continuing gold purchases",
                "💵 USD weakening - gold inversely correlated",
                "🌍 Geopolitical uncertainty boosting safe haven demand",
            ]
        else:
            drivers = [
                "📉 Profit-taking after recent gold rally",
                "💵 USD strengthening temporarily",
                "📊 Higher bond yields competing with gold",
            ]
    
    elif "AI" in sector_name or "Backbone" in sector_name:
        if avg_change > 0:
            drivers = [
                "🤖 AI CAPEX spending continues to accelerate",
                "💼 Major tech earnings beating estimates",
                "🏭 New AI chip launches driving demand",
                "📈 Hyperscaler data center buildout at record pace",
            ]
        else:
            drivers = [
                "📉 Rotation out of tech into value sectors",
                "📊 Profit-taking after strong AI rally",
                "🔍 Regulatory concerns over AI safety",
            ]
    
    elif "Quantum" in sector_name:
        if avg_change > 0:
            drivers = [
                "🔬 Quantum supremacy milestones announced",
                "💰 Government funding ($5B+) flowing into quantum R&D",
                "🏢 Major tech partnerships announced",
            ]
        else:
            drivers = [
                "📉 High volatility in small-cap quantum stocks",
                "📊 No near-term revenue - speculative selling",
            ]
    
    elif "FANGMAN" in sector_name:
        if avg_change > 0:
            drivers = [
                "📈 Mega-cap tech earnings beating expectations",
                "🤖 AI monetization driving revenue growth",
                "💰 Share buybacks supporting stock prices",
            ]
        else:
            drivers = [
                "📉 Regulatory headwinds (antitrust, AI regulation)",
                "📊 Rotation to value/defensive sectors",
                "📈 Rising bond yields pressuring growth stocks",
            ]
    
    elif "Semi" in sector_name:
        if avg_change > 0:
            drivers = [
                "🖥️ Chip demand at all-time high ($600B market)",
                "🏭 AI chip orders boosting fab utilization",
                "🔧 EUV machines sold out for 2+ years",
            ]
        else:
            drivers = [
                "📉 Cyclical semiconductor correction fears",
                "📊 Trade tensions with China impacting outlook",
                "💼 Inventory adjustments in non-AI chips",
            ]
    
    elif "Copper" in sector_name or "copper" in sector_name:
        if avg_change > 0:
            drivers = [
                "🟢 Copper prices rising on supply deficit fears",
                "🏭 AI data centers driving massive copper demand",
                "🚗 EV adoption accelerating copper consumption",
            ]
        else:
            drivers = [
                "📉 China demand concerns weighing on copper",
                "📊 Global manufacturing slowdown fears",
                "💵 Strong USD pressuring commodity prices",
            ]
    
    elif "Financial" in sector_name or "XLF" in sector_name:
        if avg_change > 0:
            drivers = [
                "🏦 Rate cuts expected - lower deposit costs + higher lending",
                "📈 Investment banking fees surging",
                "🤖 Banks deploying AI to cut costs 15-20%",
            ]
        else:
            drivers = [
                "📉 Yield curve inversion concerns",
                "📊 Loan loss provisions increasing",
                "💰 Regulatory capital requirements tightening",
            ]
    
    else:
        drivers = [
            "📊 Sector moving with overall market trends",
            "📈 Sector-specific news driving sentiment",
        ]
    
    return drivers[:3]  # Max 3 drivers
