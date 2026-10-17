# 🇩🇰 Danish Job Market Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-SQLite%20(3NF)-green.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passing-success.svg)](#6-cómo-ejecutarlo)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 1. Qué es

Un pipeline reproducible de **Data Engineering + Analytics** que recopila, limpia, transforma y analiza el mercado laboral tecnológico en Dinamarca (Copenhague, Aarhus, Odense, Aalborg, etc.).

Incluye:
* Pipeline ETL modular con validaciones de calidad (DQ) y deduplicación por hash MD5.
* Base de datos relacional normalizada (3FN) con consultas analíticas en SQL.
* Motor de extracción de habilidades técnicas y clasificación de ofertas.
* Algoritmo de **Candidate Match** con detección de requisitos de idioma (inglés vs. danés).
* Dashboard analítico interactivo (Streamlit + Web App).

---

## 2. Qué demuestra

Diseñado para demostrar competencias prácticas para roles de **Data Specialist / Data Instructor / Junior Data Engineer**:

* **Python & Data Engineering:** Pipeline modular (Extract, Clean, Transform, Load) tipado y reproducible.
* **Calidad de datos:** Deduplicación determinista, stripping HTML, normalización de entidades y reporte de calidad.
* **Modelado relacional y SQL:** Esquema 3NF con tabla intermedia de unión (N:M) y consultas analíticas avanzadas.
* **Extracción de entidades:** Taxonomía RegEx robusta ante casos borde (`C#`, `.NET`, `Go`).
* **AI pragmática:** Capa LLM con validación estricta de JSON y fallback offline (`AI_MODE=mock`).
* **Buenas prácticas:** Tests unitarios automatizados (18 tests), contenedor Docker y código desacoplado.

---

## 3. Arquitectura

```text
[ Fuentes de Datos ] ──► (JobSource Interface: Demo, CSV, APIs)
         │
         ▼
[ Ingestion & Clean ] ──► Deduplicación MD5 + Stripping HTML + Normalización de entidades
         │
         ▼
[ Transform & Extract ] ──► Motor RegEx (config/skills.yaml) + Clasificación (Idioma / Seniority)
         │
         ▼
[ SQLite Database ] ──► Esquema relacional 3NF (jobs, companies, locations, skills, job_skills)
         │
         ▼
[ Serving & Analytics ] ──► SQL Console + Candidate Matcher + Streamlit / Web Dashboard
```

---

## 4. Tech Stack

* **Lenguaje:** Python 3.10+
* **Datos & ETL:** Pandas, SQLite3 (compatible con PostgreSQL / Azure SQL)
* **RegEx & Taxonomía:** YAML / JSON (`config/skills.yaml`)
* **AI Layer:** Google Gemini / OpenAI API con fallback determinista offline
* **Visualización:** Streamlit + React / Express
* **Testing:** Pytest / Unittest (18 tests, 100% passing)
* **DevOps:** Docker, Docker Compose, Makefile

---

## 5. Demo Data

Para garantizar ejecución 100% local e inmediata sin dependencias externas:

* **Dataset demo:** 520+ ofertas realistas del mercado IT danés (Novo Nordisk, Maersk, Netcompany, SimCorp, etc.).
* **Ciudades cubiertas:** Copenhagen, Aarhus, Odense, Aalborg, Ballerup, Lyngby, Hillerød, Roskilde.
* **Transparencia ética:** Todos los registros sintéticos están identificados explícitamente con `source = "synthetic_demo"`.

---

## 6. Cómo ejecutarlo

### Con Docker (Recomendado)
```bash
docker compose up --build
```
Abre el dashboard en: `http://localhost:8501`

### Local con Make
```bash
make pipeline    # Ejecuta Extract -> Clean -> Transform -> Load
make test        # Ejecuta los 18 tests automatizados
make dashboard   # Lanza el dashboard Streamlit
```

---

## 7. Limitaciones

* **Datos reales vs. scraping:** Para respetar términos de servicio y `robots.txt` de portales daneses (Jobindex, Jobnet), la ingesta utiliza conectores adapter y dataset sintético representativo.
* **Alcance de la IA:** El LLM enriquece matices cualitativos (cultura, requisitos implícitos); el procesamiento crítico de datos es determinista y no depende de llamadas externas.
* **Entorno:** Diseñado para ejecución ágil y local en SQLite antes de su despliegue en infraestructuras cloud.

---

## 8. Roadmap

Diseñado con un camino directo de evolución hacia arquitecturas **Lakehouse (Medallion)** en plataformas empresariales danesas (Microsoft Azure / Databricks / Microsoft Fabric):

1. **Bronze:** Landing de JSONs crudos en Azure Data Lake Storage Gen2 / OneLake.
2. **Silver:** Limpieza, deduplicación y tipado mediante PySpark / Databricks Notebooks en Delta Lake.
3. **Gold:** Modelo dimensional Star Schema (`Fact_Job_Postings`, `Dim_Skill`, `Dim_Company`).
4. **BI:** Conexión directa a Power BI mediante Direct Lake mode.

*Detalles ampliados disponibles en [`docs/fabric_migration.md`](docs/fabric_migration.md) y [`docs/interview_guide.md`](docs/interview_guide.md).*
