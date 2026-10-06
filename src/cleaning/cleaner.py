"""
Data Cleaning stage for Danish Job Market Analytics.
Handles deduplication, HTML stripping, entity normalization, and validation logging.
"""

import hashlib
import logging
from typing import Any, Dict, List, Set, Tuple
from src.ingestion.base import RawJobRecord
from .normalizers import normalize_city, normalize_company_name, normalize_title, strip_html
from .validator import QualityReport, validate_job_record

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self):
        self.seen_signatures: Set[str] = set()

    def generate_dedup_signature(self, title: str, company: str, city: str) -> str:
        """Create MD5 signature based on title, company, and city to catch cross-source duplicates."""
        base = f"{title.lower()}|{company.lower()}|{city.lower()}".strip()
        return hashlib.md5(base.encode("utf-8")).hexdigest()

    def clean_records(self, raw_records: List[RawJobRecord]) -> Tuple[List[Dict[str, Any]], QualityReport]:
        report = QualityReport(records_processed=len(raw_records))
        cleaned_jobs: List[Dict[str, Any]] = []
        self.seen_signatures.clear()

        for rec in raw_records:
            # 1. Clean HTML & normalize text
            raw_title = rec.title
            norm_title = normalize_title(raw_title)
            norm_company = normalize_company_name(rec.company)
            norm_city, norm_region = normalize_city(rec.location)
            clean_desc = strip_html(rec.description)

            # 2. Duplicate Detection
            sig = self.generate_dedup_signature(norm_title, norm_company, norm_city)
            if sig in self.seen_signatures:
                report.duplicates_removed += 1
                logger.debug(f"Duplicate detected and filtered: {rec.job_id} ({norm_title} at {norm_company})")
                continue
            self.seen_signatures.add(sig)

            # 3. Build cleaned dictionary
            job_dict: Dict[str, Any] = {
                "job_id": rec.job_id,
                "source": rec.source,
                "title": raw_title.strip() if raw_title else "Software Developer",
                "normalized_title": norm_title,
                "company": rec.company.strip() if rec.company else "Tech Company",
                "normalized_company": norm_company,
                "description": clean_desc,
                "location": norm_city,
                "region": norm_region,
                "remote": rec.remote or "On-site",
                "employment_type": rec.employment_type or "Full-time",
                "published_date": rec.published_date or "2025-01-01",
                "salary_min": float(rec.salary_min) if rec.salary_min is not None else None,
                "salary_max": float(rec.salary_max) if rec.salary_max is not None else None,
                "currency": rec.currency or "DKK",
                "url": rec.url or "",
                "language_requirements": rec.language_requirements or "",
                "experience_level": rec.experience_level or "Mid",
                "education_requirements": rec.education_requirements or "",
                "technologies": rec.technologies or [],
                "skills": rec.skills or [],
                "industry": rec.industry or "Technology"
            }

            # 4. Validate
            is_valid, error_msg = validate_job_record(job_dict)
            if not is_valid:
                report.invalid_records += 1
                report.errors.append({"job_id": rec.job_id, "error": error_msg})
                logger.warning(f"Invalid record dropped {rec.job_id}: {error_msg}")
                continue

            report.valid_records += 1
            cleaned_jobs.append(job_dict)

        logger.info(
            f"Cleaning finished: {report.valid_records} valid out of {report.records_processed} "
            f"({report.duplicates_removed} duplicates, {report.invalid_records} invalid)"
        )
        return cleaned_jobs, report
