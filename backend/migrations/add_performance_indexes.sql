-- Performance Indexes for 1M+ Products
-- Critical indexes for production deployment

-- Products table indexes
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_last_checked ON products(last_checked_at);
CREATE INDEX IF NOT EXISTS idx_products_check_priority ON products(check_priority);
CREATE INDEX IF NOT EXISTS idx_products_created_at ON products(created_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_products_active_priority ON products(is_active, check_priority) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_products_active_last_checked ON products(is_active, last_checked_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active);

-- Deals table indexes
CREATE INDEX IF NOT EXISTS idx_deals_is_active ON deals(is_active);
CREATE INDEX IF NOT EXISTS idx_deals_is_published ON deals(is_published);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_deals_discount_pct ON deals(discount_percentage DESC);
CREATE INDEX IF NOT EXISTS idx_deals_telegram_sent ON deals(telegram_sent);

-- Composite indexes for deals
CREATE INDEX IF NOT EXISTS idx_deals_active_published ON deals(is_active, is_published) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_deals_published_not_sent ON deals(is_published, telegram_sent) WHERE is_published = true AND telegram_sent = false;

-- Price history table indexes
CREATE INDEX IF NOT EXISTS idx_price_history_product_id ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_checked_at ON price_history(checked_at DESC);
CREATE INDEX IF NOT EXISTS idx_price_history_product_date ON price_history(product_id, checked_at DESC);

-- Categories indexes
CREATE INDEX IF NOT EXISTS idx_categories_is_active ON categories(is_active);
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);

-- Worker logs indexes
CREATE INDEX IF NOT EXISTS idx_worker_logs_created_at ON worker_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_worker_logs_status ON worker_logs(status);
CREATE INDEX IF NOT EXISTS idx_worker_logs_job_type ON worker_logs(job_type);

-- Analyze tables for better query planning
ANALYZE products;
ANALYZE deals;
ANALYZE price_history;
ANALYZE categories;

-- Vacuum to reclaim space and update statistics
VACUUM ANALYZE products;
VACUUM ANALYZE deals;
VACUUM ANALYZE price_history;
