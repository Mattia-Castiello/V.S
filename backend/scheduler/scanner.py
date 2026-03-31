import json
import logging
from datetime import datetime

from backend.database import get_supabase
from backend.scheduler.jobs import set_last_scan, set_session_status
from backend.services.opportunity_scorer import score_opportunity
from backend.services.price_stats import calculate_cluster_stats
from backend.services.product_clusterer import cluster_products
from backend.services.vinted_scraper import scrape_watchlist_items
from backend.services.vinted_session import VintedSession

logger = logging.getLogger("vinted_intelligence")


async def run_full_scan():
    db = get_supabase()
    scan_start = datetime.utcnow()

    scan_log = (
        db.table("scan_logs")
        .insert({"started_at": scan_start.isoformat(), "status": "running"})
        .execute()
    )
    scan_id = scan_log.data[0]["id"] if scan_log.data else None

    total_listings = 0
    total_opportunities = 0
    errors = []

    try:
        # 1. Get active watchlist items
        watchlist = db.table("watchlist_items").select("*").eq("active", True).execute()
        items = watchlist.data or []

        if not items:
            logger.info("No active watchlist items, skipping scan")
            return

        # 2. Initialize Vinted session
        session = VintedSession()
        try:
            await session.ensure_session()
        except RuntimeError as e:
            logger.error(f"Vinted session failed: {e}")
            errors.append({"error": str(e)})
            set_session_status("error")
            if scan_id:
                scan_end = datetime.utcnow()
                db.table("scan_logs").update(
                    {
                        "finished_at": scan_end.isoformat(),
                        "status": "failed",
                        "listings_found": 0,
                        "opportunities_found": 0,
                        "errors": errors,
                        "duration_seconds": (scan_end - scan_start).total_seconds(),
                    }
                ).eq("id", scan_id).execute()
            return
        set_session_status("active")

        # 3. Scrape listings
        all_listings = await scrape_watchlist_items(session, items)
        total_listings = len(all_listings)
        logger.info(f"Found {total_listings} listings")

        if total_listings == 0:
            logger.warning(f"Scan found 0 listings across {len(items)} watchlist items")

        # 4. Cluster products (Ollama + regex fallback)
        try:
            cluster_map = await cluster_products(all_listings)
            logger.info(f"Clustered listings into {len(set(cluster_map.values()))} groups")
        except Exception as e:
            logger.warning(f"Clustering failed, proceeding without cluster stats: {e}")
            cluster_map = {}

        # 5. Calculate price stats for each unique cluster
        cluster_stats: dict[str, dict] = {}
        for cluster_id in set(cluster_map.values()):
            try:
                cluster_stats[cluster_id] = calculate_cluster_stats(cluster_id)
            except Exception as e:
                logger.error(f"Error calculating stats for cluster {cluster_id}: {e}")
                cluster_stats[cluster_id] = {
                    "all": {"avg": 0, "min": 0, "max": 0, "count": 0}
                }

        # 6. Score and upsert opportunities
        for listing in all_listings:
            try:
                lid = listing["id"]
                cid = cluster_map.get(lid)
                stats = cluster_stats.get(cid, {}) if cid else {}
                _upsert_listing_opportunity(db, listing, cid, stats)
                total_opportunities += 1
            except Exception as e:
                logger.error(
                    f"Error processing listing {listing.get('id')}: {e}",
                    exc_info=True,
                )
                errors.append({"listing_id": listing.get("id"), "error": str(e)})

        await session.close()
        set_session_status("inactive")

    except Exception as e:
        logger.error(f"Scan failed: {e}")
        errors.append({"error": str(e)})
        set_session_status("error")

    # Update scan log
    scan_end = datetime.utcnow()
    duration = (scan_end - scan_start).total_seconds()
    set_last_scan(scan_end.isoformat())

    if scan_id:
        db.table("scan_logs").update(
            {
                "finished_at": scan_end.isoformat(),
                "status": "completed" if not errors else "failed",
                "listings_found": total_listings,
                "opportunities_found": total_opportunities,
                "errors": errors,
                "duration_seconds": duration,
            }
        ).eq("id", scan_id).execute()

    logger.info(
        f"Scan completed: {total_listings} listings, {total_opportunities} opportunities, "
        f"{len(errors)} errors, {duration:.1f}s"
    )


async def run_single_item_scan(watchlist_item: dict):
    """Scan Vinted for a single watchlist item immediately."""
    db = get_supabase()

    try:
        session = VintedSession()
        try:
            await session.ensure_session()
        except RuntimeError as e:
            logger.error(f"Vinted session failed for single item scan: {e}")
            set_session_status("error")
            return
        set_session_status("active")

        listings = await scrape_watchlist_items(session, [watchlist_item])
        logger.info(
            f"Single item scan: found {len(listings)} listings for '{watchlist_item.get('query')}'"
        )

        if len(listings) == 0:
            logger.warning(
                f"Single item scan found 0 listings for '{watchlist_item.get('query')}'"
            )

        # Cluster + stats + score
        try:
            cluster_map = await cluster_products(listings)
        except Exception as e:
            logger.warning(f"Clustering failed for single item scan, proceeding without cluster stats: {e}")
            cluster_map = {}
        cluster_stats: dict[str, dict] = {}
        for cluster_id in set(cluster_map.values()):
            try:
                cluster_stats[cluster_id] = calculate_cluster_stats(cluster_id)
            except Exception as e:
                logger.error(f"Error calculating stats for cluster {cluster_id}: {e}")
                cluster_stats[cluster_id] = {
                    "all": {"avg": 0, "min": 0, "max": 0, "count": 0}
                }

        for listing in listings:
            try:
                lid = listing["id"]
                cid = cluster_map.get(lid)
                stats = cluster_stats.get(cid, {}) if cid else {}
                _upsert_listing_opportunity(db, listing, cid, stats)
            except Exception as e:
                logger.error(
                    f"Error processing listing {listing.get('id')}: {e}",
                    exc_info=True,
                )

        await session.close()
        set_session_status("inactive")

    except Exception as e:
        logger.error(f"Single item scan failed: {e}")
        set_session_status("error")


def _upsert_listing_opportunity(db, listing: dict, cluster_id: str | None, stats: dict):
    """Create/update an opportunity with avg price data and scoring."""
    price = listing.get("price", 0)
    condition = listing.get("condition", "")

    all_stats = stats.get("all", {})
    condition_stats = stats.get(condition, {})

    avg_same = condition_stats.get("avg", 0)
    avg_all = all_stats.get("avg", 0)
    num_similar = all_stats.get("count", 0)

    scoring = score_opportunity(price, avg_same, avg_all, num_similar)

    # Build condition breakdown
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

    # Fetch canonical_name from cluster
    canonical_name = None
    if cluster_id:
        cluster = (
            db.table("product_clusters")
            .select("canonical_name")
            .eq("id", cluster_id)
            .execute()
        )
        if cluster.data:
            canonical_name = cluster.data[0]["canonical_name"]

    opportunity = {
        "listing_id": listing["id"],
        "vinted_price": price,
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
        "product_cluster_id": cluster_id,
        "score": scoring["score"],
        "is_active": True,
    }
    db.table("opportunities").upsert(opportunity, on_conflict="listing_id").execute()
