-- PostgreSQL Initialization Script for MCP Crypto Trading
-- Creates crypto_trading database with required tables and indexes
-- Security hardened - Production ready
-- Last Updated: 2025-09-21

-- Create crypto_trading database (if not exists)
SELECT 'CREATE DATABASE crypto_trading'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'crypto_trading');

-- Connect to crypto_trading database
\c crypto_trading;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create enum types
CREATE TYPE signal_type AS ENUM ('BUY', 'SELL', 'HOLD');
CREATE TYPE position_type AS ENUM ('LONG', 'SHORT');

-- Market data table
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(20,8),
    high DECIMAL(20,8),
    low DECIMAL(20,8),
    open_price DECIMAL(20,8),
    close_price DECIMAL(20,8),
    source VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trading signals table
CREATE TABLE IF NOT EXISTS trading_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    signal_type signal_type NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    confidence DECIMAL(5,4) CHECK (confidence >= 0 AND confidence <= 1),
    indicators JSONB,
    target_price DECIMAL(20,8),
    stop_loss DECIMAL(20,8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Portfolio positions table
CREATE TABLE IF NOT EXISTS portfolio_positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    current_price DECIMAL(20,8),
    position_type position_type NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    exit_price DECIMAL(20,8),
    exit_timestamp TIMESTAMPTZ,
    pnl DECIMAL(20,8),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Risk management table
CREATE TABLE IF NOT EXISTS risk_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    portfolio_value DECIMAL(20,8),
    total_exposure DECIMAL(20,8),
    var_95 DECIMAL(20,8),
    sharpe_ratio DECIMAL(10,6),
    max_drawdown DECIMAL(5,4),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_timestamp ON trading_signals(symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_trading_signals_signal_type ON trading_signals(signal_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_symbol ON portfolio_positions(symbol);
CREATE INDEX IF NOT EXISTS idx_portfolio_positions_timestamp ON portfolio_positions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_risk_metrics_timestamp ON risk_metrics(timestamp DESC);

-- Create partitioning for market_data by date (for large datasets)
-- Enable for high-volume production environments
-- Example: Monthly partitions for better performance
-- CREATE TABLE market_data_y2025m01 PARTITION OF market_data
-- FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
-- CREATE TABLE market_data_y2025m02 PARTITION OF market_data
-- FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Grant permissions (user creation handled by environment variables)
-- Note: User creation is handled by docker-compose environment variables
-- This script assumes POSTGRES_USER already exists from container initialization
GRANT CONNECT ON DATABASE crypto_trading TO :"POSTGRES_USER";
GRANT USAGE ON SCHEMA public TO :"POSTGRES_USER";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO :"POSTGRES_USER";
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO :"POSTGRES_USER";

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :"POSTGRES_USER";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO :"POSTGRES_USER";

-- Log initialization with metadata
INSERT INTO risk_metrics (timestamp, portfolio_value, total_exposure)
VALUES (NOW(), 0, 0);

-- Create audit log for database initialization
CREATE TABLE IF NOT EXISTS system_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    event_description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_name VARCHAR(50)
);

INSERT INTO system_audit (event_type, event_description, user_name)
VALUES ('DATABASE_INIT', 'Crypto trading database initialized successfully', current_user);

SELECT 'PostgreSQL crypto_trading database initialized successfully' AS status;