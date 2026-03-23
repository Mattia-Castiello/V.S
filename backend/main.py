from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import (
    debug,
    health,
    opportunities,
    purchases,
    scan,
    stats,
    watchlist,
)
from backend.scheduler.jobs import start_scheduler, stop_scheduler
from backend.utils.logger import setup_logging

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Vinted Intelligence backend")
    start_scheduler()
    yield
    logger.info("Shutting down")
    stop_scheduler()


app = FastAPI(title="Vinted Intelligence", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router)
app.include_router(opportunities.router)
app.include_router(watchlist.router)
app.include_router(scan.router)
app.include_router(purchases.router)
app.include_router(debug.router)
app.include_router(health.router)
