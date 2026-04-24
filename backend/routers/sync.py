from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
import logging
from datetime import datetime

from database import get_db
from price_engine import bulk_fetch_prices

logger = logging.getLogger(__name__)
router = APIRouter()


class SyncRequest(BaseModel):
    tickers: List[str]


@router.post("/sync")
async def sync_stocks(request: SyncRequest, app_request: Request):
    """
    Sync stock data from yfinance for the given tickers.
    Uses batch processing for efficiency with 13,000+ stocks.
    """
    csv_stocks = app_request.app.state.csv_stocks
    
    # Filter stocks by requested tickers
    if request.tickers:
        stocks_to_sync = [s for s in csv_stocks if s["ticker"] in request.tickers]
    else:
        # If no tickers specified, sync all
        stocks_to_sync = csv_stocks
    
    if not stocks_to_sync:
        raise HTTPException(404, "No stocks found")
    
    logger.info(f"Starting sync for {len(stocks_to_sync)} stocks")
    
    # Bulk fetch using price_engine
    enriched = await bulk_fetch_prices(stocks_to_sync)
    
    # Save to database
    synced = 0
    failed = 0
    failed_tickers = []
    
    async with await get_db() as db:
        for stock in enriched:
            if "sync_error" in stock:
                failed += 1
                failed_tickers.append(stock["ticker"])
                # Save error
                await db.execute(
                    """INSERT OR REPLACE INTO fundamentals 
                       (ticker, isin, name, country, asset_type, sync_error, synced_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        stock["ticker"],
                        stock["isin"],
                        stock["name"],
                        stock["country"],
                        stock["asset_type"],
                        stock["sync_error"],
                        datetime.now().isoformat(),
                    ),
                )
            else:
                synced += 1
                await db.execute(
                    """INSERT OR REPLACE INTO fundamentals 
                       (ticker, isin, name, country, asset_type, current_price, target_mean_price,
                        beta, trailing_pe, price_to_book, return_on_equity, debt_to_equity,
                        annualized_volatility, rsi14, sma50, sma200, sma_dist, skewness, kurtosis,
                        synced_at, sync_error)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                    (
                        stock["ticker"],
                        stock["isin"],
                        stock["name"],
                        stock["country"],
                        stock["asset_type"],
                        stock.get("current_price"),
                        stock.get("target_mean_price"),
                        stock.get("beta"),
                        stock.get("trailing_pe"),
                        stock.get("price_to_book"),
                        stock.get("return_on_equity"),
                        stock.get("debt_to_equity"),
                        stock.get("annualized_volatility"),
                        stock.get("rsi14"),
                        stock.get("sma50"),
                        stock.get("sma200"),
                        stock.get("sma_dist"),
                        stock.get("skewness"),
                        stock.get("kurtosis"),
                        stock["synced_at"],
                    ),
                )
        await db.commit()
    
    logger.info(f"Sync complete. Synced={synced}, Failed={failed}")
    
    return {
        "synced": synced,
        "failed": failed,
        "tickers_failed": failed_tickers,
    }


@router.get("/sync/status")
async def get_sync_status(app_request: Request):
    """
    Get sync status for all stocks from CSV.
    """
    csv_stocks = app_request.app.state.csv_stocks
    
    async with await get_db() as db:
        cursor = await db.execute(
            "SELECT ticker, synced_at, sync_error FROM fundamentals"
        )
        rows = await cursor.fetchall()
        synced_map = {row[0]: {"synced_at": row[1], "sync_error": row[2]} for row in rows}
    
    result = []
    for stock in csv_stocks:
        ticker = stock["ticker"]
        sync_data = synced_map.get(ticker, {})
        
        if sync_data.get("sync_error"):
            status = "failed"
        elif sync_data.get("synced_at"):
            status = "synced"
        else:
            status = "pending"
        
        result.append({
            **stock,
            "status": status,
            "synced_at": sync_data.get("synced_at"),
            "sync_error": sync_data.get("sync_error"),
        })
    
    return result
