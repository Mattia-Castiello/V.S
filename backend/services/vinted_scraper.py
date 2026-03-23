import asyncio
import logging
import random
from datetime import datetime, timezone

from postgrest import APIError

from backend.config import get_settings
from backend.database import get_supabase
from backend.services.vinted_session import VintedSession
from backend.utils.apple_products import get_search_configs_for_query

logger = logging.getLogger("vinted_intelligence")


async def scrape_catalog(
    session: VintedSession,
    search_text: str,
    brand_ids: list[int] | None = None,
    catalog_ids: list[int] | None = None,
    size_ids: list[int] | None = None,
    color_ids: list[int] | None = None,
    material_ids: list[int] | None = None,
    status_ids: list[int] | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort_order: str = "newest_first",
    per_page: int = 96,
    max_pages: int = 5,
) -> list[dict]:
    """Scrape Vinted catalog for items matching criteria, with pagination."""
    settings = get_settings()
    all_items: list[dict] = []

    for page in range(1, max_pages + 1):
        # Use list of tuples to support repeated keys
        params: list[tuple[str, str | int | float]] = [
            ("search_text", search_text),
            ("per_page", per_page),
            ("order", sort_order),
            ("page", page),
        ]
        if brand_ids:
            for bid in brand_ids:
                params.append(("brand_ids[]", bid))
        if catalog_ids:
            for cid in catalog_ids:
                params.append(("catalog_ids[]", cid))
        if size_ids:
            for sid in size_ids:
                params.append(("size_ids[]", sid))
        if color_ids:
            for cid in color_ids:
                params.append(("color_ids[]", cid))
        if material_ids:
            for mid in material_ids:
                params.append(("material_ids[]", mid))
        if status_ids:
            for sid in status_ids:
                params.append(("status_ids[]", sid))
        if min_price:
            params.append(("price_from", min_price))
        if max_price:
            params.append(("price_to", max_price))

        data = await session.get("/api/v2/catalog/items", params=params)
        if not data:
            break

        items = data.get("items", [])
        if not items:
            break

        all_items.extend(items)
        logger.info(
            f"Page {page}: {len(items)} items for '{search_text}' "
            f"(total so far: {len(all_items)})"
        )

        # If we got fewer items than per_page, we've reached the last page
        if len(items) < per_page:
            break

        # Rate limit between pages
        delay = random.uniform(settings.vinted_delay_min, settings.vinted_delay_max)
        await asyncio.sleep(delay)

    listings = []
    for item in all_items:
        user = item.get("user", {})
        photo = item.get("photo", {})
        photos_raw = item.get("photos", [])

        # Extract all photos
        photos = []
        for p in photos_raw:
            photos.append(
                {
                    "id": p.get("id"),
                    "url": p.get("url", ""),
                    "thumbnails": [
                        t.get("url", "") for t in (p.get("thumbnails", []) or [])
                    ],
                }
            )

        # Extract price details
        price_obj = item.get("price", {})
        if isinstance(price_obj, dict):
            price_val = float(price_obj.get("amount", "0"))
            currency = price_obj.get("currency_code", "EUR")
        else:
            price_val = float(price_obj or 0)
            currency = "EUR"

        total_price_obj = item.get("total_item_price", {})
        total_item_price = None
        if isinstance(total_price_obj, dict) and total_price_obj.get("amount"):
            total_item_price = float(total_price_obj.get("amount", "0"))

        service_fee_obj = item.get("service_fee", {})
        service_fee = None
        if isinstance(service_fee_obj, dict) and service_fee_obj.get("amount"):
            service_fee = float(service_fee_obj.get("amount", "0"))

        # Extract colours
        color1 = None
        color2 = None
        colours = item.get("colors", []) or []
        if len(colours) > 0:
            color1 = (
                colours[0].get("title")
                if isinstance(colours[0], dict)
                else str(colours[0])
            )
        if len(colours) > 1:
            color2 = (
                colours[1].get("title")
                if isinstance(colours[1], dict)
                else str(colours[1])
            )

        # Extract material
        material = item.get("material_title", "") or ""

        # Extract user location
        city = ""
        country = ""
        if user:
            city = user.get("city", "") or ""
            country = user.get("country_title", "") or ""

        listings.append(
            {
                "id": str(item.get("id", "")),
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "price": price_val,
                "currency": currency,
                "condition": item.get("status", ""),
                "image_url": photo.get("url", "") if photo else "",
                "url": item.get("url", ""),
                "published_at": item.get("created_at_ts"),
                "brand": item.get("brand_title", ""),
                "size": item.get("size_title", ""),
                "seller_id": str(user.get("id", "")) if user else "",
                "seller_username": user.get("login", "") if user else "",
                "seller_rating": (
                    float(user.get("feedback_reputation", 0) or 0) if user else 0
                ),
                "category_id": item.get("catalog_id"),
                "photos": photos,
                "total_item_price": total_item_price,
                "service_fee": service_fee,
                "color1": color1,
                "color2": color2,
                "material": material,
                "favourite_count": int(item.get("favourite_count", 0) or 0),
                "view_count": int(item.get("view_count", 0) or 0),
                "city": city,
                "country": country,
                "raw_json": item,
            }
        )

    return listings


async def scrape_watchlist_items(
    session: VintedSession, watchlist_items: list[dict]
) -> list[dict]:
    """Scrape Vinted for all active watchlist items."""
    settings = get_settings()
    db = get_supabase()
    all_listings = []

    for wl_item in watchlist_items:
        query = wl_item.get("query", "")
        configs = get_search_configs_for_query(query)

        # Get filter IDs from the watchlist item (may be empty lists)
        wl_brand_ids = wl_item.get("brand_ids") or []
        wl_catalog_ids = wl_item.get("catalog_ids") or []
        wl_size_ids = wl_item.get("size_ids") or []
        wl_color_ids = wl_item.get("color_ids") or []
        wl_material_ids = wl_item.get("material_ids") or []
        wl_status_ids = wl_item.get("status_ids") or []
        wl_sort_order = wl_item.get("sort_order") or "newest_first"
        wl_min_price = wl_item.get("min_price")

        for config in configs:
            # Merge: watchlist filters take priority, fall back to config
            brand_ids = wl_brand_ids or (
                [config["brand_id"]] if config.get("brand_id") else []
            )
            catalog_ids = wl_catalog_ids or (
                [config["category_id"]] if config.get("category_id") else []
            )

            for search_term in config.get("search_terms", [query]):
                try:
                    listings = await scrape_catalog(
                        session=session,
                        search_text=search_term,
                        brand_ids=brand_ids or None,
                        catalog_ids=catalog_ids or None,
                        size_ids=wl_size_ids or None,
                        color_ids=wl_color_ids or None,
                        material_ids=wl_material_ids or None,
                        status_ids=wl_status_ids or None,
                        min_price=wl_min_price,
                        max_price=wl_item.get("max_price"),
                        sort_order=wl_sort_order,
                    )

                    # Filter out irrelevant results
                    relevant = _filter_relevant(listings, search_term, query)
                    if len(relevant) < len(listings):
                        logger.info(
                            f"Filtered {len(listings) - len(relevant)} irrelevant "
                            f"listings for '{search_term}'"
                        )

                    # Save/update listings in Supabase
                    for listing in relevant:
                        listing["watchlist_item_id"] = wl_item["id"]
                        _save_listing(db, listing)

                    all_listings.extend(relevant)
                    logger.info(
                        f"Found {len(relevant)} relevant listings for '{search_term}'"
                    )

                except Exception as e:
                    logger.error(f"Error scraping '{search_term}': {e}")

                # Rate limit delay
                delay = random.uniform(
                    settings.vinted_delay_min, settings.vinted_delay_max
                )
                await asyncio.sleep(delay)

    # Deduplicate by listing ID
    seen = set()
    unique = []
    for listing in all_listings:
        if listing["id"] not in seen:
            seen.add(listing["id"])
            unique.append(listing)

    return unique


def _filter_relevant(listings: list[dict], search_term: str, query: str) -> list[dict]:
    """Filter out listings that are clearly irrelevant to the search query.

    Vinted text search is fuzzy and returns items like MAC cosmetics
    when searching for 'Mac Mini'. Uses phrase matching + word boundary
    checks for accurate filtering.
    """
    import re

    # Build the core phrase to search for (lowercase)
    # Use the more specific of search_term and query
    phrase = (search_term or query).lower().strip()

    # Also build individual word set for fallback matching
    all_words = f"{search_term} {query}".lower().split()
    query_words = [w for w in all_words if len(w) >= 3]
    # Deduplicate while preserving order
    seen_words: set[str] = set()
    unique_words: list[str] = []
    for w in query_words:
        if w not in seen_words:
            seen_words.add(w)
            unique_words.append(w)
    query_words = unique_words

    if not query_words:
        return listings

    relevant = []
    for listing in listings:
        title_lower = listing.get("title", "").lower()

        # Strategy 1: Check if the full phrase appears in the title
        # e.g. "mac mini" in "Apple Mac Mini M4"
        if phrase in title_lower:
            relevant.append(listing)
            continue

        # Strategy 2: Check if ALL significant query words appear as whole words
        # Use word boundary regex to avoid "minibrands" matching "mini"
        all_match = True
        for word in query_words:
            # Use word boundary for short words to avoid substring matches
            pattern = rf"\b{re.escape(word)}\b"
            if not re.search(pattern, title_lower):
                all_match = False
                break

        if all_match:
            relevant.append(listing)
        else:
            logger.debug(f"Filtered out irrelevant listing: '{listing.get('title')}'")

    return relevant


def _save_listing(db, listing: dict):
    """Upsert a listing into Supabase."""
    import json

    data = {
        "id": listing["id"],
        "title": listing["title"],
        "description": listing.get("description", ""),
        "price": listing["price"],
        "currency": listing.get("currency", "EUR"),
        "condition": listing.get("condition", ""),
        "image_url": listing.get("image_url", ""),
        "url": listing.get("url", ""),
        "published_at": listing.get("published_at"),
        "brand": listing.get("brand"),
        "model": listing.get("model"),
        "size": listing.get("size"),
        "seller_id": listing.get("seller_id"),
        "seller_username": listing.get("seller_username"),
        "seller_rating": listing.get("seller_rating"),
        "category_id": listing.get("category_id"),
        "watchlist_item_id": listing.get("watchlist_item_id"),
        "raw_json": listing.get("raw_json"),
        "last_seen_at": datetime.now(timezone.utc).isoformat(),
        # New fields
        "photos": json.dumps(listing.get("photos", [])),
        "total_item_price": listing.get("total_item_price"),
        "service_fee": listing.get("service_fee"),
        "color1": listing.get("color1"),
        "color2": listing.get("color2"),
        "material": listing.get("material"),
        "favourite_count": listing.get("favourite_count", 0),
        "view_count": listing.get("view_count", 0),
        "city": listing.get("city"),
        "country": listing.get("country"),
    }

    try:
        db.table("listings").upsert(data, on_conflict="id").execute()
    except APIError as e:
        # If the watchlist item was deleted mid-scan, skip gracefully instead of crashing.
        if e.code == "23503":
            logger.info(
                "Skipping listing %s because watchlist item %s no longer exists",
                listing["id"],
                listing.get("watchlist_item_id"),
            )
            return
        logger.error(f"Failed to save listing {listing['id']}: {e}")
    except Exception as e:
        logger.error(f"Failed to save listing {listing['id']}: {e}")
