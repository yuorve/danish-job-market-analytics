# 🇩🇰 Danish Job Market Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20PostgreSQL-green.svg)](https://sqlite.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Medallion%20%2F%20ETL-orange.svg)](#3-architecture)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passing-success.svg)](#12-testing)

An end-to-end data engineering pipeline, analytical engine, and candidate matcher analyzing the IT and Data job market in Denmark (Copenhagen, Aarhus, Odense, Aalborg, Ballerup, Lyngby, Hillerød, Roskilde).

Built as a flagship portfolio project for a **Data Specialist / Data Instructor** position in the Danish tech training and consulting ecosystem (companies working with Microsoft Azure, Microsoft Fabric, Databricks, SQL, Python, and modern AI).

---

## 1. Project Overview & Motivation

Entering the Danish technology job market as a junior developer or data instructor requires answering concrete, data-backed questions:
* *Which programming languages and data tools are most in demand in Denmark?*
* *How widespread are Microsoft Fabric and Databricks in Danish enterprise consulting?*
* *What percentage of Danish IT postings actually require fluent Danish vs. accepting English only?*
* *Where are junior entry points concentrated across Denmark's tech hubs?*
* *What specific skill gaps prevent a junior candidate from matching local vacancies?*

This project solves this by collecting, cleaning, transforming, storing, analyzing, and visualizing hundreds of Danish IT job postings through a production-grade, reproducible pipeline.

---

## 2. Key Insights Discovered

* **English-Friendly Market:** **69.5%** of analyzed IT postings in Denmark (especially at global enterprises like Novo Nordisk, Maersk, SimCorp, and Copenhagen tech startups) use English as their official working language. Danish is predominantly required in public sector IT (KMD, Kommuner, Skatteforvaltningen) and local client consulting.
* **Dominant Tech Bundles:** The strongest co-occurring technology clusters in Denmark are:
  1. `Python + SQL` (the universal foundation across all data roles)
  2. `Azure + Databricks + Microsoft Fabric` (the enterprise data platform standard)
  3. `Docker + CI/CD + Linux` (modern developer baseline)
* **Junior Opportunity Index:** **41.5%** of vacancies exhibit junior-friendly or instructor-accessible criteria when matching entry-level skill sets.
* **Geographic Distribution:** Copenhagen (42%) and Aarhus (20%) represent the largest share of openings, followed by specialized hubs like Lyngby (DTU academic/consulting cluster) and Ballerup (fintech/healthtech).

---

## 3. Architecture

```
[ Data Sources ]
  - Synthetic Demo Source (520+ realistic Danish IT postings)
  - CSV Import Connector
  - JobIndex / Jobnet Adapter Skeletons (Strictly ethical / No robots.txt breach)
          │
          ▼
[ Ingestion Layer (JobSource Interface) ]
  - Standardized RawJobRecord dataclass contract
          │
          ▼
[ Data Cleaning & Quality Validation ]
  - MD5 Content Hash Deduplication (filters re-posted listings)
  - HTML tag stripper & entity decoding
  - Danish city normalizer (København -> Copenhagen, Århus -> Aarhus)
  - Legal corporate name cleaner (Novo Nordisk A/S -> Novo Nordisk)
  - Data Quality validation report (invalid date / salary anomalies)
          │
          ▼
[ Transformation & Feature Engineering ]
  - Compiled RegEx Skill Extractor with word boundary safety (config/skills.yaml)
  - Domain classification (Data Engineering, AI/ML, Cloud/DevOps, BI, Software Dev)
  - Danish vs English-only requirement detection
  - Junior opportunity index derivation
          │
          ▼
[ Relational SQL Database (SQLite / PostgreSQL) ]
  - Normalized schema: jobs, companies, locations, skills, job_skills, sources
          │
          ▼
[ Analytics & AI Enrichment ]
  - Analytical KPI aggregations & co-occurrence matrices
  - Structured AI Layer (implicit requirement extraction with strict JSON validation)
  - Interactive Candidate Matcher with transparent gap scoring
          │
          ▼
[ Serving & Visualization ]
  - Streamlit Web Dashboard (`dashboard/app.py`)
  - Full-Stack Interactive Web Explorer (SQL Console, Live Runner, Interview Prep)
```

---

## 4. Normalized Relational Data Model

Designed for relational integrity, eliminating update anomalies and enabling high-performance analytics:

```
  ┌─────────────┐            ┌──────────────┐
  │   sources   │            │  locations   │
  ├─────────────┤            ├──────────────┤
  │ source_id PK│            │ location_idPK│
  │ name        │            │ city (UNIQUE)│
  │ base_url    │            │ region       │
  │ is_synthetic│            │ country      │
  └──────┬──────┘            └──────┬───────┘
         │                          │
         │   ┌──────────────────┐   │
         │   │    companies     │   │
         │   ├──────────────────┤   │
         │   │ company_id PK    │   │
         │   │ name (UNIQUE)    │   │
         │   │ normalized_name  │   │
         │   │ industry         │   │
         │   └────────┬─────────┘   │
         │            │             │
         ▼            ▼             ▼
  ┌─────────────────────────────────────────┐            ┌──────────────┐
  │                  jobs                   │            │    skills    │
  ├─────────────────────────────────────────┤            ├──────────────┤
  │ job_id PK                               │            │ skill_id PK  │
  │ source_id FK ───────────────────────────┤            │ name (UNIQUE)│
  │ company_id FK ──────────────────────────┤            │ category     │
  │ location_id FK ─────────────────────────┤            └──────┬───────┘
  │ title, normalized_title, role_category  │                   │
  │ published_date, salary_min, salary_max  │                   │
  │ is_danish_required, is_english_only     │                   │
  │ is_remote, is_hybrid, is_junior         │                   │
  │ experience_level, education_requirements│                   │
  └───────────────────┬─────────────────────┘                   │
                      │                                         │
                      ▼                                         ▼
               ┌──────────────────────────────────────────────────┐
               │                    job_skills                    │
               ├──────────────────────────────────────────────────┤
               │ job_id FK (PK)                                   │
               │ skill_id FK (PK)                                 │
               └──────────────────────────────────────────────────┘
```

---

## 5. Technology Stack

* **Language:** Python 3.10+ (Type hints, dataclasses, standard library robustness)
* **ETL Engine:** Python & Pandas
* **Database:** SQLite 3 (Production schema portable to PostgreSQL / Azure SQL)
* **Skill Taxonomy:** YAML / JSON regex engine (`config/skills.yaml`, `config/skills.json`)
* **AI Layer:** Google Gemini 1.5 Flash / OpenAI compatible API with offline deterministic fallback (`AI_MODE=mock`)
* **Dashboard:** Streamlit (Python) + Full-Stack React / Vite / Express
* **Testing:** Pytest / Unittest (18 unit tests, 100% passing)
* **Containerization:** Docker & Docker Compose

---

## 6. Analytical SQL Queries

### 1. Top Technologies & Market Penetration
```sql
SELECT 
    s.name AS skill_name,
    s.category,
    COUNT(js.job_id) AS job_count,
    ROUND(COUNT(js.job_id) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) AS penetration_pct
FROM skills s
JOIN job_skills js ON s.skill_id = js.skill_id
GROUP BY s.skill_id, s.name, s.category
ORDER BY job_count DESC
LIMIT 10;
```

### 2. Jobs by City & International Ratio
```sql
SELECT 
    l.city,
    l.region,
    COUNT(j.job_id) AS total_jobs,
    SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) AS english_friendly,
    ROUND(AVG(j.salary_avg), 0) AS avg_salary_dkk
FROM locations l
JOIN jobs j ON l.location_id = j.location_id
GROUP BY l.location_id, l.city, l.region
ORDER BY total_jobs DESC;
```

### 3. Technology Co-Occurrence (Pair Synergy)
```sql
SELECT 
    s1.name AS tech_a,
    s2.name AS tech_b,
    COUNT(*) AS pair_frequency
FROM job_skills js1
JOIN job_skills js2 ON js1.job_id = js2.job_id AND js1.skill_id < js2.skill_id
JOIN skills s1 ON js1.skill_id = s1.skill_id
JOIN skills s2 ON js2.skill_id = s2.skill_id
GROUP BY s1.name, s2.name
ORDER BY pair_frequency DESC
LIMIT 10;
```

---

## 7. Future Enterprise Roadmap: Microsoft Fabric & Databricks Migration

In enterprise Danish IT consulting (e.g., Netcompany, Devoteam, Delegate, Avanade Denmark, Peak Consulting), data pipelines scale into the **Medallion Lakehouse Architecture**:

```
[ Sources: Jobindex, Jobnet, APIs ]
               │
               ▼
   [ Azure Data Factory / Airflow ]
               │
               ▼
[ Azure Data Lake Storage Gen2 / OneLake ]
               │
               ▼
      [ Bronze Layer (Raw) ]
   Append-only Delta Lake tables preserving immutable JSON extracts
               │
               ▼
     [ Silver Layer (Cleaned) ]
   PySpark / Databricks notebooks executing:
   - Deduplication & Schema Enforcement
   - Entity Normalization & Quality Rules
               │
               ▼
      [ Gold Layer (Curated) ]
   Dimensional Star Schema:
   - Fact_Job_Postings
   - Dim_Skill, Dim_Company, Dim_Location, Dim_Date
               │
               ▼
[ Power BI Direct Lake / Fabric Semantic Model ]
   Sub-second interactive executive reporting for talent demand forecasting
```

---

## 8. Candidate Matching Engine

The matching algorithm computes transparent alignment between a candidate profile and a Danish job opening:
* **70% Technical Stack Match:** Exact comparison against extracted technical skills.
* **20% Language Suitability:** Flags when a position mandates fluent Danish (B2+) and the candidate is at beginner level (A1/A2), while awarding full points for international English-friendly roles.
* **10% Seniority Alignment:** Evaluates junior/associate suitability.
* **Actionable Gap Analysis:** Explains matched skills, missing skills, and custom learning recommendations.

---

## 9. Quickstart: How to Run Locally

### Option A: Using Make (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/your-username/danish-job-market-analytics.git
cd danish-job-market-analytics

# 2. Run the full ETL pipeline
make pipeline

# 3. Execute the automated test suite
make test

# 4. Launch the Streamlit dashboard
make dashboard
```

### Option B: Using Python CLI
```bash
# Generate synthetic dataset
python3 scripts/generate_demo_data.py

# Run Extract -> Clean -> Transform -> Load
python3 -m src.pipeline

# Run all 18 unit tests
python3 -m unittest discover tests -v
```

---

## 10. Docker Deployment

Launch the complete containerized environment with a single command:

```bash
docker compose up --build
```

Then visit:
```
http://localhost:8501
```

---

## 11. Testing & Data Quality

The project features 18 automated unit tests verifying every stage of the pipeline:

```bash
python3 -m unittest discover tests -v
```

Output:
```text
test_deduplication (test_cleaning.TestDataCleaning) ... ok
test_normalize_city_danish_variants (test_cleaning.TestDataCleaning) ... ok
test_normalize_company_name (test_cleaning.TestDataCleaning) ... ok
test_strip_html (test_cleaning.TestDataCleaning) ... ok
test_validation_rejects_invalid_salaries (test_cleaning.TestDataCleaning) ... ok
test_schema_initialization (test_database.TestDatabase) ... ok
test_upsert_and_retrieve_job (test_database.TestDatabase) ... ok
test_danish_requirement_warning (test_matching.TestCandidateMatching) ... ok
test_missing_skills_identification (test_matching.TestCandidateMatching) ... ok
test_strong_candidate_match (test_matching.TestCandidateMatching) ... ok
test_extract_ai_technologies (test_skill_extraction.TestSkillExtraction) ... ok
test_extract_data_and_fabric_stack (test_skill_extraction.TestSkillExtraction) ... ok
test_extract_programming_languages (test_skill_extraction.TestSkillExtraction) ... ok
test_handles_csharp_and_dotnet_boundaries (test_skill_extraction.TestSkillExtraction) ... ok
test_danish_language_requirement_flag (test_transformations.TestDataTransformations) ... ok
test_english_friendly_flag (test_transformations.TestDataTransformations) ... ok
test_junior_flag_derivation (test_transformations.TestDataTransformations) ... ok
test_role_category_data_engineering (test_transformations.TestDataTransformations) ... ok

----------------------------------------------------------------------
Ran 18 tests in 0.026s
OK
```

---

## 12. What I Learned Building This Project

1. **Relational Modeling Over Flat Data:** Designing a junction table (`job_skills`) enables instant co-occurrence and market share calculations that are unfeasible with flat JSON.
2. **Regex Edge Cases in Tech Taxonomy:** Extracting tools like `C#`, `.NET`, and `Go` requires strict boundary handling (`\b` fails on `#` and leading dots).
3. **Deterministic vs. LLM Trade-offs:** Deterministic rules are orders of magnitude faster and 100% reproducible for ETL, whereas LLMs shine in extracting implicit cultural nuances and summarizing unstructured text.
4. **Data Quality Discipline:** Catching 80+ duplicate listings using normalized content hashing demonstrates why deduplication must occur before data warehousing.

---

## 13. Ethical Considerations

* All synthetic job records are explicitly marked with `source = "synthetic_demo"`.
* Scraping modules respect `robots.txt` and Terms of Service. No anti-bot bypasses or aggressive harvesting methods are implemented.
* The Candidate Matcher is an educational exploration tool, not an automated hiring decision system.

---

## License

MIT License. Free to use, adapt, and build upon.
