# MAFAR Analytics - Backend FastAPI
# Full quantitative finance engine with 13,000+ stock universe

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from routers import stocks, sync, calculate, portfolio, altdata
from database import init_db
from csv_loader import load_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting MAFAR Analytics backend...")
    await init_db()
    stocks_data = load_csv()
    app.state.csv_stocks = stocks_data
    logger.info(f"Loaded {len(stocks_data)} stocks from CSV")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="MAFAR Analytics API",
    version="2.0.0",
    description="Quantitative finance platform - 13,000+ stock universe",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api", tags=["stocks"])
app.include_router(sync.router, prefix="/api", tags=["sync"])
app.include_router(calculate.router, prefix="/api", tags=["calculate"])
app.include_router(portfolio.router, prefix="/api", tags=["portfolio"])
app.include_router(altdata.router, prefix="/api", tags=["altdata"])


@app.get("/api/healthz")
async def health_check():
    return {"status": "ok", "stocks_loaded": len(app.state.csv_stocks)}
