"""
ETL Pipeline Orchestrator for Danish Job Market Analytics.
Coordinates Extract -> Clean -> Transform -> Load phases in strict sequential order.
Can be executed directly via `python -m src.pipeline` or invoked programmatically.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ingestion.base import JobSource
from src.ingestion.sources import SyntheticDemoSource
from src.cleaning.cleaner import DataCleaner
from src.cleaning.validator import QualityReport
from src.skill_extraction.extractor import SkillExtractor
from src.transformation.transformer import DataTransformer
from src.database.connection import init_database
from src.database.repository import JobRepository
from src.analytics.analyzer import MarketAnalyzer

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ETLPipeline")

class PipelineOrchestrator:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "data/processed/danish_jobs.db"
        self.repository = JobRepository(self.db_path)
        self.cleaner = DataCleaner()
        self.skill_extractor = SkillExtractor()
        self.transformer = DataTransformer(self.skill_extractor)

    def run(self, sources: Optional[List[JobSource]] = None) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("=====================================================")
        logger.info("Starting Danish Job Market Analytics ETL Pipeline")
        logger.info("=====================================================")

        # Ensure database tables exist
        init_database(Path(self.db_path))

        # 1. EXTRACT
        if sources is None:
            sources = [SyntheticDemoSource()]

        all_raw_records = []
        for src in sources:
            logger.info(f"[PHASE 1 - EXTRACT] Ingesting from source: {src.source_id}")
            self.repository.upsert_source(
                source_id=src.source_id,
                name=src.source_id.replace("_", " ").title(),
                is_synthetic=(src.source_id == "synthetic_demo")
            )
            records = src.fetch_jobs()
            all_raw_records.extend(records)

        logger.info(f"Total raw records extracted: {len(all_raw_records)}")

        # 2. CLEAN & VALIDATE
        logger.info("[PHASE 2 - CLEAN & VALIDATE] Running data cleaning and DQ checks...")
        cleaned_records, quality_report = self.cleaner.clean_records(all_raw_records)

        # 3. TRANSFORM & FEATURE ENGINEERING
        logger.info("[PHASE 3 - TRANSFORM] Extracting skills and deriving analytics fields...")
        transformed_records = []
        for raw_dict in cleaned_records:
            transformed = self.transformer.transform_record(raw_dict)
            transformed_records.append(transformed)

        # 4. LOAD (SQL Relational Storage)
        logger.info(f"[PHASE 4 - LOAD] Storing {len(transformed_records)} records into SQLite ({self.db_path})...")
        for job_data in transformed_records:
            # Upsert company
            company_id = self.repository.get_or_create_company(
                name=job_data["company"],
                normalized_name=job_data["normalized_company"],
                industry=job_data.get("industry")
            )

            # Upsert location
            location_id = self.repository.get_or_create_location(
                city=job_data["location"],
                region=job_data["region"]
            )

            # Upsert skills and collect IDs
            skill_ids = []
            for s in job_data.get("extracted_skills", []):
                sid = self.repository.get_or_create_skill(s["name"], s["category"])
                skill_ids.append(sid)

            # Upsert job
            job_payload = {
                "job_id": job_data["job_id"],
                "source_id": job_data["source"],
                "company_id": company_id,
                "location_id": location_id,
                "title": job_data["title"],
                "normalized_title": job_data["normalized_title"],
                "role_category": job_data["role_category"],
                "description": job_data.get("description", ""),
                "remote_type": job_data.get("remote", "On-site"),
                "employment_type": job_data.get("employment_type", "Full-time"),
                "published_date": job_data["published_date"],
                "salary_min": job_data.get("salary_min"),
                "salary_max": job_data.get("salary_max"),
                "currency": job_data.get("currency", "DKK"),
                "url": job_data.get("url", ""),
                "language_requirements": job_data.get("language_requirements", ""),
                "is_danish_required": job_data["is_danish_required"],
                "is_english_only": job_data["is_english_only"],
                "is_remote": job_data["is_remote"],
                "is_hybrid": job_data["is_hybrid"],
                "is_junior": job_data["is_junior"],
                "is_data_role": job_data["is_data_role"],
                "is_ai_role": job_data["is_ai_role"],
                "is_devops_role": job_data["is_devops_role"],
                "is_cloud_role": job_data["is_cloud_role"],
                "experience_level": job_data["experience_level"],
                "education_requirements": job_data.get("education_requirements", ""),
                "skill_ids": skill_ids
            }
            self.repository.upsert_job(job_payload)

        # 5. ANALYTICS REPORT
        logger.info("[PHASE 5 - ANALYZE] Calculating market KPIs...")
        analyzer = MarketAnalyzer(self.repository)
        kpis = analyzer.compute_overview_kpis()

        duration = round(time.time() - start_time, 2)
        logger.info(f"ETL Pipeline successfully finished in {duration} seconds.")
        logger.info(f"Loaded {kpis['total_jobs']} jobs across {kpis['total_cities']} Danish cities.")
        logger.info(f"English-friendly jobs: {kpis['english_friendly_pct']}% | Junior opportunity index: {kpis['junior_opportunity_index']}%")

        return {
            "duration_seconds": duration,
            "quality_report": quality_report.summary(),
            "kpis": kpis
        }
