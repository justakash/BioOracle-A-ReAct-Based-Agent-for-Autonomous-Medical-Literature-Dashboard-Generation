-- BioOracle PostgreSQL Initialization Script
-- Run automatically on first container start via Docker Compose.

-- BioOracle PostgreSQL Initialization Script

CREATE TABLE IF NOT EXISTS query_history (
    id                   SERIAL PRIMARY KEY,
    session_id           VARCHAR(64) UNIQUE NOT NULL,
    query_text           TEXT NOT NULL,
    intent               VARCHAR(64),
    sources_used         JSONB,
    status               VARCHAR(32) DEFAULT 'running',
    csv_path             VARCHAR(512),
    dashboard_config_id  VARCHAR(32),
    summary              TEXT,
    error_message        TEXT,
    created_at           TIMESTAMP DEFAULT NOW(),
    completed_at         TIMESTAMP,
    duration_seconds     FLOAT,
    CONSTRAINT chk_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS dataset_records (
    id             SERIAL PRIMARY KEY,
    session_id     VARCHAR(64),
    source         VARCHAR(32),
    csv_path       VARCHAR(512),
    row_count      INTEGER,
    column_names   JSONB,
    schema_json    JSONB,
    created_at     TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_dataset_session
        FOREIGN KEY (session_id) REFERENCES query_history(session_id) ON DELETE CASCADE,
    CONSTRAINT chk_source CHECK (
        source IN ('pubmed', 'clinicaltrials', 'semantic_scholar', 'europe_pmc', 'combined')
    )
);

CREATE TABLE IF NOT EXISTS dashboard_configs (
    id          SERIAL PRIMARY KEY,
    config_id   VARCHAR(32) UNIQUE NOT NULL,
    session_id  VARCHAR(64),
    title       VARCHAR(255),
    config_json JSONB,
    created_at  TIMESTAMP DEFAULT NOW(),
    view_count  INTEGER DEFAULT 0,
    CONSTRAINT fk_dashboard_session
        FOREIGN KEY (session_id) REFERENCES query_history(session_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS export_records (
    id               SERIAL PRIMARY KEY,
    session_id       VARCHAR(64),
    export_format    VARCHAR(16),
    file_path        VARCHAR(512),
    file_size_bytes  INTEGER,
    email_sent_to    VARCHAR(255),
    created_at       TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_export_session
        FOREIGN KEY (session_id) REFERENCES query_history(session_id) ON DELETE SET NULL,
    CONSTRAINT chk_export_format CHECK (
        export_format IN ('csv', 'json', 'pdf', 'xlsx')
    )
);

CREATE TABLE IF NOT EXISTS rag_documents (
    id             SERIAL PRIMARY KEY,
    doc_id         VARCHAR(64) UNIQUE NOT NULL,
    source         VARCHAR(32),
    title          TEXT,
    abstract       TEXT,
    authors        JSONB,
    year           INTEGER,
    url            VARCHAR(512),
    mesh_terms     JSONB,
    embedding_dim  INTEGER,
    indexed_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tool_calls (
    id            SERIAL PRIMARY KEY,
    session_id    VARCHAR(64) NOT NULL,
    step_number   INTEGER,
    tool_name     VARCHAR(64),
    tool_input    JSONB,
    tool_output   JSONB,
    success       BOOLEAN DEFAULT TRUE,
    error_detail  TEXT,
    latency_ms    INTEGER,
    called_at     TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_tool_session
        FOREIGN KEY (session_id) REFERENCES query_history(session_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_qh_session      ON query_history(session_id);
CREATE INDEX IF NOT EXISTS idx_qh_status       ON query_history(status);
CREATE INDEX IF NOT EXISTS idx_qh_created      ON query_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dr_session      ON dataset_records(session_id);
CREATE INDEX IF NOT EXISTS idx_dr_source       ON dataset_records(source);
CREATE INDEX IF NOT EXISTS idx_dc_config_id    ON dashboard_configs(config_id);
CREATE INDEX IF NOT EXISTS idx_dc_session      ON dashboard_configs(session_id);
CREATE INDEX IF NOT EXISTS idx_er_session      ON export_records(session_id);
CREATE INDEX IF NOT EXISTS idx_rd_source       ON rag_documents(source);
CREATE INDEX IF NOT EXISTS idx_rd_year         ON rag_documents(year);
CREATE INDEX IF NOT EXISTS idx_atc_session     ON agent_tool_calls(session_id);
CREATE INDEX IF NOT EXISTS idx_atc_tool        ON agent_tool_calls(tool_name);