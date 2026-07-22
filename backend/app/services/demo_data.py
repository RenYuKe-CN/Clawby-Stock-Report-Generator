"""Demo data generator — produces realistic-looking stock data when Clawby API key is invalid."""

from __future__ import annotations

import math
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any

random.seed(42)  # Deterministic demo data

# Known stock reference prices (approximate)
STOCK_PRICES: dict[str, float] = {
    "AAPL": 245.0, "MSFT": 450.0, "GOOGL": 180.0, "AMZN": 200.0,
    "NVDA": 130.0, "TSLA": 250.0, "META": 520.0, "SPY": 560.0,
    "QQQ": 490.0, "AMD": 160.0, "INTC": 30.0, "PLTR": 35.0,
}

DEFAULT_PRICE = 100.0


def _base_price(ticker: str) -> float:
    return STOCK_PRICES.get(ticker.upper(), DEFAULT_PRICE)


def random_date(days_ago: int) -> str:
    d = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return d.strftime("%Y-%m-%d")


def unix_seconds(days_ago: int) -> int:
    return int((datetime.now(timezone.utc) - timedelta(days=days_ago)).timestamp())


def gen_bars(ticker: str, days: int = 365) -> list[dict[str, Any]]:
    """Generate daily OHLC bars that look realistic."""
    base = _base_price(ticker)
    price = base * 0.85  # Start 15% below current
    bars: list[dict[str, Any]] = []
    for i in range(days):
        daily_change = random.gauss(0.001, 0.025)  # Mean +0.1%, std 2.5%
        if i > 0 and i % 20 == 0:
            # Occasional trend shift
            daily_change += random.gauss(0.005, 0.02)
        open_p = price
        close_p = open_p * (1 + daily_change)
        high_p = max(open_p, close_p) * (1 + random.uniform(0, 0.03))
        low_p = min(open_p, close_p) * (1 - random.uniform(0, 0.03))
        volume = int(random.uniform(10_000_000, 100_000_000))
        bars.append({
            "t": unix_seconds(days - 1 - i),
            "date": random_date(days - 1 - i),
            "o": round(open_p, 2),
            "h": round(high_p, 2),
            "l": round(low_p, 2),
            "c": round(close_p, 2),
            "v": volume,
        })
        price = close_p
    bars.reverse()
    return bars


def gen_short_volume(ticker: str) -> list[dict[str, Any]]:
    """Generate short volume data."""
    base_vol = random.randint(20_000_000, 80_000_000)
    result = []
    for i in range(60):
        date = random_date(i)
        total = int(base_vol * random.uniform(0.7, 1.3))
        short_pct = random.uniform(0.02, 0.10)
        short_vol = int(total * short_pct)
        result.append({
            "date": date,
            "rt": total,
            "st": short_vol,
            "lt": total - short_vol,
        })
    return result


def gen_short_interest(ticker: str) -> list[dict[str, Any]]:
    """Generate short interest data."""
    base = _base_price(ticker)
    shares = int(random.uniform(500_000_000, 5_000_000_000))
    result = []
    for i in range(10):
        date = random_date(i * 14)  # Bi-weekly
        si_shares = int(shares * random.uniform(0.01, 0.08))
        result.append({
            "date": date,
            "shares_short": si_shares,
            "short_pct": round(si_shares / shares * 100, 2),
            "days_to_cover": round(random.uniform(0.5, 5), 1),
        })
    return result


def gen_daily_short_interest(ticker: str) -> list[dict[str, Any]]:
    base = _base_price(ticker)
    shares = int(random.uniform(500_000_000, 5_000_000_000))
    result = []
    for i in range(30):
        date = random_date(i)
        si = int(shares * random.uniform(0.01, 0.06))
        result.append({"date": date, "shares_short": si, "short_pct": round(si / shares * 100, 2)})
    return result


def gen_borrow_fee(ticker: str) -> list[dict[str, Any]]:
    result = []
    for i in range(60):
        date = random_date(i)
        fee = round(random.uniform(0.2, 5.0), 2)
        result.append({"timestamp": date, "borrow_rate": fee, "available": random.randint(100_000, 10_000_000)})
    return result


def gen_ftds(ticker: str) -> list[dict[str, Any]]:
    result = []
    for i in range(30):
        date = random_date(i)
        fails = int(random.uniform(100_000, 5_000_000))
        result.append({"date": date, "fails": fails, "noti": round(fails * _base_price(ticker), 0)})
    return result


def gen_short_all(ticker: str) -> dict[str, Any]:
    return {
        "short_volume": gen_short_volume(ticker),
        "short_interest": gen_short_interest(ticker),
        "daily_short_interest": gen_daily_short_interest(ticker),
        "borrow_fee": gen_borrow_fee(ticker),
        "ftds": gen_ftds(ticker),
    }


def gen_darkpool(ticker: str, date: str | None = None) -> dict[str, Any]:
    base = _base_price(ticker)
    if date is None:
        date = random_date(0)
    levels = []
    for offset in range(-15, 16):
        level_price = base + offset * (base * 0.01)
        vol = int(random.uniform(10_000, 500_000))
        levels.append({"price": str(round(level_price, 2)), "volume": vol, "trades": max(1, vol // 5000)})
    return {"levels": levels, "summary": {"total_volume": sum(l["volume"] for l in levels), "trade_count": len(levels), "date": date}}


def gen_options_chain(ticker: str) -> dict[str, Any]:
    base = _base_price(ticker)
    expiration = (datetime.now(timezone.utc) + timedelta(days=35)).strftime("%Y-%m-%d")
    chain = []
    for offset in range(-12, 13):
        strike = base + offset * (base * 0.05)
        call_oi = int(random.uniform(5_000, 100_000))
        put_oi = int(random.uniform(5_000, 100_000))
        chain.append({
            "strike": round(strike, 2),
            "strike_price": round(strike, 2),
            "call_open_interest": call_oi,
            "call_oi": call_oi,
            "put_open_interest": put_oi,
            "put_oi": put_oi,
            "call_volume": int(call_oi * random.uniform(0.1, 0.5)),
            "put_volume": int(put_oi * random.uniform(0.1, 0.5)),
        })
    return {"underlying": f"US:{ticker}", "expiration": expiration, "chain": chain, "max_pain": round(base, 2)}


def gen_corporate(ticker: str) -> dict[str, Any]:
    dividends = []
    for q in range(8):
        ex_date = random_date(q * 91)
        pay_date = random_date(q * 91 - 14)
        amount = round(random.uniform(0.2, 1.5), 4)
        dividends.append({"ex_date": ex_date, "pay_date": pay_date, "amount": amount})
    splits = []
    splits.append({"date": random_date(365 * 4), "ratio": "4:1", "to_factor": "0.25"})
    float_data = []
    for i in range(5):
        date = random_date(i * 180)
        shares = int(random.uniform(1_000_000_000, 10_000_000_000))
        float_shares = int(shares * random.uniform(0.85, 0.98))
        float_data.append({"date": date, "shares_outstanding": shares, "float": float_shares})
    return {"dividends": dividends, "splits": splits, "float_history": float_data}


def gen_financials(ticker: str) -> dict[str, Any]:
    base = _base_price(ticker)
    revenue_base = base * random.uniform(0.5, 2.0) * 1_000_000_000
    result: dict[str, Any] = {"company_name": f"{ticker} Inc."}
    revenues = []
    net_incomes = []
    eps_list = []
    for q in range(8):
        fy = 2024 + q // 4
        fp = q % 4 + 1
        rev = revenue_base * (1 + q * 0.03 + random.uniform(-0.05, 0.05))
        ni = rev * random.uniform(0.1, 0.25)
        eps = ni / random.uniform(1_000_000_000, 5_000_000_000)
        revenues.append({"fy": fy, "fp": f"Q{fp}", "value": round(rev, 0)})
        net_incomes.append({"fy": fy, "fp": f"Q{fp}", "value": round(ni, 0)})
        eps_list.append({"fy": fy, "fp": f"Q{fp}", "value": round(eps, 2)})
    result["revenue"] = revenues
    result["net_income"] = net_incomes
    result["eps"] = eps_list
    result["assets"] = [{"fy": 2024, "value": round(revenue_base * random.uniform(1.5, 3.0), 0)}]
    result["equity"] = [{"fy": 2024, "value": round(revenue_base * random.uniform(0.8, 1.5), 0)}]
    return result


def gen_sentiment(ticker: str) -> dict[str, Any]:
    mentions = []
    for i in range(30):
        date = random_date(i)
        count = int(random.uniform(10, 500))
        mentions.append({"date": date, "count": count, "title": f"Discussion about {ticker}", "subreddit": "wallstreetbets"})
    daily = []
    for i in range(30):
        date = random_date(i)
        daily.append({"date": date, "count": int(random.uniform(50, 800))})
    return {"mentions": mentions, "daily_counts": daily}


def gen_exchange_volume(ticker: str) -> list[dict[str, Any]]:
    result = []
    for i in range(10):
        date = random_date(i)
        total = int(random.uniform(30_000_000, 80_000_000))
        result.append({
            "date": date,
            "xnas": int(total * 0.45),
            "xny": int(total * 0.35),
            "xbats": int(total * 0.15),
            "xotc": int(total * 0.05),
        })
    return result
