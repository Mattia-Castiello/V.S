import json
import logging

from fastapi import APIRouter

from backend.config import get_settings
from backend.database import get_supabase
from backend.services.opportunity_scorer import score_opportunity
from backend.services.price_stats import calculate_cluster_stats
from backend.services.product_clusterer import cluster_products
from backend.services.vinted_session import VintedSession

logger = logging.getLogger("vinted_intelligence")

router = APIRouter()


@router.get("/api/debug/test-vinted")
async def test_vinted_scrape(query: str = "iPhone 15", max_price: float = 500):
    """Test endpoint to debug Vinted scraping step by step."""
    steps = []

    # Step 1: Check settings
    settings = get_settings()
    steps.append(
        {
            "step": "1_settings",
            "vinted_base_url": settings.vinted_base_url,
            "supabase_url_set": bool(settings.supabase_url),
            "ollama_url": settings.ollama_base_url,
        }
    )

    # Step 2: Test Vinted session
    session = VintedSession()
    try:
        await session.ensure_session()
        steps.append(
            {
                "step": "2_session",
                "status": "ok",
                "cookie_obtained": bool(session._cookie),
                "cookie_preview": (
                    session._cookie[:20] + "..." if session._cookie else None
                ),
            }
        )
    except Exception as e:
        steps.append({"step": "2_session", "status": "error", "error": str(e)})
        await session.close()
        return {"steps": steps, "error": "Session failed"}

    # Step 3: Test catalog search
    try:
        params = {
            "search_text": query,
            "per_page": 10,
            "order": "newest_first",
            "price_to": max_price,
        }
        data = await session.get("/api/v2/catalog/items", params=params)
        if data:
            items = data.get("items", [])
            steps.append(
                {
                    "step": "3_catalog_search",
                    "status": "ok",
                    "total_items": len(items),
                    "query": query,
                    "params": params,
                    "sample_items": [
                        {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "price": item.get("price"),
                            "brand": item.get("brand_title"),
                            "url": item.get("url"),
                        }
                        for item in items[:3]
                    ],
                    "raw_keys": list(data.keys()),
                }
            )
        else:
            steps.append(
                {
                    "step": "3_catalog_search",
                    "status": "empty_response",
                    "query": query,
                    "params": params,
                }
            )
    except Exception as e:
        steps.append({"step": "3_catalog_search", "status": "error", "error": str(e)})

    # Step 4: Test WITH brand_id (current behavior)
    try:
        params_with_brand = {
            "search_text": query,
            "brand_ids[]": 319,
            "per_page": 10,
            "order": "newest_first",
            "price_to": max_price,
        }
        data2 = await session.get("/api/v2/catalog/items", params=params_with_brand)
        items2 = data2.get("items", []) if data2 else []
        steps.append(
            {
                "step": "4_catalog_with_brand_filter",
                "status": "ok",
                "total_items": len(items2),
                "note": "This is how the scraper currently searches (brand_id=319=Apple)",
            }
        )
    except Exception as e:
        steps.append(
            {"step": "4_catalog_with_brand_filter", "status": "error", "error": str(e)}
        )

    # Step 5: Test Supabase connection
    try:
        db = get_supabase()
        wl = db.table("watchlist_items").select("id", count="exact").execute()
        steps.append(
            {
                "step": "5_supabase",
                "status": "ok",
                "watchlist_count": wl.count or 0,
            }
        )
    except Exception as e:
        steps.append({"step": "5_supabase", "status": "error", "error": str(e)})

    await session.close()
    return {"steps": steps}


@router.post("/api/debug/cleanup-junk")
async def cleanup_junk_listings():
    """Remove junk listings that don't match their watchlist query.

    Uses phrase and word-boundary matching for each watchlist query.
    """
    import re

    db = get_supabase()

    # Get all watchlist items with their queries
    wl_items = db.table("watchlist_items").select("id, query").execute()
    wl_map = {w["id"]: w["query"] for w in (wl_items.data or [])}

    # If there's only one query, use it for orphan listings too
    all_queries = list({q.lower().strip() for q in wl_map.values() if q})

    # Get all listings
    listings = (
        db.table("listings").select("id, title, brand, watchlist_item_id").execute()
    )

    removed = 0
    kept = 0
    removed_titles = []
    for listing in listings.data or []:
        wl_id = listing.get("watchlist_item_id")
        query = wl_map.get(wl_id, "")

        # For orphan listings (no watchlist_item_id), try the primary query
        if not query and all_queries:
            query = all_queries[0]

        title = (listing.get("title") or "").lower()

        if not query:
            kept += 1
            continue

        phrase = query.lower().strip()
        query_words = [w for w in phrase.split() if len(w) >= 3]

        # Strategy 1: Full phrase match
        if phrase in title:
            kept += 1
            continue

        # Strategy 2: All words match with word boundaries
        all_match = True
        for word in query_words:
            if not re.search(rf"\b{re.escape(word)}\b", title):
                all_match = False
                break

        if all_match:
            kept += 1
        else:
            db.table("opportunities").delete().eq("listing_id", listing["id"]).execute()
            db.table("listings").delete().eq("id", listing["id"]).execute()
            removed += 1
            removed_titles.append(
                f"[{listing.get('brand', '')}] {listing.get('title', '')}"
            )

    return {"removed": removed, "kept": kept, "removed_titles": removed_titles}


@router.post("/api/debug/backfill-clusters")
async def backfill_clusters():
    """Re-cluster all existing listings and recalculate stats."""
    db = get_supabase()

    # Get all unclustered listings
    listings_resp = (
        db.table("listings")
        .select("id, title, description, brand, condition, price")
        .is_("product_cluster_id", "null")
        .execute()
    )
    listings = listings_resp.data or []

    if not listings:
        return {"message": "No unclustered listings found", "clustered": 0}

    # Run clustering
    cluster_map = await cluster_products(listings)

    # Calculate stats for each cluster
    cluster_stats_map: dict[str, dict] = {}
    for cluster_id in set(cluster_map.values()):
        try:
            cluster_stats_map[cluster_id] = calculate_cluster_stats(cluster_id)
        except Exception as e:
            logger.error(f"Error calculating stats for cluster {cluster_id}: {e}")
            cluster_stats_map[cluster_id] = {
                "all": {"avg": 0, "min": 0, "max": 0, "count": 0}
            }

    # Update opportunities with cluster data
    updated = 0
    for listing in listings:
        lid = listing["id"]
        cid = cluster_map.get(lid)
        if not cid:
            continue

        stats = cluster_stats_map.get(cid, {})
        price = float(listing.get("price", 0))
        condition = listing.get("condition", "")

        all_stats = stats.get("all", {})
        condition_stats = stats.get(condition, {})
        avg_same = condition_stats.get("avg", 0)
        avg_all = all_stats.get("avg", 0)
        num_similar = all_stats.get("count", 0)

        scoring = score_opportunity(price, avg_same, avg_all, num_similar)

        breakdown = []
        for cond, s in stats.items():
            if cond == "all":
                continue
            breakdown.append(
                {
                    "condition": cond,
                    "avg": s.get("avg", 0),
                    "min": s.get("min", 0),
                    "max": s.get("max", 0),
                    "count": s.get("count", 0),
                }
            )

        # Get canonical name
        canonical_name = None
        cluster = (
            db.table("product_clusters")
            .select("canonical_name")
            .eq("id", cid)
            .execute()
        )
        if cluster.data:
            canonical_name = cluster.data[0]["canonical_name"]

        # Update opportunity
        db.table("opportunities").update(
            {
                "avg_price_same_condition": avg_same,
                "avg_price_all": avg_all,
                "margin_absolute": scoring["margin_absolute"],
                "margin_percent": (
                    abs(scoring["price_vs_avg"]) if scoring["price_vs_avg"] < 0 else 0
                ),
                "price_vs_avg": scoring["price_vs_avg"],
                "num_similar": num_similar,
                "canonical_name": canonical_name,
                "condition_breakdown": json.dumps(breakdown),
                "product_cluster_id": cid,
                "score": scoring["score"],
            }
        ).eq("listing_id", lid).execute()
        updated += 1

    # Get cluster summary
    clusters = db.table("product_clusters").select("canonical_name").execute()
    cluster_names = [c["canonical_name"] for c in (clusters.data or [])]

    return {
        "clustered": len(cluster_map),
        "updated_opportunities": updated,
        "clusters": cluster_names,
    }
