from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

# --- Watchlist ---


class WatchlistItemCreate(BaseModel):
    type: str  # 'category' | 'product'
    query: str
    max_price: float = Field(alias="maxPrice")
    min_price: float = Field(default=0, alias="minPrice")
    min_margin: float = Field(alias="minMargin")
    conditions: list[str] = []
    size: Optional[str] = None
    brand_ids: list[int] = Field(default=[], alias="brandIds")
    catalog_ids: list[int] = Field(default=[], alias="catalogIds")
    size_ids: list[int] = Field(default=[], alias="sizeIds")
    color_ids: list[int] = Field(default=[], alias="colorIds")
    material_ids: list[int] = Field(default=[], alias="materialIds")
    status_ids: list[int] = Field(default=[], alias="statusIds")
    sort_order: str = Field(default="newest_first", alias="sortOrder")
    active: bool = True

    model_config = {"populate_by_name": True}


class WatchlistItem(BaseModel):
    id: str
    type: str
    query: str
    max_price: float = Field(alias="maxPrice", serialization_alias="maxPrice")
    min_price: float = Field(
        default=0, alias="minPrice", serialization_alias="minPrice"
    )
    min_margin: float = Field(alias="minMargin", serialization_alias="minMargin")
    conditions: list[str] = []
    size: Optional[str] = None
    brand_ids: list[int] = Field(
        default=[], alias="brandIds", serialization_alias="brandIds"
    )
    catalog_ids: list[int] = Field(
        default=[], alias="catalogIds", serialization_alias="catalogIds"
    )
    size_ids: list[int] = Field(
        default=[], alias="sizeIds", serialization_alias="sizeIds"
    )
    color_ids: list[int] = Field(
        default=[], alias="colorIds", serialization_alias="colorIds"
    )
    material_ids: list[int] = Field(
        default=[], alias="materialIds", serialization_alias="materialIds"
    )
    status_ids: list[int] = Field(
        default=[], alias="statusIds", serialization_alias="statusIds"
    )
    sort_order: str = Field(
        default="newest_first", alias="sortOrder", serialization_alias="sortOrder"
    )
    active: bool = True

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Listings ---


class VintedListing(BaseModel):
    id: str
    title: str
    description: str = ""
    price: float
    currency: str = "EUR"
    condition: str = ""
    image_url: str = Field(default="", alias="imageUrl", serialization_alias="imageUrl")
    url: str = ""
    published_at: Optional[str] = Field(
        default=None, alias="publishedAt", serialization_alias="publishedAt"
    )
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    seller_id: Optional[str] = None
    seller_username: Optional[str] = None
    seller_rating: Optional[float] = None
    category_id: Optional[int] = None
    photos: list[dict] = []
    total_item_price: Optional[float] = Field(
        default=None, alias="totalItemPrice", serialization_alias="totalItemPrice"
    )
    service_fee: Optional[float] = Field(
        default=None, alias="serviceFee", serialization_alias="serviceFee"
    )
    color1: Optional[str] = None
    color2: Optional[str] = None
    material: Optional[str] = None
    favourite_count: int = Field(
        default=0, alias="favouriteCount", serialization_alias="favouriteCount"
    )
    view_count: int = Field(
        default=0, alias="viewCount", serialization_alias="viewCount"
    )
    city: Optional[str] = None
    country: Optional[str] = None

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Opportunity ---


class Opportunity(BaseModel):
    id: str
    title: str
    description: str = ""
    price: float
    condition: str = ""
    image_url: str = Field(default="", alias="imageUrl", serialization_alias="imageUrl")
    url: str = ""
    published_at: Optional[str] = Field(
        default=None, alias="publishedAt", serialization_alias="publishedAt"
    )
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    seller_username: Optional[str] = Field(
        default=None, alias="sellerUsername", serialization_alias="sellerUsername"
    )
    seller_rating: Optional[float] = Field(
        default=None, alias="sellerRating", serialization_alias="sellerRating"
    )
    photos: list[dict] = []
    favourite_count: int = Field(
        default=0, alias="favouriteCount", serialization_alias="favouriteCount"
    )
    view_count: int = Field(
        default=0, alias="viewCount", serialization_alias="viewCount"
    )
    city: Optional[str] = None
    country: Optional[str] = None
    avg_price_same_condition: float = Field(
        default=0,
        alias="avgPriceSameCondition",
        serialization_alias="avgPriceSameCondition",
    )
    avg_price_all: float = Field(
        default=0, alias="avgPriceAll", serialization_alias="avgPriceAll"
    )
    margin_absolute: float = Field(
        default=0, alias="marginAbsolute", serialization_alias="marginAbsolute"
    )
    price_vs_avg: float = Field(
        default=0, alias="priceVsAvg", serialization_alias="priceVsAvg"
    )
    num_similar: int = Field(
        default=0, alias="numSimilar", serialization_alias="numSimilar"
    )
    canonical_name: Optional[str] = Field(
        default=None, alias="canonicalName", serialization_alias="canonicalName"
    )
    condition_breakdown: list[dict] = Field(
        default=[],
        alias="conditionBreakdown",
        serialization_alias="conditionBreakdown",
    )
    score: str = "low"  # 'high' | 'medium' | 'low'

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Dashboard Stats ---


class DashboardStats(BaseModel):
    total_monitored: int = Field(
        default=0, alias="totalMonitored", serialization_alias="totalMonitored"
    )
    opportunities_found: int = Field(
        default=0, alias="opportunitiesFound", serialization_alias="opportunitiesFound"
    )
    avg_margin: float = Field(
        default=0, alias="avgMargin", serialization_alias="avgMargin"
    )
    potential_profit: float = Field(
        default=0, alias="potentialProfit", serialization_alias="potentialProfit"
    )

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Purchases ---


class PurchaseCreate(BaseModel):
    listing_id: Optional[str] = Field(default=None, alias="listingId")
    title: str
    image_url: str = Field(default="", alias="imageUrl")
    url: str = ""
    brand: Optional[str] = None
    condition: str = ""
    vinted_price: float = Field(alias="vintedPrice")
    purchase_price: float = Field(alias="purchasePrice")
    resale_price: Optional[float] = Field(default=None, alias="resalePrice")
    notes: str = ""

    model_config = {"populate_by_name": True}


class PurchaseUpdate(BaseModel):
    purchase_price: Optional[float] = Field(default=None, alias="purchasePrice")
    resale_price: Optional[float] = Field(default=None, alias="resalePrice")
    sold: Optional[bool] = None
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}


class Purchase(BaseModel):
    id: str
    listing_id: Optional[str] = Field(
        default=None, alias="listingId", serialization_alias="listingId"
    )
    title: str
    image_url: str = Field(default="", alias="imageUrl", serialization_alias="imageUrl")
    url: str = ""
    brand: Optional[str] = None
    condition: str = ""
    vinted_price: float = Field(alias="vintedPrice", serialization_alias="vintedPrice")
    purchase_price: float = Field(
        alias="purchasePrice", serialization_alias="purchasePrice"
    )
    resale_price: Optional[float] = Field(
        default=None, alias="resalePrice", serialization_alias="resalePrice"
    )
    sold: bool = False
    notes: str = ""
    purchased_at: Optional[str] = Field(
        default=None, alias="purchasedAt", serialization_alias="purchasedAt"
    )
    sold_at: Optional[str] = Field(
        default=None, alias="soldAt", serialization_alias="soldAt"
    )

    model_config = {"populate_by_name": True, "by_alias": True}


# --- Health ---


class HealthStatus(BaseModel):
    status: str = "ok"
    vinted_session: str = "inactive"
    next_scan: Optional[str] = None
    last_scan: Optional[str] = None
    listings_count: int = 0
    opportunities_count: int = 0
