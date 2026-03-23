import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.config import get_settings

logger = logging.getLogger("vinted_intelligence")

_scheduler: AsyncIOScheduler | None = None
_last_scan: str | None = None
_vinted_session_status: str = "inactive"


def get_scheduler_status() -> dict:
    next_scan = None
    if _scheduler and _scheduler.running:
        jobs = _scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time
            if next_run:
                next_scan = next_run.isoformat()

    return {
        "vinted_session": _vinted_session_status,
        "next_scan": next_scan,
        "last_scan": _last_scan,
    }


def set_session_status(status: str):
    global _vinted_session_status
    _vinted_session_status = status


def set_last_scan(ts: str):
    global _last_scan
    _last_scan = ts


async def run_scan():
    from backend.scheduler.scanner import run_full_scan

    set_last_scan(datetime.utcnow().isoformat())
    try:
        await run_full_scan()
    except Exception as e:
        logger.error(f"Scan failed: {e}")


def start_scheduler():
    global _scheduler
    settings = get_settings()
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_scan,
        "interval",
        minutes=settings.scan_interval_minutes,
        id="vinted_scan",
        name="Vinted full scan",
        max_instances=1,
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.start()
    logger.info(f"Scheduler started: scan every {settings.scan_interval_minutes} min")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
