# Enterprise Migration Blueprint: Microsoft Fabric & Databricks Lakehouse

## 1. Context in the Danish Market
Danish IT consultancies (Netcompany, Devoteam, Delegate, Avanade Denmark, NNIT, Peak Consulting) frequently architect modern data platforms on **Microsoft Fabric** and **Databricks on Azure**.

This document outlines how the current Python/SQLite pipeline seamlessly migrates to an enterprise Lakehouse.

---

## 2. Medallion Architecture Mapping

### Bronze Layer (Raw Ingestion)
* **Storage:** Azure Data Lake Storage Gen2 / Microsoft Fabric OneLake
* **Format:** Delta Lake (Append-only)
* **Process:** Azure Data Factory or Fabric Data Pipelines pull job listings from APIs into `/raw/job_postings/{yyyy}/{mm}/{dd}/`.

### Silver Layer (Cleansed & Enriched)
* **Compute:** Fabric PySpark / Databricks Notebooks
* **Process:**
  - Execute deduplication matching the MD5 content signature.
  - Apply data quality constraints (schema validation, salary ranges).
  - Normalize Danish cities and company entities.
  - Run the regex and LLM skill taxonomy extractor.
* **Storage:** Cleaned Delta Lake tables (`silver_jobs`, `silver_skills`).

### Gold Layer (Curated Dimensional Star Schema)
* **Model:** Star Schema optimized for analytical queries
  - **Fact Table:** `fact_job_postings` (job_key, company_key, location_key, salary_avg, is_junior, is_english_only, published_date_key)
  - **Dimension Tables:** `dim_company`, `dim_location`, `dim_skill`, `dim_date`
  - **Bridge Table:** `bridge_job_skills` (handling many-to-many relationship)
* **Serving:** Microsoft Fabric Direct Lake mode powering Power BI executive dashboards without data copy or import delays.
