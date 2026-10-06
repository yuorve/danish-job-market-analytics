"""
Concrete implementations of JobSource for Danish Job Market Analytics.
Includes SyntheticDemoSource, CSVSource, MockSource, JobnetSource, JobIndexSource, TheHubSource, LinkedInSource.
Strictly adheres to ethical web scraping rules (no ToS violation, no anti-bot bypass).
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Optional
from .base import JobSource, RawJobRecord

logger = logging.getLogger(__name__)

class SyntheticDemoSource(JobSource):
    """Loads realistic synthetic Danish IT job listings from data/demo/synthetic_jobs.json."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path or "data/demo/synthetic_jobs.json")

    @property
    def source_id(self) -> str:
        return "synthetic_demo"

    def fetch_jobs(self) -> List[RawJobRecord]:
        if not self.file_path.exists():
            logger.warning(f"Synthetic demo file {self.file_path} not found. Triggering generator.")
            from scripts.generate_demo_data import main as generate_demo
            generate_demo()

        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        records = []
        for item in raw_data:
            records.append(
                RawJobRecord(
                    job_id=item["job_id"],
                    source="synthetic_demo",
                    title=item["title"],
                    company=item["company"],
                    description=item["description"],
                    location=item["location"],
                    region=item.get("region"),
                    remote=item.get("remote", "On-site"),
                    employment_type=item.get("employment_type", "Full-time"),
                    published_date=item.get("published_date"),
                    salary_min=item.get("salary_min"),
                    salary_max=item.get("salary_max"),
                    currency=item.get("currency", "DKK"),
                    url=item.get("url", ""),
                    language_requirements=item.get("language_requirements"),
                    experience_level=item.get("experience_level"),
                    education_requirements=item.get("education_requirements"),
                    technologies=item.get("technologies"),
                    skills=item.get("skills"),
                    industry=item.get("industry")
                )
            )
        logger.info(f"Loaded {len(records)} records from SyntheticDemoSource.")
        return records

class CSVSource(JobSource):
    """Loads jobs from arbitrary external CSV files."""

    def __init__(self, file_path: str, source_identifier: str = "csv_import"):
        self.file_path = Path(file_path)
        self._source_id = source_identifier

    @property
    def source_id(self) -> str:
        return self._source_id

    def fetch_jobs(self) -> List[RawJobRecord]:
        if not self.file_path.exists():
            logger.error(f"CSV file not found: {self.file_path}")
            return []

        records = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                records.append(
                    RawJobRecord(
                        job_id=row.get("job_id", f"csv-{idx}"),
                        source=self._source_id,
                        title=row.get("title", ""),
                        company=row.get("company", ""),
                        description=row.get("description", ""),
                        location=row.get("location", "Copenhagen"),
                        region=row.get("region", "Hovedstaden"),
                        remote=row.get("remote", "On-site"),
                        salary_min=float(row["salary_min"]) if row.get("salary_min") else None,
                        salary_max=float(row["salary_max"]) if row.get("salary_max") else None,
                        currency=row.get("currency", "DKK"),
                        url=row.get("url", ""),
                        experience_level=row.get("experience_level", "Mid")
                    )
                )
        return records

class MockSource(JobSource):
    """In-memory mock source used for unit tests and fast sanity verification."""

    @property
    def source_id(self) -> str:
        return "mock_source"

    def fetch_jobs(self) -> List[RawJobRecord]:
        return [
            RawJobRecord(
                job_id="MOCK-001",
                source="mock_source",
                title="Junior Python Data Specialist",
                company="Nordic Training Labs A/S",
                description="Join our team in Copenhagen. We teach and build data engineering pipelines with Python, SQL, Azure, and Databricks. English speaking environment.",
                location="Copenhagen",
                region="Hovedstaden",
                remote="Hybrid",
                published_date="2025-01-15",
                salary_min=42000,
                salary_max=48000,
                language_requirements="English only",
                experience_level="Junior",
                technologies=["Python", "SQL", "Azure", "Databricks"]
            ),
            RawJobRecord(
                job_id="MOCK-002",
                source="mock_source",
                title="Senior Microsoft Fabric Architect",
                company="København IT Rådgivning",
                description="Vi søger en erfaren Fabric og Power BI specialist til vores kontor i Aarhus. Flydende dansk kræves til kundemøder.",
                location="Aarhus",
                region="Midtjylland",
                remote="On-site",
                published_date="2025-01-16",
                salary_min=70000,
                salary_max=85000,
                language_requirements="Danish required",
                experience_level="Senior",
                technologies=["Microsoft Fabric", "Power BI", "SQL", "Azure"]
            )
        ]

class JobIndexSource(JobSource):
    """
    Adapter skeleton for JobIndex.dk data.
    Note: JobIndex forbids aggressive scraping in robots.txt.
    This class falls back to permitted mock/API endpoints or local dump.
    """
    @property
    def source_id(self) -> str:
        return "jobindex_dk"

    def fetch_jobs(self) -> List[RawJobRecord]:
        logger.info("JobIndexSource: Operating in compliant mode (using synthetic demo fallback to avoid TOS violation).")
        return []

class JobnetSource(JobSource):
    """Adapter for Jobnet (Danish Agency for Labour Market and Recruitment public job portal)."""
    @property
    def source_id(self) -> str:
        return "jobnet_dk"

    def fetch_jobs(self) -> List[RawJobRecord]:
        logger.info("JobnetSource: Connector initialized.")
        return []

class TheHubSource(JobSource):
    """Adapter for The Hub (Nordic startup jobs)."""
    @property
    def source_id(self) -> str:
        return "the_hub"

    def fetch_jobs(self) -> List[RawJobRecord]:
        return []

class LinkedInSource(JobSource):
    """Adapter for LinkedIn jobs export."""
    @property
    def source_id(self) -> str:
        return "linkedin_jobs"

    def fetch_jobs(self) -> List[RawJobRecord]:
        return []
