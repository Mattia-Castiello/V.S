-- Remove Amazon/market columns from opportunities
ALTER TABLE opportunities DROP COLUMN IF EXISTS price_comparison_id;
ALTER TABLE opportunities DROP COLUMN IF EXISTS amazon_price;
ALTER TABLE opportunities DROP COLUMN IF EXISTS market_price;
ALTER TABLE opportunities DROP COLUMN IF EXISTS discount_vs_amazon;
ALTER TABLE opportunities DROP COLUMN IF EXISTS margin_vs_market;
ALTER TABLE opportunities DROP COLUMN IF EXISTS discount_vs_market;

-- Add avg price columns
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS avg_price_same_condition NUMERIC DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS avg_price_all NUMERIC DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS price_vs_avg NUMERIC DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS num_similar INTEGER DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS canonical_name TEXT;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS condition_breakdown JSONB DEFAULT '[]';
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS product_cluster_id UUID;
