"""
Data Quality and Validation for Danish Job Market pipeline.
Enforces business rules and schema integrity before loading into the database.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

KNOWN_SOURCES = {
    "synthetic_demo", "mock_source", "csv_import",
    "jobindex_dk", "jobnet_dk", "the_hub", "linkedin_jobs"
}

@dataclass
class QualityReport:
    records_processed: int = 0
    valid_records: int = 0
    duplicates_removed: int = 0
    invalid_records: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> Dict[str, Any]:
        return {
            "records_processed": self.records_processed,
            "valid_records": self.valid_records,
            "duplicates_removed": self.duplicates_removed,
            "invalid_records": self.invalid_records,
            "data_health_pct": round(
                (self.valid_records / self.records_processed * 100) if self.records_processed else 0, 1
            )
        }

def validate_job_record(job: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate a single cleaned job record according to strict DQ rules."""
    job_id = job.get("job_id")
    if not job_id or not str(job_id).strip():
        return False, "job_id must not be null or empty"

    title = job.get("title")
    if not title or not str(title).strip():
        return False, "title must not be empty"

    source = job.get("source")
    if not source or source not in KNOWN_SOURCES:
        return False, f"source '{source}' is not recognized"

    # Date check
    pub_date = job.get("published_date")
    if pub_date:
        try:
            datetime.strptime(str(pub_date)[:10], "%Y-%m-%d")
        except ValueError:
            return False, f"published_date '{pub_date}' must follow ISO YYYY-MM-DD"

    # Salary check
    sal_min = job.get("salary_min")
    sal_max = job.get("salary_max")
    if sal_min is not None and sal_max is not None:
        if float(sal_min) > float(sal_max):
            return False, f"salary_min ({sal_min}) cannot exceed salary_max ({sal_max})"

    return True, None
