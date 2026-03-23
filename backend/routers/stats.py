from fastapi import APIRouter

from backend.database import get_supabase
from backend.models import DashboardStats

router = APIRouter()


@router.get("/api/stats")
async def get_stats() -> dict:
    db = get_supabase()

    watchlist = (
        db.table("watchlist_items")
        .select("id", count="exact")
        .eq("active", True)
        .execute()
    )
    total_monitored = watchlist.count or 0

    opps = (
        db.table("opportunities")
        .select("margin_absolute, price_vs_avg")
        .eq("is_active", True)
        .execute()
    )

    active_rows = opps.data or []
    opportunities_found = len(active_rows)

    avg_margin = 0.0
    potential_profit = 0.0
    if active_rows:
        # avg_margin: average of price_vs_avg (negative = below market)
        vs_avgs = [
            row.get("price_vs_avg")
            for row in active_rows
            if row.get("price_vs_avg") is not None
        ]
        avg_margin = round(sum(vs_avgs) / len(vs_avgs), 1) if vs_avgs else 0.0
        # potential_profit: sum of positive margin_absolute (savings)
        potential_profit = round(
            sum(
                row.get("margin_absolute") or 0
                for row in active_rows
                if (row.get("margin_absolute") or 0) > 0
            ),
            2,
        )

    return DashboardStats(
        total_monitored=total_monitored,
        opportunities_found=opportunities_found,
        avg_margin=avg_margin,
        potential_profit=potential_profit,
    ).model_dump(by_alias=True)
