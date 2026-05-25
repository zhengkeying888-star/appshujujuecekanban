-- ============================================================
-- Neon PostgreSQL Schema for APP Lead Ads Analytics
-- 表设计原则：精简核心字段 + JSONB 扩展字段，兼顾查询性能与分析灵活性
-- ============================================================

-- 1. 后链路线索明细
DROP TABLE IF EXISTS backend_leads;
CREATE TABLE backend_leads (
    id SERIAL PRIMARY KEY,
    stat_month TEXT NOT NULL,
    order_time TIMESTAMP,
    tag_level_1 TEXT,              -- 广告资源位（标准化后的名称）
    category_name TEXT,
    camp_name TEXT,
    sku_price NUMERIC,
    is_add_friend INTEGER,
    first_order_count INTEGER,     -- 首单数
    first_order_revenue NUMERIC,   -- 首单流水
    attended INTEGER,              -- 是否到课（总）
    ltv NUMERIC,
    lead_count INTEGER DEFAULT 1,  -- 线索数（原始数据每行=1）
    user_id TEXT,
    sex TEXT,
    age TEXT,
    city TEXT,
    growth_level TEXT,
    -- 完课/到课明细用 JSONB 存储，避免108列宽表
    completion_json JSONB,         -- {先导课:0, 第1节:1, ...}
    attendance_json JSONB,         -- {先导课:1, 第1节:1, ...}
    raw_json JSONB,                -- 原始完整行数据（未来扩展用）
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_backend_month ON backend_leads(stat_month);
CREATE INDEX idx_backend_resource ON backend_leads(tag_level_1);
CREATE INDEX idx_backend_category ON backend_leads(category_name);
CREATE INDEX idx_backend_time ON backend_leads(order_time);
CREATE INDEX idx_backend_month_resource ON backend_leads(stat_month, tag_level_1);

-- 2. 前链路日汇总
DROP TABLE IF EXISTS frontend_daily;
CREATE TABLE frontend_daily (
    id SERIAL PRIMARY KEY,
    data_date DATE NOT NULL,
    stat_month TEXT NOT NULL,
    ad_name TEXT,                  -- 原始广告位名称
    resource TEXT,                 -- 标准化后的资源位（经 AD_NAME_MAP 映射）
    category_name TEXT,
    exposure_uv INTEGER,
    click_uv INTEGER,
    sales_page_uv INTEGER,         -- 售卖页浏览UV
    leads INTEGER,
    first_orders INTEGER,
    first_order_amount NUMERIC,
    sku_price NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_frontend_date ON frontend_daily(data_date);
CREATE INDEX idx_frontend_month ON frontend_daily(stat_month);
CREATE INDEX idx_frontend_resource ON frontend_daily(resource);
CREATE INDEX idx_frontend_month_resource ON frontend_daily(stat_month, resource);

-- 3. 月活数据（用户等级维度）
DROP TABLE IF EXISTS mau_monthly;
CREATE TABLE mau_monthly (
    id SERIAL PRIMARY KEY,
    stat_month TEXT NOT NULL,
    user_level INTEGER,
    mau INTEGER,
    ratio NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_mau_month ON mau_monthly(stat_month);

-- 4. 日活数据（精简：仅保留日期 + DAU + 新用户数）
DROP TABLE IF EXISTS daily_dau;
CREATE TABLE daily_dau (
    id SERIAL PRIMARY KEY,
    data_date DATE NOT NULL UNIQUE,
    dau INTEGER,
    new_users INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dau_date ON daily_dau(data_date);

-- 5. 品类映射（正式品/孵化品 + 兴趣线/健康线/变美线）
DROP TABLE IF EXISTS category_mapping;
CREATE TABLE category_mapping (
    id SERIAL PRIMARY KEY,
    category_name TEXT UNIQUE NOT NULL,
    cat_type TEXT,                 -- 正式品 / 孵化品
    cat_attr TEXT,                 -- 兴趣线 / 健康线 / 变美线
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cat_name ON category_mapping(category_name);
