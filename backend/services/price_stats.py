import logging
from datetime import datetime, timezone

from backend.database import get_supabase

logger = logging.getLogger("vinted_intelligence")

# Map Vinted status IDs to readable condition names
CONDITION_MAP = {
    "6": "Nuovo con cartellino",
    "1": "Nuovo senza cartellino",
    "2": "Ottimo",
    "3": "Buono",
    "4": "Discreto",
}


def calculate_cluster_stats(cluster_id: str) -> dict:
    """Calculate price stats for all listings in a cluster, grouped by condition.

    Returns:
        {
            "all": {"avg": 150, "min": 80, "max": 220, "count": 25},
            "Nuovo con cartellino": {"avg": 180, "min": 150, "max": 220, "count": 8},
            ...
        }
    """
    db = get_supabase()

    listings = (
        db.table("listings")
        .select("price, condition")
        .eq("product_cluster_id", cluster_id)
        .execute()
    )
    rows = listings.data or []

    if not rows:
        return {"all": {"avg": 0, "min": 0, "max": 0, "count": 0}}

    # Group by condition
    by_condition: dict[str, list[float]] = {}
    all_prices: list[float] = []

    for row in rows:
        price = float(row.get("price") or 0)
        if price <= 0:
            continue
        condition = row.get("condition", "") or "Unknown"
        by_condition.setdefault(condition, []).append(price)
        all_prices.append(price)

    stats: dict[str, dict] = {}

    # Overall stats
    if all_prices:
        stats["all"] = {
            "avg": round(sum(all_prices) / len(all_prices), 2),
            "min": round(min(all_prices), 2),
            "max": round(max(all_prices), 2),
            "count": len(all_prices),
        }
    else:
        stats["all"] = {"avg": 0, "min": 0, "max": 0, "count": 0}

    # Per-condition stats
    for condition, prices in by_condition.items():
        stats[condition] = {
            "avg": round(sum(prices) / len(prices), 2),
            "min": round(min(prices), 2),
            "max": round(max(prices), 2),
            "count": len(prices),
        }

    # Persist to cluster_price_stats table
    _persist_stats(db, cluster_id, stats)

    return stats


def _persist_stats(db, cluster_id: str, stats: dict):
    """Upsert aggregated stats into the cluster_price_stats table."""
    now = datetime.now(timezone.utc).isoformat()

    for condition, s in stats.items():
        db.table("cluster_price_stats").upsert(
            {
                "product_cluster_id": cluster_id,
                "condition": condition,
                "avg_price": s["avg"],
                "min_price": s["min"],
                "max_price": s["max"],
                "listing_count": s["count"],
                "computed_at": now,
            },
            on_conflict="product_cluster_id,condition",
        ).execute()
