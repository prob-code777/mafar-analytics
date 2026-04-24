import csv
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

CSV_PATH = "TR-csv-completo.csv"


def load_csv() -> List[Dict]:
    """Load stock universe from TR-csv-completo.csv."""
    if not os.path.exists(CSV_PATH):
        logger.warning(f"CSV file not found: {CSV_PATH}")
        return []
    
    stocks = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stocks.append({
                "isin": row.get("ISIN", ""),
                "wkn": row.get("WKN", ""),
                "ticker": row.get("Ticker", ""),
                "asset_type": row.get("AssetType", ""),
                "name": row.get("Name", ""),
                "country": row.get("Country", ""),
            })
    
    logger.info(f"Loaded {len(stocks)} stocks from {CSV_PATH}")
    return stocks
