-- Add SEO fields to categories table
-- Migration: add_category_seo_fields
-- Date: 2025-11-12

ALTER TABLE categories 
ADD COLUMN IF NOT EXISTS meta_title VARCHAR(255),
ADD COLUMN IF NOT EXISTS meta_description TEXT,
ADD COLUMN IF NOT EXISTS meta_keywords TEXT,
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Create index for better ordering
CREATE INDEX IF NOT EXISTS idx_categories_display_order ON categories(display_order, name);

-- Add comment
COMMENT ON COLUMN categories.meta_title IS 'SEO meta title for category page';
COMMENT ON COLUMN categories.meta_description IS 'SEO meta description for category page';
COMMENT ON COLUMN categories.meta_keywords IS 'SEO keywords (comma separated)';
COMMENT ON COLUMN categories.display_order IS 'Display order for category listing';
