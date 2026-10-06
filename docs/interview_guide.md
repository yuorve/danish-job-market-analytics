# Danish IT Technical Interview & Portfolio Presentation Kit
*Targeted for Data Specialist / Data Instructor roles in Denmark*

---

## 1. CV & LinkedIn Presentation (5-7 Lines)

```text
Built Danish Job Market Analytics, an end-to-end data engineering pipeline and analytics engine evaluating 400+ IT vacancies across Denmark (Copenhagen, Aarhus, Odense, Aalborg). Architected automated data extraction, MD5 hash deduplication, data quality validation, and regex technology taxonomy extraction into a normalized SQLite/SQL relational model. Developed an interactive Candidate Matcher with language gap detection and an AI semantic extraction layer. Configured Docker containerization, an 18-test suite, and designed a concrete Medallion Architecture roadmap for Microsoft Fabric and Databricks Lakehouse migration.
```

---

## 2. 30-Second Interview Elevator Pitch

> *"I created Danish Job Market Analytics to demonstrate my hands-on data engineering foundation. It's a pipeline that extracts IT vacancies, cleans and deduplicates them using custom hash signatures, extracts skills via regex taxonomies, and stores them in a normalized relational database. I then built an analytical engine that uncovers Danish market realities—such as nearly 70% of tech jobs accepting English—along with an interactive candidate matcher. I designed every phase with modular code and unit tests so it can easily transition into a Microsoft Fabric or Databricks lakehouse."*

---

## 3. What a Junior Candidate MUST Be Able to Explain Personally

During an interview in Denmark, you are not expected to be a senior architect who has built multi-petabyte clusters. Danish hiring managers look for:
1. **Understanding the Data Flow:** Be able to trace a record from raw extraction -> cleaning -> transformation -> relational load -> analytics query without hesitation.
2. **The "Why" Behind Normalization:** Explain why `job_skills` is a separate junction table instead of a comma-separated string inside `jobs`.
3. **Data Quality & Edge Cases:** Explain why `#` in `C#` and the leading dot in `.NET` break standard regex `\b` boundaries, and how your test suite caught that.
4. **Deduplication Strategy:** Explain how your MD5 content signature works (combining normalized title + company + city) to eliminate duplicate listings.
5. **Danish Workplace Culture Awareness:** Articulate why English-friendliness is high in pharma/logistics/fintech while Danish is required in public sector IT (KMD, Kommuner).
6. **Future Lakehouse Concept:** Show familiarity with terms used by Danish consultancies: Microsoft Fabric, OneLake, Delta Lake, Bronze/Silver/Gold layers, and Power BI Direct Lake.

---

## 4. 10 Technical Interview Questions from Danish IT Employers & Model Answers

### Question 1: "Why did you choose a normalized relational model instead of saving raw JSON documents in MongoDB or flat tables?"
* **Model Answer:**
  "A normalized relational model enforces schema integrity and eliminates update anomalies. In IT recruiting, jobs and skills have a many-to-many relationship: one job requires multiple skills, and one skill belongs to thousands of jobs. If we stored skills as comma-separated strings or nested JSON, analytical queries—like calculating the co-occurrence matrix of which technologies appear together—would require costly string pattern searches across the entire dataset. With the `job_skills` junction table, we execute fast relational self-joins and aggregations with index scans."
* **Key Talking Points:** Many-to-many relationship, junction table, relational indexing, query efficiency, data redundancy prevention.

---

### Question 2: "How does your deduplication mechanism handle identical job postings republished under different IDs or across multiple job portals?"
* **Model Answer:**
  "Relying on job IDs is insufficient because different job boards assign different IDs to the same opening. To solve this, the cleaner normalizes the company name (stripping Danish legal suffixes like A/S and ApS), normalizes city names (mapping 'København' to 'Copenhagen'), and cleans the title. It then concatenates these normalized values and computes an MD5 hash signature. If a newly ingested record matches an existing hash in our cache, it is marked as a duplicate and omitted, protecting our analytics from skewed counts."
* **Key Talking Points:** Deterministic content fingerprinting, MD5 hash, normalizing entities before hashing, avoiding skewed metric counts.

---

### Question 3: "What challenges did you face when extracting programming languages like C#, .NET, or Go using regular expressions?"
* **Model Answer:**
  "Standard regex `\b` word boundaries only recognize alphanumeric characters and underscores (`\w`). Because `#` and `.` are non-word characters (`\W`), a pattern like `\bc#\b` fails because there is no word character after `#`. Similarly, `.NET` fails if preceded by whitespace. Additionally, 'Go' easily matches the common English verb. To resolve this, I implemented lookahead and negative lookbehind assertions—for example, matching `(?<!\w)(?:\.net\b|\bdotnet\b)` and requiring specific boundary delimiters for `C#`. I verified these fixes with unit tests."
* **Key Talking Points:** RegEx word boundaries (`\w` vs `\W`), lookaheads/lookbehinds, test-driven debugging.

---

### Question 4: "Why did you build both deterministic regex extraction and an LLM AI layer? Why not use the LLM for everything?"
* **Model Answer:**
  "Deterministic code and SQL are fast, zero-cost, 100% reproducible, and run completely offline without hallucination. Using an LLM to parse thousands of known keywords like 'Python' or 'SQL' is wasteful and introduces latency. Instead, I reserved the LLM for tasks where deterministic code struggles: inferring implicit workplace expectations (like Danish flat hierarchy, agile autonomy, or client-facing consulting nuances) and providing summaries. Furthermore, I built an `AI_MODE=mock` fallback so the pipeline functions offline without an API key."
* **Key Talking Points:** Cost-efficiency, deterministic reliability, LLMs for unstructured nuance, strict JSON output validation, offline fallback.

---

### Question 5: "How would you migrate this architecture into an enterprise Microsoft Fabric or Databricks environment?"
* **Model Answer:**
  "I would adopt the Medallion Architecture. In Phase 1 (Bronze), raw job files would land into Azure Data Lake Storage Gen2 / OneLake as append-only Delta Lake tables. In Phase 2 (Silver), PySpark notebooks on Fabric or Databricks would execute cleaning, deduplication, and schema validation. In Phase 3 (Gold), we would build a dimensional star schema with `Fact_Job_Postings` and dimension tables for skills, companies, and locations. Finally, Power BI would connect via Direct Lake mode for instant reporting without data replication."
* **Key Talking Points:** Medallion Architecture (Bronze -> Silver -> Gold), OneLake / ADLS Gen2, PySpark notebooks, Delta Lake, Power BI Direct Lake mode.

---

### Question 6: "What data quality metrics do you track, and how do you ensure invalid data doesn't corrupt your database?"
* **Model Answer:**
  "Our validator checks every record against five business rules: non-empty job ID, non-empty title, valid ISO published date, recognized data source, and logical salary ranges (`salary_min <= salary_max`). The pipeline produces a `QualityReport` summarizing total records processed, valid records, dropped duplicates, and invalid records, computing a final data health percentage."
* **Key Talking Points:** Automated validation rules, data health percentage, quality reporting, fail-safe ingestion.

---

### Question 7: "What did your analytics reveal about language requirements in the Danish tech sector?"
* **Model Answer:**
  "The data showed that 69.5% of IT jobs in Denmark accept English only or use English as the corporate working language. This is especially prevalent in pharmaceutical multinationals (Novo Nordisk, Leo Pharma), global shipping (Maersk), fintech (SimCorp), and Copenhagen startups. Fluent Danish is concentrated in Danish public sector IT (KMD, municipal agencies) and local consulting. For foreign candidates, this proves that immediate employment in Danish tech is viable in English while learning Danish for long-term integration."
* **Key Talking Points:** 70/30 English vs Danish split, sector-specific language needs, data-driven career strategy.

---

### Question 8: "As a Data Instructor, how would you explain the difference between ETL and ELT to junior students?"
* **Model Answer:**
  "I explain that in traditional ETL, data is transformed by a specialized compute engine before loading into the database, which was necessary when storage and database compute were expensive. In modern cloud ELT (using Snowflake, BigQuery, or Fabric), we extract and load raw data directly into the cloud data warehouse or lakehouse first, and then execute transformations in-place using SQL or Spark. ELT preserves raw historical snapshots and leverages elastic cloud parallel compute."
* **Key Talking Points:** Clear pedagogical analogy, compute vs storage separation, preserving raw data, modern cloud parallel engines.

---

### Question 9: "Why are automated unit tests important in a data pipeline, and what do your tests cover?"
* **Model Answer:**
  "Data pipelines frequently suffer from silent schema drift and edge-case corruption. My 18 unit tests cover HTML stripping, Danish city and company name normalization, regex boundary handling for C# and Go, salary validation checks, SQLite table creation, and candidate matching scores. This ensures that any new data source added to the `JobSource` interface does not introduce breaking changes downstream."
* **Key Talking Points:** Silent data bugs, regression protection, testing ETL edge cases, contract assurance.

---

### Question 10: "How does the Candidate Matcher calculate fit, and how do you prevent it from being a 'black box'?"
* **Model Answer:**
  "The algorithm is completely transparent: 70% technical skill overlap, 20% language suitability, and 10% seniority alignment. Rather than just returning a number, it produces an explicit breakdown: exactly which skills matched, which are missing, whether Danish fluency is required, and a tailored learning recommendation. This makes it a coaching and diagnostic tool rather than an opaque black box."
* **Key Talking Points:** Weighted transparent scoring, actionable feedback, skill gap diagnostics, candidate mentoring value.
