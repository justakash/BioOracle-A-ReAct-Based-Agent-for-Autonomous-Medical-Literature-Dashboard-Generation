-- BioOracle PostgreSQL Initialization Script
-- Run automatically on first container start via Docker Compose.

CREATE TABLE IF NOT EXISTS query_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    query_text TEXT NOT NULL,
    intent VARCHAR(64),
    sources_used JSONB,
    status VARCHAR(32) DEFAULT 'running',
    csv_path VARCHAR(512),
    dashboard_config_id VARCHAR(32),
    summary TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds FLOAT
);

CREATE TABLE IF NOT EXISTS dataset_records (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64),
    source VARCHAR(32),
    csv_path VARCHAR(512),
    row_count INTEGER,
    column_names JSONB,
    schema_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dashboard_configs (
    id SERIAL PRIMARY KEY,
    config_id VARCHAR(32) UNIQUE NOT NULL,
    session_id VARCHAR(64),
    title VARCHAR(255),
    config_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    view_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS export_records (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64),
    export_format VARCHAR(16),
    file_path VARCHAR(512),
    file_size_bytes INTEGER,
    email_sent_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_query_history_session ON query_history(session_id);
CREATE INDEX IF NOT EXISTS idx_dataset_records_session ON dataset_records(session_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_session ON dashboard_configs(session_id);
CREATE INDEX IF NOT EXISTS idx_export_records_session ON export_records(session_id);
