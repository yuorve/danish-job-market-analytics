# Danish Job Market Analytics - Architecture Specification

## 1. System Components

The repository is organized following clean architectural separation of concerns:

```text
danish-job-market-analytics/
├── data/
│   ├── raw/                  # Landed source payloads
│   ├── processed/            # SQLite database & transformed marts
│   └── demo/                 # Synthetic demo dataset
├── src/
│   ├── ingestion/            # Source connectors (JobSource contract)
│   ├── cleaning/             # Deduplication, HTML stripping, normalizers, DQ
│   ├── transformation/       # Feature engineering, language & junior flags
│   ├── skill_extraction/     # RegEx skill taxonomy engine
│   ├── database/             # Relational schema, connection, repository, SQL
│   ├── analytics/            # KPIs, city demand, co-occurrence matrices
│   ├── ai/                   # LLM extraction layer with strict JSON schemas
│   ├── matching/             # Candidate match simulator & gap analyzer
│   └── pipeline/             # Orchestrator coordinating all phases
├── dashboard/
│   └── app.py                # Streamlit analytics application
├── config/
│   ├── skills.yaml           # Human-readable skills taxonomy
│   └── skills.json           # Compiled skills patterns
├── tests/                    # 18 automated unit tests
├── docs/                     # Architectural & interview guides
├── Dockerfile                # Multi-stage container build
├── docker-compose.yml        # Orchestrated deployment
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Build metadata & test settings
├── Makefile                  # Automated command runner
└── README.md                 # Master documentation
```

## 2. Data Flow Lifecycle

```text
Extract (JobSource) ──> Clean & Validate ──> Transform & Skills ──> Load (SQLite) ──> Analytics & Dashboard
```

1. **Extract**: Pluggable `JobSource` abstraction.
2. **Clean & Validate**: MD5 content hashing, entity normalization, schema validation rules.
3. **Transform**: RegEx skill taxonomy, domain categorization, language classification.
4. **Load**: Relational SQLite storage with indexed foreign keys and many-to-many junction table.
5. **Analyze & Serve**: Analytical SQL queries, Streamlit dashboard, and interactive web application.
