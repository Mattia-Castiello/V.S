from datetime import datetime

from fastapi import APIRouter, HTTPException
from postgrest import APIError

from backend.database import get_supabase
from backend.models import PurchaseCreate, PurchaseUpdate

router = APIRouter()


def _row_to_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "listingId": row.get("listing_id"),
        "title": row["title"],
        "imageUrl": row.get("image_url") or "",
        "url": row.get("url") or "",
        "brand": row.get("brand"),
        "condition": row.get("condition") or "",
        "vintedPrice": row["vinted_price"],
        "purchasePrice": row["purchase_price"],
        "resalePrice": row.get("resale_price"),
        "sold": row.get("sold") or False,
        "notes": row.get("notes") or "",
        "purchasedAt": row.get("purchased_at"),
        "soldAt": row.get("sold_at"),
    }


MISSING_TABLE_MESSAGE = (
    "Table 'purchases' not found in Supabase. "
    "Run migration 004_purchases.sql (or create the table manually) to enable purchases."
)


def _is_missing_table_error(err: Exception) -> bool:
    return isinstance(err, APIError) and err.code == "PGRST205"


def _raise_missing_table():
    raise HTTPException(status_code=503, detail=MISSING_TABLE_MESSAGE)


@router.get("/api/purchases")
async def get_purchases() -> list[dict]:
    db = get_supabase()
    try:
        result = (
            db.table("purchases").select("*").order("created_at", desc=True).execute()
        )
        return [_row_to_response(row) for row in (result.data or [])]
    except APIError as err:
        if _is_missing_table_error(err):
            # Backend not fully provisioned yet; keep UI functional with an empty list.
            return []
        raise


@router.post("/api/purchases")
async def create_purchase(item: PurchaseCreate) -> dict:
    db = get_supabase()
    data = {
        "listing_id": item.listing_id,
        "title": item.title,
        "image_url": item.image_url,
        "url": item.url,
        "brand": item.brand,
        "condition": item.condition,
        "vinted_price": item.vinted_price,
        "purchase_price": item.purchase_price,
        "resale_price": item.resale_price,
        "notes": item.notes,
    }
    try:
        result = db.table("purchases").insert(data).execute()
    except APIError as err:
        if _is_missing_table_error(err):
            _raise_missing_table()
        raise
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create purchase")
    return _row_to_response(result.data[0])


@router.patch("/api/purchases/{purchase_id}")
async def update_purchase(purchase_id: str, update: PurchaseUpdate) -> dict:
    db = get_supabase()
    data: dict = {}
    if update.purchase_price is not None:
        data["purchase_price"] = update.purchase_price
    if update.resale_price is not None:
        data["resale_price"] = update.resale_price
    if update.sold is not None:
        data["sold"] = update.sold
        if update.sold:
            data["sold_at"] = datetime.utcnow().isoformat()
        else:
            data["sold_at"] = None
    if update.notes is not None:
        data["notes"] = update.notes

    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = db.table("purchases").update(data).eq("id", purchase_id).execute()
    except APIError as err:
        if _is_missing_table_error(err):
            _raise_missing_table()
        raise
    if not result.data:
        raise HTTPException(status_code=404, detail="Purchase not found")
    return _row_to_response(result.data[0])


@router.delete("/api/purchases/{purchase_id}")
async def delete_purchase(purchase_id: str):
    db = get_supabase()
    try:
        db.table("purchases").delete().eq("id", purchase_id).execute()
    except APIError as err:
        if _is_missing_table_error(err):
            _raise_missing_table()
        raise
    return None
