import logging

from fastapi import APIRouter, HTTPException

from backend.database import get_supabase
from backend.models import WatchlistItemCreate

logger = logging.getLogger("vinted_intelligence")

router = APIRouter()


def _row_to_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "query": row["query"],
        "maxPrice": row["max_price"],
        "minPrice": row.get("min_price") or 0,
        "minMargin": row["min_margin"],
        "conditions": row.get("conditions") or [],
        "size": row.get("size"),
        "brandIds": row.get("brand_ids") or [],
        "catalogIds": row.get("catalog_ids") or [],
        "sizeIds": row.get("size_ids") or [],
        "colorIds": row.get("color_ids") or [],
        "materialIds": row.get("material_ids") or [],
        "statusIds": row.get("status_ids") or [],
        "sortOrder": row.get("sort_order") or "newest_first",
        "active": row["active"],
    }


@router.get("/api/watchlist")
async def get_watchlist() -> list[dict]:
    db = get_supabase()
    result = (
        db.table("watchlist_items").select("*").order("created_at", desc=True).execute()
    )
    return [_row_to_response(row) for row in (result.data or [])]


@router.post("/api/watchlist")
async def create_watchlist_item(item: WatchlistItemCreate) -> dict:
    db = get_supabase()
    data = {
        "type": item.type,
        "query": item.query,
        "max_price": item.max_price,
        "min_price": item.min_price,
        "min_margin": item.min_margin,
        "conditions": item.conditions,
        "size": item.size,
        "brand_ids": item.brand_ids,
        "catalog_ids": item.catalog_ids,
        "size_ids": item.size_ids,
        "color_ids": item.color_ids,
        "material_ids": item.material_ids,
        "status_ids": item.status_ids,
        "sort_order": item.sort_order,
        "active": item.active,
    }
    result = db.table("watchlist_items").insert(data).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create watchlist item")
    return _row_to_response(result.data[0])


@router.delete("/api/watchlist/{item_id}")
async def delete_watchlist_item(item_id: str):
    """Delete a watchlist item and all its associated listings/opportunities."""
    db = get_supabase()

    # Find all listings linked to this watchlist item
    listings_result = (
        db.table("listings").select("id").eq("watchlist_item_id", item_id).execute()
    )
    listing_ids = [row["id"] for row in (listings_result.data or [])]

    if listing_ids:
        # Batch delete related rows in a single query per table (instead of N queries)
        db.table("opportunities").delete().in_("listing_id", listing_ids).execute()
        db.table("price_comparisons").delete().in_("listing_id", listing_ids).execute()
        db.table("price_history").delete().in_("listing_id", listing_ids).execute()

        # Delete the listings themselves
        db.table("listings").delete().eq("watchlist_item_id", item_id).execute()

    # Delete the watchlist item
    db.table("watchlist_items").delete().eq("id", item_id).execute()
    logger.info(f"Deleted watchlist item {item_id} with {len(listing_ids)} listings")
    return None
