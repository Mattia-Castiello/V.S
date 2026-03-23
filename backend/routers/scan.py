import logging

from fastapi import APIRouter, BackgroundTasks

from backend.database import get_supabase
from backend.scheduler.scanner import run_full_scan, run_single_item_scan

logger = logging.getLogger("vinted_intelligence")

router = APIRouter()


@router.post("/api/scan")
async def trigger_full_scan(background_tasks: BackgroundTasks) -> dict:
    """Trigger a full scan of all active watchlist items."""
    background_tasks.add_task(run_full_scan)
    return {"status": "scan_started", "message": "Full scan triggered in background"}


@router.post("/api/scan/{item_id}")
async def trigger_item_scan(item_id: str, background_tasks: BackgroundTasks) -> dict:
    """Trigger a scan for a single watchlist item and return listings immediately."""
    db = get_supabase()
    item = db.table("watchlist_items").select("*").eq("id", item_id).single().execute()
    if not item.data:
        return {"status": "error", "message": "Watchlist item not found"}

    background_tasks.add_task(run_single_item_scan, item.data)
    return {"status": "scan_started", "item_id": item_id}
