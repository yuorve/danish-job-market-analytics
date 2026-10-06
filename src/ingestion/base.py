"""
Base interface and abstractions for job data ingestion.
Enforces the JobSource contract across real APIs, CSV files, and synthetic sources.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

@dataclass
class RawJobRecord:
    job_id: str
    source: str
    title: str
    company: str
    description: str
    location: str
    region: Optional[str] = None
    remote: Optional[str] = "On-site"
    employment_type: Optional[str] = "Full-time"
    published_date: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: Optional[str] = "DKK"
    url: Optional[str] = ""
    language_requirements: Optional[str] = None
    experience_level: Optional[str] = "Mid"
    education_requirements: Optional[str] = None
    technologies: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    industry: Optional[str] = "Technology"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class JobSource(ABC):
    """Abstract interface that all ingestion sources must implement."""

    @abstractmethod
    def fetch_jobs(self) -> List[RawJobRecord]:
        """Fetch raw job records from source."""
        pass

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier for the source."""
        pass
