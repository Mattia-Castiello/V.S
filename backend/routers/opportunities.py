import json

from fastapi import APIRouter

from backend.database import get_supabase

router = APIRouter()


@router.get("/api/opportunities")
async def get_opportunities() -> list[dict]:
    db = get_supabase()

    result = (
        db.table("opportunities")
        .select(
            "id, listing_id, vinted_price, "
            "avg_price_same_condition, avg_price_all, margin_absolute, margin_percent, "
            "price_vs_avg, num_similar, canonical_name, condition_breakdown, "
            "product_cluster_id, score, is_active, "
            "listings(id, title, description, price, condition, image_url, url, "
            "published_at, brand, model, size, seller_username, seller_rating, "
            "photos, favourite_count, view_count, city, country, watchlist_item_id)"
        )
        .eq("is_active", True)
        .order("price_vs_avg", desc=False)
        .execute()
    )

    opportunities = []
    for row in result.data or []:
        listing = row.get("listings") or {}
        # Skip opportunities whose listing has no active watchlist item
        if not listing.get("watchlist_item_id"):
            continue
        photos = listing.get("photos") or []

        # Parse condition_breakdown from JSON string if needed
        breakdown = row.get("condition_breakdown") or []
        if isinstance(breakdown, str):
            try:
                breakdown = json.loads(breakdown)
            except (json.JSONDecodeError, TypeError):
                breakdown = []

        opportunities.append(
            {
                "id": listing.get("id", row["listing_id"]),
                "title": listing.get("title", ""),
                "description": listing.get("description", ""),
                "price": row["vinted_price"],
                "condition": listing.get("condition", ""),
                "imageUrl": listing.get("image_url", ""),
                "url": listing.get("url", ""),
                "publishedAt": listing.get("published_at"),
                "brand": listing.get("brand"),
                "model": listing.get("model"),
                "size": listing.get("size"),
                "sellerUsername": listing.get("seller_username"),
                "sellerRating": listing.get("seller_rating"),
                "photos": photos if isinstance(photos, list) else [],
                "favouriteCount": listing.get("favourite_count") or 0,
                "viewCount": listing.get("view_count") or 0,
                "city": listing.get("city"),
                "country": listing.get("country"),
                "avgPriceSameCondition": row.get("avg_price_same_condition") or 0,
                "avgPriceAll": row.get("avg_price_all") or 0,
                "marginAbsolute": row.get("margin_absolute") or 0,
                "priceVsAvg": row.get("price_vs_avg") or 0,
                "numSimilar": row.get("num_similar") or 0,
                "canonicalName": row.get("canonical_name"),
                "conditionBreakdown": breakdown,
                "score": row["score"],
            }
        )

    return opportunities
