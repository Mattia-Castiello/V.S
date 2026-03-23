-- Vinted Intelligence: Initial Schema
-- Run this in Supabase SQL Editor

-- Watchlist items
CREATE TABLE IF NOT EXISTS watchlist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('category', 'product')),
    query TEXT NOT NULL,
    max_price NUMERIC NOT NULL DEFAULT 0,
    min_margin NUMERIC NOT NULL DEFAULT 0,
    conditions TEXT[] DEFAULT '{}',
    size TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Vinted listings
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    price NUMERIC NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    condition TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    url TEXT DEFAULT '',
    published_at TIMESTAMPTZ,
    brand TEXT,
    model TEXT,
    size TEXT,
    seller_id TEXT,
    seller_username TEXT,
    seller_rating NUMERIC,
    category_id INTEGER,
    watchlist_item_id UUID REFERENCES watchlist_items(id) ON DELETE SET NULL,
    raw_json JSONB,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_sold BOOLEAN NOT NULL DEFAULT false
);

-- Price comparisons from SerpAPI
CREATE TABLE IF NOT EXISTS price_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    amazon_price NUMERIC,
    market_price NUMERIC,
    asin TEXT,
    source TEXT NOT NULL DEFAULT 'serpapi',
    search_query TEXT DEFAULT '',
    confidence NUMERIC DEFAULT 0.0,
    raw_response JSONB,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Calculated opportunities
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price_comparison_id UUID REFERENCES price_comparisons(id) ON DELETE SET NULL,
    vinted_price NUMERIC NOT NULL,
    amazon_price NUMERIC,
    market_price NUMERIC,
    margin_absolute NUMERIC DEFAULT 0,
    margin_percent NUMERIC DEFAULT 0,
    discount_vs_amazon NUMERIC DEFAULT 0,
    score TEXT NOT NULL DEFAULT 'low' CHECK (score IN ('high', 'medium', 'low')),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Price history for tracking over time
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id TEXT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price NUMERIC NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Scan logs
CREATE TABLE IF NOT EXISTS scan_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    listings_found INTEGER DEFAULT 0,
    opportunities_found INTEGER DEFAULT 0,
    errors JSONB DEFAULT '[]',
    duration_seconds NUMERIC
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_listings_brand ON listings(brand);
CREATE INDEX IF NOT EXISTS idx_listings_watchlist ON listings(watchlist_item_id);
CREATE INDEX IF NOT EXISTS idx_listings_last_seen ON listings(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_opportunities_active ON opportunities(is_active);
CREATE INDEX IF NOT EXISTS idx_opportunities_score ON opportunities(score);
CREATE INDEX IF NOT EXISTS idx_price_comparisons_listing ON price_comparisons(listing_id);
CREATE INDEX IF NOT EXISTS idx_price_history_listing ON price_history(listing_id);
CREATE INDEX IF NOT EXISTS idx_scan_logs_status ON scan_logs(status);
