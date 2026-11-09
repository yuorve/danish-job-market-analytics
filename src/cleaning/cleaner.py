"""
Data Cleaning stage for Danish Job Market Analytics.
Handles deduplication, HTML stripping, entity normalization, and validation logging.
Implements two-stage deduplication:
1. Exact Canonical URL / ID matching.
2. Cross-board republication similarity analysis (company + title + city + description token similarity)
   preventing accidental merging of distinct job vacancies at the same employer.
"""

import hashlib
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from src.ingestion.base import RawJobRecord
from .normalizers import normalize_city, normalize_company_name, normalize_title, strip_html
from .validator import QualityReport, validate_job_record

logger = logging.getLogger(__name__)


def extract_description_tokens(text: Optional[str]) -> Set[str]:
    """Tokenize and normalize text for similarity comparison."""
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    # Exclude very short stopwords/single chars
    tokens = {word for word in cleaned.split() if len(word) > 2}
    return tokens


def calculate_jaccard_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Calculate token Jaccard similarity between two token sets."""
    if not tokens_a and not tokens_b:
        return 1.0
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return intersection / union if union > 0 else 0.0


def calculate_containment_similarity(tokens_a: Set[str], tokens_b: Set[str]) -> float:
    """Calculate containment similarity (useful when one posting wraps or abbreviates another)."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = len(tokens_a & tokens_b)
    min_len = min(len(tokens_a), len(tokens_b))
    return intersection / min_len if min_len > 0 else 0.0


class DataCleaner:
    def __init__(self, similarity_threshold: float = 0.65):
        self.similarity_threshold = similarity_threshold
        # Stores seen URLs to catch exact URL republications
        self.seen_urls: Set[str] = set()
        # Stores seen job IDs
        self.seen_job_ids: Set[str] = set()
        # Group seen postings by entity key: (norm_company, norm_city, norm_title) -> list of posting metadata
        self.entity_postings: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}

    def is_duplicate_republication(
        self,
        norm_title: str,
        norm_company: str,
        norm_city: str,
        clean_desc: str,
        url: Optional[str],
        job_id: str
    ) -> Tuple[bool, str]:
        """
        Determine if a posting is a duplicate republication using two-stage validation:
        1. Exact URL / job_id check.
        2. Attribute + Content similarity check under the same (company, city, title) entity bucket.
           Distinct vacancies with different descriptions are preserved.
        """
        # 1. Exact ID check
        if job_id and job_id in self.seen_job_ids:
            return True, f"Exact job_id collision: {job_id}"

        # 2. Canonical URL check
        norm_url = url.strip().lower().rstrip("/") if url else ""
        if norm_url and norm_url in self.seen_urls:
            return True, f"Exact canonical URL match: {norm_url}"

        # 3. Entity bucket similarity check
        entity_key = (norm_company.lower(), norm_city.lower(), norm_title.lower())
        existing_in_bucket = self.entity_postings.get(entity_key, [])

        if existing_in_bucket:
            new_tokens = extract_description_tokens(clean_desc)
            desc_hash = hashlib.md5(clean_desc.strip().lower().encode("utf-8")).hexdigest()

            for existing in existing_in_bucket:
                # Exact identical normalized description text
                if existing.get("desc_hash") == desc_hash:
                    return True, f"Identical description hash for {norm_title} at {norm_company}"

                existing_tokens = existing.get("tokens", set())
                # If both postings have substantive descriptions, compare token similarity
                if len(new_tokens) >= 15 and len(existing_tokens) >= 15:
                    jaccard = calculate_jaccard_similarity(new_tokens, existing_tokens)
                    containment = calculate_containment_similarity(new_tokens, existing_tokens)

                    # Substantial token overlap indicates duplicate reposting on another board
                    if jaccard >= self.similarity_threshold or containment >= 0.85:
                        return True, (
                            f"Republication detected (Jaccard: {jaccard:.2f}, Containment: {containment:.2f}) "
                            f"for {norm_title} at {norm_company}"
                        )
                elif len(new_tokens) < 15 and len(existing_tokens) < 15:
                    # In degenerate cases where neither posting has a real description,
                    # identical entity key is flagged as duplicate placeholder
                    return True, f"Placeholder duplicate without description for {norm_title} at {norm_company}"

        return False, ""

    def register_posting(
        self,
        norm_title: str,
        norm_company: str,
        norm_city: str,
        clean_desc: str,
        url: Optional[str],
        job_id: str
    ) -> None:
        """Register a valid posting in the deduplication index."""
        if job_id:
            self.seen_job_ids.add(job_id)
        if url:
            self.seen_urls.add(url.strip().lower().rstrip("/"))

        entity_key = (norm_company.lower(), norm_city.lower(), norm_title.lower())
        tokens = extract_description_tokens(clean_desc)
        desc_hash = hashlib.md5(clean_desc.strip().lower().encode("utf-8")).hexdigest()

        if entity_key not in self.entity_postings:
            self.entity_postings[entity_key] = []

        self.entity_postings[entity_key].append({
            "job_id": job_id,
            "url": url,
            "tokens": tokens,
            "desc_hash": desc_hash
        })

    def clean_records(self, raw_records: List[RawJobRecord]) -> Tuple[List[Dict[str, Any]], QualityReport]:
        report = QualityReport(records_processed=len(raw_records))
        cleaned_jobs: List[Dict[str, Any]] = []

        self.seen_urls.clear()
        self.seen_job_ids.clear()
        self.entity_postings.clear()

        for rec in raw_records:
            # 1. Clean HTML & normalize text
            raw_title = rec.title
            norm_title = normalize_title(raw_title)
            norm_company = normalize_company_name(rec.company)
            norm_city, norm_region = normalize_city(rec.location)
            clean_desc = strip_html(rec.description)

            # 2. Duplicate Detection
            is_dup, reason = self.is_duplicate_republication(
                norm_title=norm_title,
                norm_company=norm_company,
                norm_city=norm_city,
                clean_desc=clean_desc,
                url=rec.url,
                job_id=rec.job_id
            )

            if is_dup:
                report.duplicates_removed += 1
                logger.debug(f"Duplicate detected: {rec.job_id} ({norm_title} at {norm_company}) - {reason}")
                continue

            self.register_posting(
                norm_title=norm_title,
                norm_company=norm_company,
                norm_city=norm_city,
                clean_desc=clean_desc,
                url=rec.url,
                job_id=rec.job_id
            )

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
