"""Raw data endpoints — each calls Clawby and returns structured JSON."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    BarsResponse,
    CorporateActionsResponse,
    DarkPoolResponse,
    FinancialsResponse,
    OptionsResponse,
    QuoteResponse,
    SentimentResponse,
    ShortDataResponse,
)
from app.services import clawby

router = APIRouter(prefix="/api", tags=["data"])


def _require_key():
    """Raise 503 if Clawby key is missing."""
    from app.config import settings
    if not settings.clawby_api_key:
        raise HTTPException(status_code=503, detail="CLAWBY_API_KEY not configured")


@router.get("/quote/{ticker}", response_model=QuoteResponse)
async def get_quote(ticker: str):
    _require_key()
    raw = await clawby.get_quote(ticker.upper())
    # Screener returns a list; take first result
    if isinstance(raw, list) and len(raw) > 0:
        raw = raw[0]
    if isinstance(raw, dict) and "error" in raw:
        raise HTTPException(status_code=502, detail=raw["error"])
    if not isinstance(raw, dict):
        raw = {}
    return QuoteResponse(
        ticker=ticker.upper(),
        price=raw.get("reg_price"),
        change=None,
        change_pct=raw.get("reg_change_pct"),
        market_cap=raw.get("market_cap"),
        volume=int(raw.get("reg_volume", 0)) if raw.get("reg_volume") else None,
        raw=raw,
    )


@router.get("/bars/{ticker}", response_model=BarsResponse)
async def get_bars(ticker: str, days: int = 365):
    _require_key()
    raw = await clawby.get_bars(ticker.upper(), days=days)
    return BarsResponse(ticker=ticker.upper(), bars=raw, count=len(raw))


@router.get("/short/{ticker}", response_model=ShortDataResponse)
async def get_short(ticker: str):
    _require_key()
    raw = await clawby.get_short_all(ticker.upper())
    return ShortDataResponse(
        ticker=ticker.upper(),
        short_volume=raw.get("short_volume", []),
        short_interest=raw.get("short_interest", []),
        daily_short_interest=raw.get("daily_short_interest", []),
        borrow_fee=raw.get("borrow_fee", []),
        ftds=raw.get("ftds", []),
    )


@router.get("/darkpool/{ticker}", response_model=DarkPoolResponse)
async def get_darkpool(ticker: str, date: str | None = None):
    _require_key()
    raw = await clawby.get_darkpool(ticker.upper(), date=date)
    return DarkPoolResponse(
        ticker=ticker.upper(),
        date=raw.get("date"),
        levels=raw.get("levels", []),
        summary=raw.get("summary", {}),
    )


@router.get("/options/{ticker}", response_model=OptionsResponse)
async def get_options(ticker: str):
    _require_key()
    raw = await clawby.get_options_chain(ticker.upper())
    return OptionsResponse(
        ticker=ticker.upper(),
        underlying=raw.get("underlying", f"US:{ticker.upper()}"),
        expiration=raw.get("expiration"),
        chain=raw.get("chain", []),
    )


@router.get("/financials/{ticker}", response_model=FinancialsResponse)
async def get_financials(ticker: str):
    _require_key()
    raw = await clawby.get_financials(ticker.upper())
    return FinancialsResponse(
        ticker=ticker.upper(),
        company_name=raw.get("company_name"),
        revenue=raw.get("revenue", []),
        net_income=raw.get("net_income", []),
        eps=raw.get("eps", []),
        assets=raw.get("assets", []),
        equity=raw.get("equity", []),
    )


@router.get("/corporate/{ticker}", response_model=CorporateActionsResponse)
async def get_corporate(ticker: str):
    _require_key()
    raw = await clawby.get_corporate(ticker.upper())
    return CorporateActionsResponse(
        ticker=ticker.upper(),
        dividends=raw.get("dividends", []),
        splits=raw.get("splits", []),
        float_history=raw.get("float_history", []),
    )


@router.get("/sentiment/{ticker}", response_model=SentimentResponse)
async def get_sentiment(ticker: str):
    _require_key()
    raw = await clawby.get_sentiment(ticker.upper())
    return SentimentResponse(
        ticker=ticker.upper(),
        mentions=raw.get("mentions", []),
        daily_counts=raw.get("daily_counts", []),
    )
