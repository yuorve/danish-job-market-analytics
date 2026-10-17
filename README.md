# 🇩🇰 Danish Job Market Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20(3NF)-green.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passing-success.svg)](#6-how-to-run-it)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 1. What It Is

A reproducible **Data Engineering + Analytics** pipeline that ingests, cleans, transforms, and analyzes the technology job market in Denmark (Copenhagen, Aarhus, Odense, Aalborg, etc.).

Key components:
* Modular ETL pipeline with data quality (DQ) checks and MD5 hash deduplication.
* Normalized relational database (3NF) with analytical SQL queries.
* Technology taxonomy and skill extraction engine.
* **Candidate Matcher** evaluating technical fit and Danish vs. English language requirements.
* Interactive analytics dashboard (Streamlit + Web App).

---

## 2. What It Demonstrates

Built to showcase production-ready skills for **Data Specialist / Data Instructor / Junior Data Engineer** roles:

* **Python & Data Engineering:** Modular, typed, and reproducible pipeline (Extract, Clean, Transform, Load).
* **Data Quality & Hygiene:** Deterministic deduplication, HTML stripping, entity normalization, and validation reports.
* **Relational Modeling & SQL:** 3NF schema with junction tables (N:M) and analytical aggregations.
* **Entity Extraction:** RegEx taxonomy handling tricky edge cases (`C#`, `.NET`, `Go`).
* **Pragmatic AI:** Structured LLM extraction with strict JSON validation and offline fallback (`AI_MODE=mock`).
* **Software Engineering Practices:** 18 automated unit tests, Docker containerization, and decoupled components.

---

## 3. Architecture

```text
[ Data Sources ] ──► (JobSource Interface: Demo, CSV, APIs)
        │
        ▼
[ Ingestion & Clean ] ──► MD5 Deduplication + HTML Stripping + Entity Normalization
        │
        ▼
[ Transform & Extract ] ──► RegEx Engine (config/skills.yaml) + Domain & Language Flags
        │
        ▼
[ SQLite Database ] ──► 3NF Relational Model (jobs, companies, locations, skills, job_skills)
        │
        ▼
[ Serving & Analytics ] ──► SQL Studio + Candidate Matcher + Streamlit / Web Dashboard
```

---

## 4. Tech Stack

* **Language:** Python 3.10+
* **Data & ETL:** Pandas, SQLite3 (portable to PostgreSQL / Azure SQL)
* **RegEx & Taxonomy:** YAML / JSON (`config/skills.yaml`)
* **AI Layer:** Google Gemini / OpenAI API with offline deterministic fallback
* **Dashboard:** Streamlit + React / Express
* **Testing:** Pytest / Unittest (18 tests, 100% passing)
* **DevOps:** Docker, Docker Compose, Makefile

---

## 5. Demo Data

Ensures 100% local, instant reproducibility without external API credentials:

* **Demo Dataset:** 520+ realistic job postings modeled after Danish tech employers (Novo Nordisk, Maersk, Netcompany, SimCorp, etc.).
* **Geographic Coverage:** Copenhagen, Aarhus, Odense, Aalborg, Ballerup, Lyngby, Hillerød, Roskilde.
* **Ethical Transparency:** All synthetic demo records are explicitly marked with `source = "synthetic_demo"`.

---

## 6. How to Run It

### With Docker (Recommended)
```bash
docker compose up --build
```
Open dashboard at: `http://localhost:8501`

### Local with Make
```bash
make pipeline    # Run Extract -> Clean -> Transform -> Load
make test        # Run the 18 automated unit tests
make dashboard   # Launch Streamlit dashboard
```

---

## 7. Limitations

* **Real Web Data vs. Scraping:** To comply with Terms of Service and `robots.txt` of Danish job portals (Jobindex, Jobnet), live ingestion is modeled via adapter skeletons and a realistic synthetic dataset.
* **AI Boundaries:** LLMs are used selectively for qualitative analysis (culture, implicit soft skills); core data processing is 100% deterministic.
* **Storage:** Uses SQLite for local simplicity and instant portfolio evaluation before cloud deployment.

---

## 8. Roadmap

Designed with a clear migration path to an enterprise **Medallion Lakehouse** on modern platforms common in Danish IT consultancies (Microsoft Azure / Databricks / Microsoft Fabric):

1. **Bronze:** Land raw JSON payloads into Azure Data Lake Storage Gen2 / OneLake.
2. **Silver:** Clean, deduplicate, and enforce schemas with PySpark / Databricks in Delta Lake.
3. **Gold:** Star Schema analytical mart (`Fact_Job_Postings`, `Dim_Skill`, `Dim_Company`).
4. **BI:** Direct Lake connectivity in Power BI for sub-second executive analytics.

*Deep-dive guides available in [`docs/fabric_migration.md`](docs/fabric_migration.md) and [`docs/interview_guide.md`](docs/interview_guide.md).*
