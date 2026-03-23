-- Add market margin columns to opportunities table
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS margin_vs_market NUMERIC DEFAULT 0;
ALTER TABLE opportunities ADD COLUMN IF NOT EXISTS discount_vs_market NUMERIC DEFAULT 0;

-- Update default source for new price comparisons
-- Existing rows keep 'serpapi', new ones will use 'trovaprezzi'
COMMENT ON COLUMN price_comparisons.source IS 'Price data source: trovaprezzi or serpapi (legacy)';
