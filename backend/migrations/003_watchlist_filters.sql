-- Migration 003: Add full Vinted filters to watchlist_items and extra fields to listings

-- Watchlist: new filter columns
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS min_price NUMERIC DEFAULT 0;
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS brand_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS catalog_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS size_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS color_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS material_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS status_ids INTEGER[] DEFAULT '{}';
ALTER TABLE watchlist_items ADD COLUMN IF NOT EXISTS sort_order TEXT DEFAULT 'newest_first';

-- Listings: extra info from Vinted API
ALTER TABLE listings ADD COLUMN IF NOT EXISTS photos JSONB DEFAULT '[]';
ALTER TABLE listings ADD COLUMN IF NOT EXISTS total_item_price NUMERIC;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS service_fee NUMERIC;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS color1 TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS color2 TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS material TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS favourite_count INTEGER DEFAULT 0;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS view_count INTEGER DEFAULT 0;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS country TEXT;
