-- Product clusters table
CREATE TABLE IF NOT EXISTS product_clusters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL UNIQUE,
    brand TEXT,
    product_line TEXT,
    model TEXT,
    specs JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- FK on listings
ALTER TABLE listings ADD COLUMN IF NOT EXISTS product_cluster_id UUID
    REFERENCES product_clusters(id) ON DELETE SET NULL;

-- FK on opportunities
ALTER TABLE opportunities ADD CONSTRAINT fk_opp_cluster
    FOREIGN KEY (product_cluster_id) REFERENCES product_clusters(id) ON DELETE SET NULL;

-- Cached price stats per cluster + condition
CREATE TABLE IF NOT EXISTS cluster_price_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_cluster_id UUID NOT NULL REFERENCES product_clusters(id) ON DELETE CASCADE,
    condition TEXT NOT NULL,
    avg_price NUMERIC DEFAULT 0,
    min_price NUMERIC DEFAULT 0,
    max_price NUMERIC DEFAULT 0,
    listing_count INTEGER DEFAULT 0,
    computed_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(product_cluster_id, condition)
);
