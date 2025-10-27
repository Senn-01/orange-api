-- ============================================================================
-- Orange Belgium Subscription API - Database Schema
-- ============================================================================
-- Purpose: Support chatbot queries for subscription bundles and pricing
-- Database: PostgreSQL 14+
-- ============================================================================

-- Enable UUID extension for future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. GROUPS TABLE
-- ============================================================================
-- Product categories: Internet, Mobile, TV, Extra
-- ============================================================================

CREATE TABLE groups (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '54776'
    name VARCHAR(100) NOT NULL,  -- e.g., 'Internet'
    slug VARCHAR(50) NOT NULL UNIQUE,  -- e.g., 'internet'
    description TEXT,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_groups_slug ON groups(slug);

COMMENT ON TABLE groups IS 'Product categories (Internet, Mobile, TV, Extra)';
COMMENT ON COLUMN groups.display_order IS 'Order for UI display';

-- ============================================================================
-- 2. PRODUCTS TABLE
-- ============================================================================
-- Main subscription products (Internet plans, Mobile plans, TV packages)
-- ============================================================================

CREATE TABLE products (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '54801'
    internal_name VARCHAR(100),  -- e.g., 'Zen Fiber'
    display_name VARCHAR(200) NOT NULL,  -- e.g., 'Internet illimité 500 Mbps'
    slug VARCHAR(100) NOT NULL,  -- e.g., 'net-m'
    epc_id VARCHAR(50),  -- External Product Code for billing, e.g., 'AO005017'
    group_id VARCHAR(20) NOT NULL REFERENCES groups(id),
    
    -- Pricing
    monthly_price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    device_fee DECIMAL(10, 2) DEFAULT 0,
    activation_fee DECIMAL(10, 2) DEFAULT 0,
    installation_fee DECIMAL(10, 2) DEFAULT 0,
    
    -- Product specifications (stored as JSON for flexibility)
    specs JSONB DEFAULT '{}',
    -- Example: {"speed": 500, "data": "unlimited", "channels": 100}
    
    -- Display information
    description TEXT,
    card_title VARCHAR(200),
    card_subtitle VARCHAR(200),
    summary_title VARCHAR(200),
    modal_content TEXT,
    
    -- Metadata
    weight INTEGER DEFAULT 0,  -- For sorting
    labels JSONB DEFAULT '[]',  -- Display badges/labels
    rules JSONB DEFAULT '[]',  -- Product-specific rules
    footprints JSONB DEFAULT '[]',  -- Regional availability
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_group ON products(group_id);
CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_active ON products(is_active);
CREATE INDEX idx_products_price ON products(monthly_price);
CREATE INDEX idx_products_specs ON products USING gin(specs);

COMMENT ON TABLE products IS 'Main subscription products (Internet, Mobile, TV)';
COMMENT ON COLUMN products.epc_id IS 'External Product Code used in billing systems';
COMMENT ON COLUMN products.specs IS 'JSON: product attributes like speed, data, channels';
COMMENT ON COLUMN products.weight IS 'Display order within group';
COMMENT ON COLUMN products.footprints IS 'Regional availability (e.g., Wallonie, Bruxelles)';

-- ============================================================================
-- 3. OPTIONS TABLE
-- ============================================================================
-- Add-ons that can be combined with products (Netflix, WiFi Comfort, etc.)
-- ============================================================================

CREATE TABLE options (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '54891'
    name VARCHAR(200) NOT NULL,  -- e.g., 'Netflix'
    slug VARCHAR(100),
    description TEXT,
    
    -- Pricing
    monthly_price DECIMAL(10, 2) NOT NULL DEFAULT 0,
    device_fee DECIMAL(10, 2) DEFAULT 0,
    activation_fee DECIMAL(10, 2) DEFAULT 0,
    
    -- Metadata
    option_type VARCHAR(50),  -- e.g., 'streaming', 'service', 'hardware'
    specs JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_options_active ON options(is_active);
CREATE INDEX idx_options_type ON options(option_type);

COMMENT ON TABLE options IS 'Add-on services (Netflix, WiFi Comfort, TV channels, etc.)';

-- ============================================================================
-- 4. CONFIGURATORS TABLE
-- ============================================================================
-- Bundle templates that define valid product combinations
-- ============================================================================

CREATE TABLE configurators (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '54896'
    name VARCHAR(200) NOT NULL,  -- e.g., 'Configurateur'
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    weight INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE configurators IS 'Bundle templates defining valid product combinations';

-- ============================================================================
-- 5. CONFIGURATOR_PRODUCTS TABLE (Junction)
-- ============================================================================
-- Links configurators to allowed products
-- ============================================================================

CREATE TABLE configurator_products (
    configurator_id VARCHAR(20) REFERENCES configurators(id) ON DELETE CASCADE,
    product_id VARCHAR(20) REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (configurator_id, product_id)
);

CREATE INDEX idx_conf_products_conf ON configurator_products(configurator_id);
CREATE INDEX idx_conf_products_prod ON configurator_products(product_id);

COMMENT ON TABLE configurator_products IS 'Defines which products can be bundled together';

-- ============================================================================
-- 6. CONFIGURATOR_OPTIONS TABLE (Junction)
-- ============================================================================
-- Links configurators to allowed options
-- ============================================================================

CREATE TABLE configurator_options (
    configurator_id VARCHAR(20) REFERENCES configurators(id) ON DELETE CASCADE,
    option_id VARCHAR(20) REFERENCES options(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (configurator_id, option_id)
);

CREATE INDEX idx_conf_options_conf ON configurator_options(configurator_id);
CREATE INDEX idx_conf_options_opt ON configurator_options(option_id);

COMMENT ON TABLE configurator_options IS 'Defines which options can be added to bundles';

-- ============================================================================
-- 7. PRICE_RULES TABLE
-- ============================================================================
-- PERMANENT bundle discounts (Avantage à vie / multi-produits)
-- Applied when combining products from different groups
-- ============================================================================

CREATE TABLE price_rules (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '55001'
    name VARCHAR(200) NOT NULL,  -- e.g., 'Avantage multi-produits'
    description TEXT,
    
    -- Calculation
    calculation_method VARCHAR(20) NOT NULL,  -- 'amount', 'percentage'
    calculation_value DECIMAL(10, 2) NOT NULL,  -- e.g., 4.00 for -€4
    
    -- Application rules (stored as JSON)
    rules JSONB DEFAULT '[]',
    -- Example: [{"type": "hasProductInGroup", "parameters": ["54776"]}]
    
    -- Priority for stacking
    calculation_order INTEGER DEFAULT 50,
    
    -- Metadata
    legal_summary TEXT,
    legal_info TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_price_rules_active ON price_rules(is_active);
CREATE INDEX idx_price_rules_order ON price_rules(calculation_order);
CREATE INDEX idx_price_rules_rules ON price_rules USING gin(rules);

COMMENT ON TABLE price_rules IS 'PERMANENT bundle discounts (Avantage à vie)';
COMMENT ON COLUMN price_rules.calculation_method IS 'How discount is calculated: amount (fixed €) or percentage (%)';
COMMENT ON COLUMN price_rules.rules IS 'JSON array of conditions that must be met';
COMMENT ON COLUMN price_rules.calculation_order IS 'Order of application when stacking (lower = first)';

-- ============================================================================
-- 8. PRICE_RULE_PRODUCTS TABLE (Junction)
-- ============================================================================
-- Defines which products a price rule applies to
-- ============================================================================

CREATE TABLE price_rule_products (
    price_rule_id VARCHAR(20) REFERENCES price_rules(id) ON DELETE CASCADE,
    product_id VARCHAR(20) REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (price_rule_id, product_id)
);

CREATE INDEX idx_price_rule_prod_rule ON price_rule_products(price_rule_id);
CREATE INDEX idx_price_rule_prod_prod ON price_rule_products(product_id);

COMMENT ON TABLE price_rule_products IS 'Links price rules to products they discount';

-- ============================================================================
-- 9. PROMOTIONS TABLE
-- ============================================================================
-- TIME-LIMITED promotional discounts (6-12 months duration)
-- ============================================================================

CREATE TABLE promotions (
    id VARCHAR(20) PRIMARY KEY,  -- e.g., '55441'
    name VARCHAR(200) NOT NULL,  -- e.g., 'Promo : -15€ pendant 12 mois'
    promo_type VARCHAR(50) NOT NULL,  -- 'discount', 'activationFee', 'data'
    
    -- Calculation
    calculation_method VARCHAR(20) NOT NULL,  -- 'amount', 'percentage', 'free'
    calculation_value DECIMAL(10, 2) DEFAULT 0,  -- e.g., 15.00 for -€15
    duration_months INTEGER DEFAULT 0,  -- How many months the promo lasts
    
    -- Time constraints
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    
    -- Application rules
    rules JSONB DEFAULT '[]',
    -- Example: [{"type": "hasProductInGroup", "parameters": ["54781"]}]
    
    -- Stacking logic
    calculation_order INTEGER DEFAULT 50,
    excluded_promos JSONB DEFAULT '[]',  -- Array of promo IDs that conflict
    
    -- Display
    labels JSONB DEFAULT '[]',  -- e.g., [{"name": "Black Friday", "style": "orange"}]
    specs JSONB DEFAULT '{}',  -- Display info like description
    
    -- Legal text
    legal_summary TEXT,
    legal_info TEXT,
    
    -- Metadata
    is_choice BOOLEAN DEFAULT FALSE,  -- User must actively choose this promo
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_promotions_active ON promotions(is_active);
CREATE INDEX idx_promotions_dates ON promotions(start_date, end_date);
CREATE INDEX idx_promotions_type ON promotions(promo_type);
CREATE INDEX idx_promotions_order ON promotions(calculation_order);
CREATE INDEX idx_promotions_rules ON promotions USING gin(rules);

COMMENT ON TABLE promotions IS 'TIME-LIMITED promotional offers (typically 6-12 months)';
COMMENT ON COLUMN promotions.duration_months IS 'How long the discount lasts after activation';
COMMENT ON COLUMN promotions.start_date IS 'When the promotion becomes available';
COMMENT ON COLUMN promotions.end_date IS 'When the promotion expires (last day to subscribe)';
COMMENT ON COLUMN promotions.excluded_promos IS 'JSON array of promotion IDs that cannot stack with this one';
COMMENT ON COLUMN promotions.is_choice IS 'Whether customer must explicitly opt-in';

-- ============================================================================
-- 10. PROMOTION_PRODUCTS TABLE (Junction)
-- ============================================================================
-- Defines which products a promotion applies to
-- ============================================================================

CREATE TABLE promotion_products (
    promotion_id VARCHAR(20) REFERENCES promotions(id) ON DELETE CASCADE,
    product_id VARCHAR(20) REFERENCES products(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (promotion_id, product_id)
);

CREATE INDEX idx_promo_prod_promo ON promotion_products(promotion_id);
CREATE INDEX idx_promo_prod_prod ON promotion_products(product_id);

COMMENT ON TABLE promotion_products IS 'Links promotions to products they discount';

-- ============================================================================
-- 11. PROMOTION_OPTIONS TABLE (Junction)
-- ============================================================================
-- Defines which options a promotion applies to
-- ============================================================================

CREATE TABLE promotion_options (
    promotion_id VARCHAR(20) REFERENCES promotions(id) ON DELETE CASCADE,
    option_id VARCHAR(20) REFERENCES options(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (promotion_id, option_id)
);

CREATE INDEX idx_promo_opt_promo ON promotion_options(promotion_id);
CREATE INDEX idx_promo_opt_opt ON promotion_options(option_id);

COMMENT ON TABLE promotion_options IS 'Links promotions to options they affect';

-- ============================================================================
-- 12. PROMO_CODES TABLE
-- ============================================================================
-- Special codes for promotions (if needed in future)
-- ============================================================================

CREATE TABLE promo_codes (
    id VARCHAR(20) PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    promotion_id VARCHAR(20) REFERENCES promotions(id) ON DELETE CASCADE,
    description TEXT,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_promo_codes_code ON promo_codes(code);
CREATE INDEX idx_promo_codes_active ON promo_codes(is_active);

COMMENT ON TABLE promo_codes IS 'Special promotional codes (for targeted campaigns)';

-- ============================================================================
-- 13. DATA SYNC LOG TABLE
-- ============================================================================
-- Track when Orange JSON data was last imported
-- ============================================================================

CREATE TABLE data_sync_log (
    id SERIAL PRIMARY KEY,
    sync_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_url VARCHAR(500),
    records_imported INTEGER,
    sync_status VARCHAR(20),  -- 'success', 'failed', 'partial'
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sync_log_date ON data_sync_log(sync_date DESC);

COMMENT ON TABLE data_sync_log IS 'Tracks imports from Orange API JSON';

-- ============================================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================================

-- View: Active products with group info
CREATE OR REPLACE VIEW v_active_products AS
SELECT 
    p.id,
    p.display_name,
    p.slug,
    p.monthly_price,
    p.activation_fee,
    p.specs,
    g.id as group_id,
    g.name as group_name,
    g.slug as group_slug
FROM products p
JOIN groups g ON p.group_id = g.id
WHERE p.is_active = TRUE;

-- View: Active promotions (current date)
CREATE OR REPLACE VIEW v_current_promotions AS
SELECT 
    id,
    name,
    promo_type,
    calculation_method,
    calculation_value,
    duration_months,
    start_date,
    end_date,
    rules,
    legal_summary
FROM promotions
WHERE is_active = TRUE
  AND start_date <= CURRENT_TIMESTAMP
  AND end_date >= CURRENT_TIMESTAMP;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function: Get all products in a bundle
CREATE OR REPLACE FUNCTION get_bundle_products(config_id VARCHAR)
RETURNS TABLE (
    product_id VARCHAR,
    product_name VARCHAR,
    monthly_price DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.display_name,
        p.monthly_price
    FROM products p
    JOIN configurator_products cp ON p.id = cp.product_id
    WHERE cp.configurator_id = config_id
      AND p.is_active = TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function: Check if products can be bundled together
CREATE OR REPLACE FUNCTION can_bundle_products(product_ids VARCHAR[])
RETURNS BOOLEAN AS $$
DECLARE
    config_count INTEGER;
BEGIN
    -- Find configurators that contain ALL the given products
    SELECT COUNT(DISTINCT configurator_id) INTO config_count
    FROM configurator_products
    WHERE product_id = ANY(product_ids)
    GROUP BY configurator_id
    HAVING COUNT(DISTINCT product_id) = array_length(product_ids, 1);
    
    RETURN config_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Function: Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers to all tables with updated_at
CREATE TRIGGER update_groups_updated_at BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_options_updated_at BEFORE UPDATE ON options
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_price_rules_updated_at BEFORE UPDATE ON price_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promotions_updated_at BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

COMMENT ON DATABASE current_database() IS 'Orange Belgium Subscription API - Bundle pricing and recommendations';
