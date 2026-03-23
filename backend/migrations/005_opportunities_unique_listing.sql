-- Migration 005: Add UNIQUE constraint on opportunities.listing_id
-- Required for upsert(on_conflict="listing_id") to work correctly in PostgreSQL.
-- Without this, every opportunity creation silently fails with:
-- "there is no unique or exclusion constraint matching the ON CONFLICT specification"

-- Remove any duplicate opportunities first (keep the most recent one per listing)
DELETE FROM opportunities
WHERE id NOT IN (
    SELECT DISTINCT ON (listing_id) id
    FROM opportunities
    ORDER BY listing_id, created_at DESC
);

ALTER TABLE opportunities ADD CONSTRAINT opportunities_listing_id_key UNIQUE (listing_id);
