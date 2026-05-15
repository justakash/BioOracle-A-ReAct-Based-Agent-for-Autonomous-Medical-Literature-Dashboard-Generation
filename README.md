# BioOracle

A ReAct Based Agent for Autonomous Medical Literature Dashboard Generation

BioOracle converts natural language biomedical queries into interactive, data-driven dashboards by orchestrating a pipeline of biomedical APIs, an ETL layer, an optional RAG module, and a Plotly Dash visualization engine -- all coordinated by a Claude-powered ReAct agent.

---

# BioOracle Webpage Link: 
https://v0-optimus-the-ai-platform-to-iy547lf5k.vercel.app/

---

## Project Overview

BioOracle bridges the gap between complex biomedical data sources and end-users who need actionable insights without writing custom scripts. A single natural language query such as "Show me GLP-1 clinical trial trends from 2018 to 2024" triggers the full pipeline automatically.

**Core Model:** Claude Sonnet 4.6 (Anthropic)

**Data Sources:**
- PubMed / NCBI (publications, MeSH terms, authors)
- ClinicalTrials.gov (trial phases, status, geography)
- Semantic Scholar (citations, open-access papers)
- Europe PMC (full-text open-access articles)

**Visualization:** Plotly Dash (interactive, browser-based)

---

## Folder Structure

```
biooracle/
|
|-- main.py                         # Application entry point
|-- requirements.txt                # Python dependencies
|-- Dockerfile                      # Container build definition
|-- docker-compose.yml              # Full stack: API + worker + DB + Redis
|-- .env.example                    # Environment variable template
|-- .gitignore
|-- README.md
|
|-- agent/                          # ReAct agent core
|   |-- __init__.py
|   |-- react_agent.py              # Main ReAct loop (Claude API)
|   |-- tools.py                    # Tool definitions and handlers
|   |-- prompt.py                   # System prompt
|
|-- api/                            # FastAPI web server
|   |-- __init__.py
|   |-- server.py                   # App factory, CORS, routers
|   |-- routes/
|   |   |-- __init__.py
|   |   |-- health.py               # GET /health/
|   |   |-- query.py                # POST /api/v1/query/
|   |   |-- dashboard.py            # GET /api/v1/dashboard/{id}
|   |   |-- export.py               # GET /api/v1/export/{format}/{id}
|   |-- connectors/
|       |-- __init__.py
|       |-- pubmed.py               # NCBI E-utilities connector
|       |-- clinicaltrials.py       # ClinicalTrials.gov API v2 connector
|       |-- semantic_scholar.py     # Semantic Scholar Graph API connector
|       |-- europe_pmc.py           # Europe PMC REST API connector
|
|-- etl/                            # Data processing pipeline
|   |-- __init__.py
|   |-- pipeline.py                 # Extract, clean, normalize, save CSV
|   |-- schema_inspector.py         # CSV schema analysis for agent
|   |-- mesh_processor.py           # MeSH term frequency and trend analysis
|
|-- rag/                            # Retrieval-Augmented Generation
|   |-- __init__.py
|   |-- indexer.py                  # FAISS vector index builder
|   |-- retriever.py                # Semantic search and context assembly
|
|-- dashboard/                      # Visualization layer
|   |-- __init__.py
|   |-- renderer.py                 # Dashboard config to HTML/Dash converter
|   |-- chart_builder.py            # Plotly chart factory functions
|
|-- storage/                        # Persistence layer
|   |-- __init__.py
|   |-- database.py                 # SQLAlchemy engine and session
|   |-- models.py                   # ORM models (query history, datasets, configs)
|   |-- cache.py                    # Redis cache helpers
|
|-- utils/                          # Shared utilities
|   |-- __init__.py
|   |-- exporter.py                 # CSV, JSON, PDF export logic
|   |-- emailer.py                  # SMTP report delivery
|   |-- celery_app.py               # Celery configuration
|   |-- tasks.py                    # Background task definitions
|   |-- logger.py                   # Loguru configuration
|
|-- scripts/
|   |-- init_db.sql                 # PostgreSQL schema initialization
|   |-- seed_rag.py                 # Seed the FAISS RAG index
|
|-- tests/
|   |-- __init__.py
|   |-- test_connectors.py          # Unit tests for API connectors
|   |-- test_etl.py                 # Unit tests for ETL pipeline
|   |-- test_api.py                 # Integration tests for FastAPI routes
|   |-- test_agent.py               # Unit tests for ReAct agent
|
|-- data/                           # Generated CSVs and dashboard configs (git-ignored)
|   |-- .gitkeep
|
|-- exports/                        # PDF and JSON exports (git-ignored)
|   |-- .gitkeep
|
|-- cache/                          # Local file cache (git-ignored)
    |-- .gitkeep
```

---

## Quickstart

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/biooracle.git
cd biooracle
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Run with Docker Compose (recommended)

```bash
docker compose up --build
```

This starts:
- `biooracle_api` on port 8000
- `biooracle_worker` (Celery background tasks)
- `biooracle_db` (PostgreSQL on port 5432)
- `biooracle_redis` (Redis on port 6379)
- `biooracle_flower` (Celery monitor on port 5555)

### 3. Run locally (development)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 4. Seed the RAG index (optional)

```bash
python scripts/seed_rag.py
```

---

## API Usage

### Submit a query

```bash
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me GLP-1 clinical trial trends from 2018 to 2024"}'
```

### View the dashboard

Open in browser:
```
http://localhost:8000/api/v1/dashboard/{config_id}
```

### Download CSV

```
GET http://localhost:8000/api/v1/export/csv/{session_id}
```

### Download PDF

```
GET http://localhost:8000/api/v1/export/pdf/{config_id}
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. Key variables:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (required) |
| `NCBI_API_KEY` | NCBI/PubMed API key (free, optional but recommended) |
| `NCBI_EMAIL` | Your email for NCBI courtesy |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SMTP_USER` / `SMTP_PASSWORD` | For email report delivery |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Pipeline Flow

```
User natural language query
        |
        v
ReAct Agent (Claude Sonnet 4.6)
        |
        v
create_execution_plan
        |
        v
fetch_pubmed_data / fetch_clinicaltrials_data / ...
        |
        v
ETL Pipeline (clean, normalize, save CSV)
        |
        v
RAG Layer (optional context enrichment via FAISS)
        |
        v
get_csv_schema
        |
        v
configure_dashboard (chart types, axes, filters)
        |
        v
render_dashboard (Plotly Dash HTML)
        |
        v
Dashboard served / exported / emailed
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent | Claude Sonnet 4.6 (Anthropic API) |
| API Server | FastAPI + Uvicorn |
| Task Queue | Celery + Redis |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Cache | Redis |
| Visualization | Plotly / Plotly Dash |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Search | FAISS |
| Exports | ReportLab (PDF), Pandas (CSV/JSON) |
| Containerization | Docker + Docker Compose |

---

## Team

| Name | Roll No |
|---|---|
| Akash | SE25MBDS005 |
| Surya Vamsi | SE25MBDS011 |
| Harish Reddy | SE25MBDS003 |
| EV Nithin | SE25MBDS007 |

---

## License

MIT License. See LICENSE for details.

