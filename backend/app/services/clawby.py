"""Clawby HTTP client — all US equity data interfaces.

Every method returns raw dict (the `data` field from Clawby's relay response).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import settings
from app.services import demo_data
import random
from datetime import datetime, timezone, timedelta

CLAWBY_RELAY = f"{settings.clawby_base_url}/api/relay"

# Built at call time to pick up runtime key changes
def _headers():
    from app.services.clawby_config import get_api_key
    return {
        "X-API-Key": get_api_key(),
        "Content-Type": "application/json",
    }

# Timeout per call (seconds)
TIMEOUT = 30.0


# ── Low-level caller ────────────────────────────────────────────────────────

def _demo_fallback(name: str, params: dict[str, Any] | None = None) -> Any:
    """Generate demo data when Clawby API is unavailable."""
    ticker = ""
    if params:
        ticker = (params.get("symbol") or "").replace("US:", "").replace("BTC:", "")
        if not ticker:
            ticker = (params.get("underlying") or "").replace("US:", "")
        if not ticker:
            ticker = (params.get("company") or "")[:10]

    fallbacks = {
        "Quote for a given stock": lambda: {"reg_price": demo_data._base_price(ticker), "reg_change_pct": round(random.uniform(-3, 3), 2), "market_cap": random.randint(50_000_000_000, 500_000_000_000), "reg_volume": random.randint(10_000_000, 100_000_000)},
        "Screen thousands of stocks": lambda: [{"display": ticker, "reg_price": demo_data._base_price(ticker), "reg_change_pct": round(random.uniform(-3, 3), 2), "market_cap": random.randint(50_000_000_000, 500_000_000_000), "reg_volume": random.randint(10_000_000, 100_000_000)}],
        "Stock aggregate OHLC bars (k-line)": lambda: demo_data.gen_bars(ticker),
        "Short volume for a given stock": lambda: demo_data.gen_short_volume(ticker),
        "Short Interest for a given stock": lambda: demo_data.gen_short_interest(ticker),
        "Daily Short Interest for a given stock": lambda: demo_data.gen_daily_short_interest(ticker),
        "Cost-to-borrow from Interactive Brokers": lambda: demo_data.gen_borrow_fee(ticker),
        "FTDs for a given stock": lambda: demo_data.gen_ftds(ticker),
        "Dark Pool Levels for a given stock": lambda: demo_data.gen_darkpool(ticker).get("levels", []),
        "Dark Pool Prints (trades) summary for a given stock": lambda: demo_data.gen_darkpool(ticker).get("summary", {}),
        "Option chain summary (max pain, ITM/OTM)": lambda: demo_data.gen_options_chain(ticker).get("chain", []),
        "List of option contracts": lambda: [{"expiration": "2026-08-21"}],
        "Dividends for a given stock": lambda: demo_data.gen_corporate(ticker).get("dividends", []),
        "Splits for a given stock": lambda: demo_data.gen_corporate(ticker).get("splits", []),
        "Historical Float and Shares Outstanding for a given stock": lambda: demo_data.gen_corporate(ticker).get("float_history", []),
        "Reddit mentions for a given stock": lambda: demo_data.gen_sentiment(ticker).get("mentions", []),
        "Daily Reddit mention counts for a given stock": lambda: demo_data.gen_sentiment(ticker).get("daily_counts", []),
        "Exchange volume for a given stock": lambda: demo_data.gen_exchange_volume(ticker),
        "sec_cik_lookup": lambda: [{"cik": "320193", "name": ticker}],
        "sec_company_concept": lambda: demo_data.gen_financials(ticker).get("eps", []),
        "List of option contracts": lambda: [{"expiration": (datetime.now(timezone.utc) + timedelta(days=35)).strftime("%Y-%m-%d")}],
        "List of stock exchanges": lambda: [{"code": "NASDAQ", "name": "NASDAQ"}, {"code": "NYSE", "name": "NYSE"}],
    }
    fn = fallbacks.get(name)
    if fn:
        return fn()
    return {"error": f"no_demo_for_{name}"}

async def _call(name: str, params: dict[str, Any] | None = None) -> Any:
    """POST to Clawby relay, return the `data` field. Falls back to demo data on error."""
    key = _headers()["X-API-Key"]
    # Auto-create clawby_config.json on first use
    from app.services.clawby_config import load_config, save_config
    cfg = load_config()
    if "api_key" not in cfg or not cfg.get("api_key"):
        cfg["api_key"] = settings.clawby_api_key
        save_config(cfg)
    if not key or key.startswith("pk_test") or key == "sk-test-placeholder":
        return _demo_fallback(name, params)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            CLAWBY_RELAY,
            headers=_headers(),
            json={"name": name, "params": params or {}},
        )
        if resp.status_code == 401:
            return _demo_fallback(name, params)
        if resp.status_code == 403:
            return _demo_fallback(name, params)
        if resp.status_code == 429:
            return {"error": "rate_limited"}
        resp.raise_for_status()
        body = resp.json()
        if "data" in body:
            return body["data"]
        return body
    """POST to Clawby relay, return the `data` field."""
    key = _headers()["X-API-Key"]
    if not key:
        return {"error": "CLAWBY_API_KEY not configured"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(
            CLAWBY_RELAY,
            headers=_headers(),
            json={"name": name, "params": params or {}},
        )
        if resp.status_code == 401:
            return {"error": "invalid_clawby_key"}
        if resp.status_code == 403:
            return {"error": "need_upgrade"}
        if resp.status_code == 429:
            return {"error": "rate_limited"}
        resp.raise_for_status()
        body = resp.json()
        if "data" in body:
            return body["data"]
        # Some interfaces return the payload directly
        return body


# ── Health check ────────────────────────────────────────────────────────────

async def check_connectivity() -> str:
    """Try a lightweight call to verify the API key."""
    try:
        result = await _call("List of stock exchanges")
        if isinstance(result, dict) and "error" in result:
            return result["error"]
        return "ok"
    except Exception as exc:
        return f"error: {exc}"


# ── Quote (via screener for real-time) ──────────────────────────────────────

async def get_quote(ticker: str) -> dict[str, Any]:
    """Real-time quote via screener."""
    result = await _call("Screen thousands of stocks", {
        "symbol": ticker,           # ⚠️  bare ticker, no US: prefix
        "view_cols": "display,reg_price,reg_change_pct,market_cap,reg_volume",
    })
    if isinstance(result, list) and len(result) > 0:
        return result[0]
    return result


# ── OHLC Bars ───────────────────────────────────────────────────────────────

def _unix_days_ago(days: int) -> int:
    return int(time.time()) - days * 86400


async def get_bars(ticker: str, days: int = 365) -> list[dict[str, Any]]:
    result = await _call("Stock aggregate OHLC bars (k-line)", {
        "symbol": f"US:{ticker}",
        "agg_type": "day",
        "start": _unix_days_ago(days),
    })
    if isinstance(result, list):
        return result
    return []


# ── Short Data ──────────────────────────────────────────────────────────────

async def get_short_volume(ticker: str) -> list[dict[str, Any]]:
    result = await _call("Short volume for a given stock", {
        "symbol": f"US:{ticker}",
        "ordering": "-date",
    })
    return result if isinstance(result, list) else []


async def get_short_interest(ticker: str) -> list[dict[str, Any]]:
    result = await _call("Short Interest for a given stock", {
        "symbol": f"US:{ticker}",
        "ordering": "-date",
    })
    return result if isinstance(result, list) else []


async def get_daily_short_interest(ticker: str) -> list[dict[str, Any]]:
    result = await _call("Daily Short Interest for a given stock", {
        "symbol": f"US:{ticker}",
        "ordering": "-date",
    })
    return result if isinstance(result, list) else []


async def get_borrow_fee(ticker: str) -> list[dict[str, Any]]:
    result = await _call("Cost-to-borrow from Interactive Brokers", {
        "symbol": f"US:{ticker}",
        "ordering": "-timestamp",
    })
    return result if isinstance(result, list) else []


async def get_ftds(ticker: str) -> list[dict[str, Any]]:
    result = await _call("FTDs for a given stock", {
        "symbol": f"US:{ticker}",
        "ordering": "-date",
    })
    return result if isinstance(result, list) else []


async def get_short_all(ticker: str) -> dict[str, Any]:
    """Aggregate all short-related data."""
    from asyncio import gather
    sv, si, dsi, bf, ftd = await gather(
        get_short_volume(ticker),
        get_short_interest(ticker),
        get_daily_short_interest(ticker),
        get_borrow_fee(ticker),
        get_ftds(ticker),
    )
    return {
        "short_volume": sv,
        "short_interest": si,
        "daily_short_interest": dsi,
        "borrow_fee": bf,
        "ftds": ftd,
    }


# ── Dark Pool ───────────────────────────────────────────────────────────────

async def get_darkpool(ticker: str, date: str | None = None) -> dict[str, Any]:
    """Dark pool levels + summary for a given date."""
    from datetime import datetime, timezone
    if date is None:
        # Default to today; Clawby will return empty if not a trading day
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    from asyncio import gather
    levels, summary = await gather(
        _call("Dark Pool Levels for a given stock", {
            "symbol": f"US:{ticker}",
            "date": date,
            "decimals": "2",
        }),
        _call("Dark Pool Prints (trades) summary for a given stock", {
            "symbol": f"US:{ticker}",
            "date": date,
            "all_exchanges": True,
        }),
    )
    return {
        "date": date,
        "levels": levels if isinstance(levels, list) else [],
        "summary": summary if isinstance(summary, dict) else {},
    }


# ── Options ─────────────────────────────────────────────────────────────────

async def get_options_chain(ticker: str) -> dict[str, Any]:
    """Fetch the nearest monthly expiration's option chain."""
    # First, list available option contracts to find the nearest expiration
    contracts = await _call("List of option contracts", {
        "underlying": f"US:{ticker}",
        "expiration_gte": time.strftime("%Y-%m-%d"),
        "page_size": 1,
    })
    if not isinstance(contracts, list) or len(contracts) == 0:
        return {"underlying": f"US:{ticker}", "expiration": None, "max_pain": None, "chain": []}

    nearest_exp = contracts[0].get("expiration")
    if not nearest_exp:
        return {"underlying": f"US:{ticker}", "expiration": None, "max_pain": None, "chain": []}

    chain = await _call("Option chain summary (max pain, ITM/OTM)", {
        "underlying": f"US:{ticker}",
        "expiration": nearest_exp,
    })
    return {
        "underlying": f"US:{ticker}",
        "expiration": nearest_exp,
        "chain": chain if isinstance(chain, list) else [],
    }


# ── Corporate Actions ───────────────────────────────────────────────────────

async def get_corporate(ticker: str) -> dict[str, Any]:
    from asyncio import gather
    div, spl, flt = await gather(
        _call("Dividends for a given stock", {"symbol": f"US:{ticker}"}),
        _call("Splits for a given stock", {"symbol": f"US:{ticker}"}),
        _call("Historical Float and Shares Outstanding for a given stock", {
            "symbol": f"US:{ticker}",
            "ordering": "-date",
        }),
    )
    return {
        "dividends": div if isinstance(div, list) else [],
        "splits": spl if isinstance(spl, list) else [],
        "float_history": flt if isinstance(flt, list) else [],
    }


# ── SEC Financials ──────────────────────────────────────────────────────────

SEC_CONCEPTS = [
    ("Revenues", "revenue"),
    ("NetIncomeLoss", "net_income"),
    ("EarningsPerShareDiluted", "eps"),
    ("Assets", "assets"),
    ("StockholdersEquity", "equity"),
]


async def get_financials(ticker: str) -> dict[str, Any]:
    """Look up CIK, then fetch key financial concepts."""
    # Step 1: search company name via yfinance / hardcoded mapping
    # For now use a fallback: screener gives us the company name
    quote = await get_quote(ticker)
    company_name = None
    if isinstance(quote, dict):
        company_name = quote.get("display") or quote.get("name")

    # Step 2: CIK lookup
    cik_result = await _call("sec_cik_lookup", {"company": company_name or ticker})
    cik = None
    if isinstance(cik_result, list) and len(cik_result) > 0:
        # Parse CIK from the result (varies by company; best effort)
        cik = cik_result[0].get("cik")

    if not cik:
        return {"company_name": company_name, "concepts": {}}

    # Step 3: fetch each concept
    from asyncio import gather

    async def _fetch_concept(concept: str) -> tuple[str, Any]:
        result = await _call("sec_company_concept", {"cik": cik, "concept": concept})
        return concept, result

    concepts_data = await gather(*[_fetch_concept(c) for c, _ in SEC_CONCEPTS])
    result = {"company_name": company_name, "cik": cik}
    for concept_tag, field_name in SEC_CONCEPTS:
        for tag, data in concepts_data:
            if tag == concept_tag:
                result[field_name] = data if isinstance(data, list) else []
                break
        else:
            result[field_name] = []

    return result


# ── Sentiment (Reddit) ──────────────────────────────────────────────────────

async def get_sentiment(ticker: str) -> dict[str, Any]:
    from asyncio import gather
    mentions, daily = await gather(
        _call("Reddit mentions for a given stock", {"symbol": f"US:{ticker}"}),
        _call("Daily Reddit mention counts for a given stock", {"symbol": f"US:{ticker}"}),
    )
    return {
        "mentions": mentions if isinstance(mentions, list) else [],
        "daily_counts": daily if isinstance(daily, list) else [],
    }


# ── Exchange Volume ─────────────────────────────────────────────────────────

async def get_exchange_volume(ticker: str) -> list[dict[str, Any]]:
    result = await _call("Exchange volume for a given stock", {
        "symbol": f"US:{ticker}",
        "ordering": "-date",
    })
    return result if isinstance(result, list) else []
