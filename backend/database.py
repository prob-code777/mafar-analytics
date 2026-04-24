import aiosqlite
import os

DB_PATH = os.environ.get("DB_PATH", "stocks.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS fundamentals (
                ticker TEXT PRIMARY KEY,
                isin TEXT,
                name TEXT,
                country TEXT,
                asset_type TEXT,
                current_price REAL,
                target_mean_price REAL,
                beta REAL,
                trailing_pe REAL,
                price_to_book REAL,
                return_on_equity REAL,
                debt_to_equity REAL,
                annualized_volatility REAL,
                rsi14 REAL,
                sma50 REAL,
                sma200 REAL,
                sma_dist REAL,
                skewness REAL,
                kurtosis REAL,
                wiki_views_7d INTEGER DEFAULT 0,
                reddit_mentions_7d INTEGER DEFAULT 0,
                insider_buy_count INTEGER DEFAULT 0,
                insider_sell_count INTEGER DEFAULT 0,
                insider_sell_ratio REAL DEFAULT 0.0,
                synced_at TEXT,
                sync_error TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS price_cache (
                ticker TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                PRIMARY KEY (ticker, date)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS insider_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                date TEXT,
                insider_name TEXT,
                position TEXT,
                type TEXT,
                shares REAL,
                value REAL
            )
        """)
        await db.commit()


async def get_db():
    return aiosqlite.connect(DB_PATH)
