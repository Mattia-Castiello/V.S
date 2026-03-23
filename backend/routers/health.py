from fastapi import APIRouter

from backend.database import get_supabase
from backend.models import HealthStatus

router = APIRouter()


@router.get("/api/health")
async def health_check() -> dict:
    db = get_supabase()

    try:
        listings = db.table("listings").select("id", count="exact").execute()
        listings_count = listings.count or 0
    except Exception:
        listings_count = 0

    try:
        opps = (
            db.table("opportunities")
            .select("id", count="exact")
            .eq("is_active", True)
            .execute()
        )
        opps_count = opps.count or 0
    except Exception:
        opps_count = 0

    # Session and scan info will be populated by the scheduler module
    from backend.scheduler.jobs import get_scheduler_status

    scheduler_info = get_scheduler_status()

    return HealthStatus(
        status="ok",
        vinted_session=scheduler_info.get("vinted_session", "inactive"),
        next_scan=scheduler_info.get("next_scan"),
        last_scan=scheduler_info.get("last_scan"),
        listings_count=listings_count,
        opportunities_count=opps_count,
    ).model_dump()
