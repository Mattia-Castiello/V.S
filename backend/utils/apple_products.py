# brand_id=319 does not work on vinted.it — the API returns 0 results.
# Text-based search finds Apple products correctly, so we set brand_id=None
# to rely on search terms instead of brand filtering.

# Apple product categories with Vinted search configurations
APPLE_PRODUCTS = [
    {
        "name": "iPhone 16 Pro Max",
        "search_terms": ["iPhone 16 Pro Max"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 500,
        "max_price": 1500,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "iPhone 16 Pro",
        "search_terms": ["iPhone 16 Pro"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 400,
        "max_price": 1400,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "iPhone 16",
        "search_terms": ["iPhone 16"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 300,
        "max_price": 1100,
        "storage_variants": ["128GB", "256GB", "512GB"],
    },
    {
        "name": "iPhone 15 Pro Max",
        "search_terms": ["iPhone 15 Pro Max"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 400,
        "max_price": 1300,
        "storage_variants": ["256GB", "512GB", "1TB"],
    },
    {
        "name": "iPhone 15 Pro",
        "search_terms": ["iPhone 15 Pro"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 350,
        "max_price": 1200,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "iPhone 15",
        "search_terms": ["iPhone 15"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 250,
        "max_price": 900,
        "storage_variants": ["128GB", "256GB", "512GB"],
    },
    {
        "name": "iPhone 14 Pro Max",
        "search_terms": ["iPhone 14 Pro Max"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 300,
        "max_price": 1000,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "iPhone 14 Pro",
        "search_terms": ["iPhone 14 Pro"],
        "category_id": 2405,
        "brand_id": None,
        "min_price": 250,
        "max_price": 900,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "MacBook Pro 14",
        "search_terms": ["MacBook Pro 14"],
        "category_id": 1884,
        "brand_id": None,
        "min_price": 600,
        "max_price": 3000,
        "storage_variants": ["512GB", "1TB", "2TB"],
    },
    {
        "name": "MacBook Pro 16",
        "search_terms": ["MacBook Pro 16"],
        "category_id": 1884,
        "brand_id": None,
        "min_price": 800,
        "max_price": 4000,
        "storage_variants": ["512GB", "1TB", "2TB"],
    },
    {
        "name": "MacBook Air M2",
        "search_terms": ["MacBook Air M2"],
        "category_id": 1884,
        "brand_id": None,
        "min_price": 400,
        "max_price": 1500,
        "storage_variants": ["256GB", "512GB"],
    },
    {
        "name": "MacBook Air M3",
        "search_terms": ["MacBook Air M3"],
        "category_id": 1884,
        "brand_id": None,
        "min_price": 500,
        "max_price": 1800,
        "storage_variants": ["256GB", "512GB", "1TB"],
    },
    {
        "name": "iPad Pro M4",
        "search_terms": ["iPad Pro M4"],
        "category_id": 1886,
        "brand_id": None,
        "min_price": 400,
        "max_price": 2000,
        "storage_variants": ["256GB", "512GB", "1TB", "2TB"],
    },
    {
        "name": "iPad Air M2",
        "search_terms": ["iPad Air M2"],
        "category_id": 1886,
        "brand_id": None,
        "min_price": 300,
        "max_price": 1000,
        "storage_variants": ["128GB", "256GB", "512GB", "1TB"],
    },
    {
        "name": "Apple Watch Ultra 2",
        "search_terms": ["Apple Watch Ultra 2"],
        "category_id": 2387,
        "brand_id": None,
        "min_price": 300,
        "max_price": 900,
        "storage_variants": [],
    },
    {
        "name": "Apple Watch Series 9",
        "search_terms": ["Apple Watch Series 9"],
        "category_id": 2387,
        "brand_id": None,
        "min_price": 150,
        "max_price": 600,
        "storage_variants": [],
    },
    {
        "name": "AirPods Pro 2",
        "search_terms": ["AirPods Pro 2", "AirPods Pro"],
        "category_id": 2403,
        "brand_id": None,
        "min_price": 50,
        "max_price": 300,
        "storage_variants": [],
    },
    {
        "name": "AirPods Max",
        "search_terms": ["AirPods Max"],
        "category_id": 2403,
        "brand_id": None,
        "min_price": 150,
        "max_price": 600,
        "storage_variants": [],
    },
]


def get_search_configs_for_query(query: str) -> list[dict]:
    """Find matching Apple product configs for a watchlist query."""
    query_lower = query.lower()
    matches = []
    for product in APPLE_PRODUCTS:
        if any(term.lower() in query_lower for term in product["search_terms"]):
            matches.append(product)
        elif query_lower in product["name"].lower():
            matches.append(product)
    # If no specific match, return a generic search without brand filter
    if not matches:
        matches.append(
            {
                "name": query,
                "search_terms": [query],
                "brand_id": None,
                "min_price": 0,
                "max_price": 5000,
                "storage_variants": [],
            }
        )
    return matches
