-- Migration 004: Purchases tracking table

CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id TEXT REFERENCES listings(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    image_url TEXT DEFAULT '',
    url TEXT DEFAULT '',
    brand TEXT,
    condition TEXT DEFAULT '',
    vinted_price NUMERIC NOT NULL,
    purchase_price NUMERIC NOT NULL,
    resale_price NUMERIC,
    sold BOOLEAN NOT NULL DEFAULT false,
    notes TEXT DEFAULT '',
    purchased_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sold_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_purchases_sold ON purchases(sold);
CREATE INDEX IF NOT EXISTS idx_purchases_listing ON purchases(listing_id);
