-- Migration: Add Celery-related fields to products table
-- Purpose: Enable priority-based distributed task processing for 1M+ products

-- Add priority and check count fields
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS check_priority INTEGER DEFAULT 50,
ADD COLUMN IF NOT EXISTS check_count INTEGER DEFAULT 0;

-- Create index on check_priority for fast queries
CREATE INDEX IF NOT EXISTS idx_products_check_priority ON products(check_priority DESC);

-- Create composite index for smart batching
CREATE INDEX IF NOT EXISTS idx_products_priority_checked 
ON products(check_priority DESC, last_checked_at);

-- Create index for available products
CREATE INDEX IF NOT EXISTS idx_products_available_priority 
ON products(is_available, check_priority DESC) 
WHERE is_available = true;

-- Update existing products with initial priority based on current data
UPDATE products
SET check_priority = CASE
    -- Active deals: High priority
    WHEN EXISTS (SELECT 1 FROM deals WHERE deals.product_id = products.id AND deals.is_active = true) THEN 90
    -- High rating + many reviews: Medium-high priority
    WHEN rating >= 4.0 AND review_count >= 100 THEN 70
    -- Good rating: Medium priority
    WHEN rating >= 3.5 THEN 50
    -- Low priority
    ELSE 30
END
WHERE check_priority = 50;  -- Only update defaults

-- Create index on price_history for volatility calculations
CREATE INDEX IF NOT EXISTS idx_price_history_product_date 
ON price_history(product_id, recorded_at DESC);

-- Create index on deals for active deal queries
CREATE INDEX IF NOT EXISTS idx_deals_active_product 
ON deals(is_active, product_id) 
WHERE is_active = true;

-- Add comment
COMMENT ON COLUMN products.check_priority IS 'Priority score (0-100) for smart batch processing. Higher = check more frequently';
COMMENT ON COLUMN products.check_count IS 'Total number of times product price has been checked';
