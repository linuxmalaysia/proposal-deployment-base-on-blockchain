-- RCF & DAC Platform Database Schema Definition for Supabase PostgreSQL
-- Governed by DSOM Protocol // Clean Architecture

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    did VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    dept VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    trl INT NOT NULL CHECK (trl >= 1 AND trl <= 9),
    abstract TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    sha256_digest VARCHAR(255) NOT NULL,
    tx_outbox_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cloverleaf_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(255),
    tech_score INT NOT NULL CHECK (tech_score >= 0 AND tech_score <= 60),
    market_score INT NOT NULL CHECK (market_score >= 0 AND market_score <= 80),
    comm_score INT NOT NULL CHECK (comm_score >= 0 AND comm_score <= 60),
    mgmt_score INT NOT NULL CHECK (mgmt_score >= 0 AND mgmt_score <= 60),
    total_score INT NOT NULL CHECK (total_score >= 0 AND total_score <= 260),
    is_qualified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS revenue_splits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_ingested_myr NUMERIC(15, 2) NOT NULL,
    revenue_type VARCHAR(50) NOT NULL,
    distribution_splits JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blockchain_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    asset_symbol VARCHAR(50) NOT NULL,
    amount NUMERIC(28, 8) NOT NULL,
    sync_state VARCHAR(50) NOT NULL,
    block_id BIGINT,
    tx_hash VARCHAR(255),
    retry_count INT DEFAULT 0,
    failure_reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for high-concurrency lookup
CREATE INDEX IF NOT EXISTS idx_users_did ON users(did);
CREATE INDEX IF NOT EXISTS idx_assets_asset_id ON assets(asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_created_at_trl ON assets(created_at, trl);
CREATE INDEX IF NOT EXISTS idx_cloverleaf_asset_id ON cloverleaf_scores(asset_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_id ON blockchain_transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_blockchain_sync_state ON blockchain_transactions(sync_state);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_timestamp_state ON blockchain_transactions(timestamp, sync_state);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_timestamp_asset ON blockchain_transactions(timestamp, asset_symbol);
CREATE INDEX IF NOT EXISTS idx_blockchain_tx_timestamp_account ON blockchain_transactions(timestamp, account_id);

-- TimescaleDB Hypertables & Compression Policy Configuration
-- Converts blockchain_transactions table into a TimescaleDB hypertable partitioned by time
SELECT create_hypertable('blockchain_transactions', 'timestamp', if_not_exists => TRUE);

-- Configure native columnar compression on transaction history (segment by account/asset, order by timestamp)
ALTER TABLE blockchain_transactions SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'account_id, asset_symbol',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Automatically compress transaction history chunks older than 7 days
SELECT add_compression_policy('blockchain_transactions', INTERVAL '7 days', if_not_exists => TRUE);
