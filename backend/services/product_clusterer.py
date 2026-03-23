import json
import logging

import httpx

from backend.config import get_settings
from backend.database import get_supabase
from backend.services.product_matcher import (
    _clean_title,
    _extract_model,
    _extract_storage,
)

logger = logging.getLogger("vinted_intelligence")


async def cluster_products(listings: list[dict]) -> dict[str, str]:
    """Cluster listings into product groups using Ollama, with regex fallback.

    Returns a dict mapping listing_id -> product_cluster_id.
    Listings already clustered (with product_cluster_id) are skipped.
    """
    db = get_supabase()
    settings = get_settings()
    result_map: dict[str, str] = {}

    # Filter listings that need clustering
    unclustered = []
    for listing in listings:
        lid = listing["id"]
        # Check if already clustered in DB
        existing = (
            db.table("listings")
            .select("product_cluster_id")
            .eq("id", lid)
            .single()
            .execute()
        )
        if existing.data and existing.data.get("product_cluster_id"):
            result_map[lid] = existing.data["product_cluster_id"]
        else:
            unclustered.append(listing)

    if not unclustered:
        return result_map

    logger.info(f"Clustering {len(unclustered)} unclustered listings")

    # Process in batches
    batch_size = settings.clustering_batch_size
    for i in range(0, len(unclustered), batch_size):
        batch = unclustered[i : i + batch_size]
        cluster_results = await _cluster_batch(batch, settings)

        for listing, info in zip(batch, cluster_results):
            cluster_id = _get_or_create_cluster(db, info)
            result_map[listing["id"]] = cluster_id

            # Update listing with cluster_id
            db.table("listings").update({"product_cluster_id": cluster_id}).eq(
                "id", listing["id"]
            ).execute()

    return result_map


async def _cluster_batch(listings: list[dict], settings) -> list[dict]:
    """Send a batch of listings to Ollama for structured extraction.

    Falls back to regex-based extraction if Ollama is unavailable.
    """
    try:
        return await _ollama_cluster(listings, settings)
    except Exception as e:
        logger.warning(f"Ollama clustering failed, using regex fallback: {e}")
        return [_regex_fallback(l) for l in listings]


async def _ollama_cluster(listings: list[dict], settings) -> list[dict]:
    """Use Ollama local LLM to extract structured product info."""
    items_text = ""
    for idx, l in enumerate(listings):
        items_text += (
            f"{idx + 1}. Title: {l.get('title', '')}\n"
            f"   Brand: {l.get('brand', '')}\n"
            f"   Condition: {l.get('condition', '')}\n\n"
        )

    prompt = f"""Analyze these Vinted listings and extract the canonical product name for each.
For each listing, respond with a JSON array where each element has:
- "canonical_name": The standardized product name (e.g. "Nike Tech Fleece Joggers", "Apple iPhone 15 Pro 256GB", "Sony WH-1000XM5")
- "brand": The brand name
- "product_line": The product line (e.g. "Tech Fleece", "iPhone", "WH-1000XM")
- "model": Specific model (e.g. "Joggers", "15 Pro", "XM5")
- "specs": An object with relevant specs like size, storage, color, RAM etc.

Important rules:
- The canonical_name should be generic enough to group similar products, but specific enough to distinguish different models
- Include storage/memory in canonical_name for electronics (e.g. "256GB")
- Do NOT include condition, color, or seller info in canonical_name
- If you can't determine the product, use the cleaned title as canonical_name

Listings:
{items_text}

Respond with ONLY a valid JSON array, no explanation. Example:
[{{"canonical_name": "Nike Tech Fleece Joggers", "brand": "Nike", "product_line": "Tech Fleece", "model": "Joggers", "specs": {{}}}}]"""

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/chat",
            json={
                "model": settings.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    content = data.get("message", {}).get("content", "")
    parsed = json.loads(content)

    # Handle case where Ollama wraps in an object
    if isinstance(parsed, dict):
        # Try common wrapper keys
        for key in ("items", "listings", "results", "products"):
            if key in parsed and isinstance(parsed[key], list):
                parsed = parsed[key]
                break
        else:
            parsed = [parsed]

    # Ensure we have one result per listing
    if len(parsed) < len(listings):
        # Pad with regex fallbacks
        for i in range(len(parsed), len(listings)):
            parsed.append(_regex_fallback(listings[i]))

    return parsed[: len(listings)]


def _regex_fallback(listing: dict) -> dict:
    """Extract product info using regex patterns when Ollama is unavailable."""
    title = listing.get("title", "")
    brand = listing.get("brand", "") or ""
    combined = f"{title} {listing.get('description', '')}"

    model = _extract_model(combined)
    storage = _extract_storage(combined)
    clean = _clean_title(title)

    if model:
        canonical = model
        if storage and storage not in canonical:
            canonical += f" {storage}"
    else:
        canonical = clean or title

    # Prepend brand if not already in canonical
    if brand and brand.lower() not in canonical.lower():
        canonical = f"{brand} {canonical}"

    return {
        "canonical_name": canonical.strip(),
        "brand": brand,
        "product_line": "",
        "model": model or "",
        "specs": {"storage": storage} if storage else {},
    }


def _get_or_create_cluster(db, info: dict) -> str:
    """Find or create a product_cluster by canonical_name."""
    canonical = (info.get("canonical_name") or "Unknown").strip()
    if not canonical:
        canonical = "Unknown"

    # Try to find existing
    existing = (
        db.table("product_clusters")
        .select("id")
        .eq("canonical_name", canonical)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    # Create new
    new_cluster = (
        db.table("product_clusters")
        .insert(
            {
                "canonical_name": canonical,
                "brand": info.get("brand", ""),
                "product_line": info.get("product_line", ""),
                "model": info.get("model", ""),
                "specs": info.get("specs", {}),
            }
        )
        .execute()
    )
    return new_cluster.data[0]["id"]
