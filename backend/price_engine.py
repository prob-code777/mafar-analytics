"""Price engine optimized for 13,000+ stocks using batch downloads."""
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
import time
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# Country to Yahoo Finance suffix mapping
COUNTRY_SUFFIX = {
    "IT": ".MI",
    "FR": ".PA",
    "DE": ".DE",
    "NL": ".AS",
    "ES": ".MC",
    "BE": ".BR",
    "SE": ".ST",
    "CH": ".SW",
    "GB": ".L",
    "US": "",
    "AU": ".AX",
    "CA": ".TO",
    "JP": ".T",
}

BATCH_SIZE = 100
MAX_WORKERS = 5
DELAY_BETWEEN_BATCHES = 0.5


def get_ticker_with_suffix(ticker: str, country: str) -> str:
    """Append correct Yahoo Finance suffix based on country."""
    suffix = COUNTRY_SUFFIX.get(country, "")
    return f"{ticker}{suffix}"


def download_batch(tickers: List[str], period="1y") -> Dict:
    """
    Download a batch of tickers using yfinance with threads=True.
    Returns dict of {ticker: data}.
    """
    logger.info(f"Downloading batch of {len(tickers)} tickers...")
    try:
        data = yf.download(
            tickers=" ".join(tickers),
            period=period,
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        return {"status": "ok", "data": data}
    except Exception as e:
        logger.error(f"Batch download failed: {e}")
        return {"status": "error", "error": str(e)}


def calculate_metrics(df: pd.DataFrame) -> Optional[Dict]:
    """
    Calculate annualized volatility, RSI14, SMA50/200, skewness, kurtosis.
    """
    if df is None or len(df) < 50:
        return None
    
    try:
        # Returns
        returns = df["Close"].pct_change().dropna()
        
        # Annualized Volatility
        vol = returns.std() * np.sqrt(252)
        
        # RSI-14 (Wilder smoothing)
        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi14 = rsi.iloc[-1] if not rsi.empty else None
        
        # SMA
        sma50 = df["Close"].rolling(50).mean().iloc[-1]
        sma200 = df["Close"].rolling(200).mean().iloc[-1]
        sma_dist = (sma50 - sma200) / sma200 if sma200 else None
        
        # Skewness & Kurtosis
        skew = returns[-252:].skew() if len(returns) >= 252 else None
        kurt = returns[-252:].kurtosis() if len(returns) >= 252 else None
        
        return {
            "annualized_volatility": vol,
            "rsi14": rsi14,
            "sma50": sma50,
            "sma200": sma200,
            "sma_dist": sma_dist,
            "skewness": skew,
            "kurtosis": kurt,
        }
    except Exception as e:
        logger.warning(f"Metric calc failed: {e}")
        return None


async def bulk_fetch_prices(stocks: List[Dict], batch_size=BATCH_SIZE, max_workers=MAX_WORKERS):
    """
    Fetch prices for 13,000+ stocks in batches.
    Uses yfinance.download with threads=True for parallelism.
    
    Returns: List of enriched stock dicts.
    """
    results = []
    total = len(stocks)
    
    # Group stocks by batch
    batches = [stocks[i:i+batch_size] for i in range(0, total, batch_size)]
    
    logger.info(f"Starting bulk fetch for {total} stocks in {len(batches)} batches")
    
    for idx, batch in enumerate(batches):
        logger.info(f"Processing batch {idx+1}/{len(batches)}")
        
        # Prepare tickers with suffix
        batch_tickers = [get_ticker_with_suffix(s["ticker"], s["country"]) for s in batch]
        
        # Download batch
        batch_result = await asyncio.to_thread(download_batch, batch_tickers)
        
        if batch_result["status"] == "error":
            logger.warning(f"Batch {idx+1} failed: {batch_result['error']}")
            results.extend([{**s, "sync_error": batch_result["error"]} for s in batch])
            continue
        
        data = batch_result["data"]
        
        # Process each stock in batch
        for stock in batch:
            ticker_suffix = get_ticker_with_suffix(stock["ticker"], stock["country"])
            
            try:
                # Extract this ticker's data
                if len(batch_tickers) == 1:
                    df = data
                else:
                    df = data[ticker_suffix] if ticker_suffix in data else None
                
                if df is None or df.empty:
                    results.append({**stock, "sync_error": "No data"})
                    continue
                
                # Get latest price
                current_price = df["Close"].iloc[-1]
                
                # Calculate metrics
                metrics = calculate_metrics(df)
                
                # Fetch .info for fundamentals
                ticker_obj = yf.Ticker(ticker_suffix)
                info = ticker_obj.info or {}
                
                enriched = {
                    **stock,
                    "current_price": current_price,
                    "target_mean_price": info.get("targetMeanPrice"),
                    "beta": info.get("beta"),
                    "trailing_pe": info.get("trailingPE"),
                    "price_to_book": info.get("priceToBook"),
                    "return_on_equity": info.get("returnOnEquity"),
                    "debt_to_equity": info.get("debtToEquity"),
                    "synced_at": datetime.now().isoformat(),
                }
                
                if metrics:
                    enriched.update(metrics)
                
                results.append(enriched)
                
            except Exception as e:
                logger.warning(f"Failed to process {ticker_suffix}: {e}")
                results.append({**stock, "sync_error": str(e)})
        
        # Rate limiting
        if idx < len(batches) - 1:
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)
    
    logger.info(f"Bulk fetch completed. {len(results)} stocks processed.")
    return results
