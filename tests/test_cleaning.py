"""
Unit tests for data cleaning, normalizations, and quality validation.
Includes tests for two-stage deduplication (URL check + content similarity)
ensuring genuinely distinct job vacancies at the same employer are preserved.
"""

import unittest
from src.ingestion.base import RawJobRecord
from src.cleaning.cleaner import DataCleaner
from src.cleaning.normalizers import (
    normalize_city,
    normalize_company_name,
    normalize_title,
    strip_html
)
from src.cleaning.validator import validate_job_record

class TestDataCleaning(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()

    def test_strip_html(self):
        raw = "<p>Senior <strong>Python</strong> Developer &amp; Data Engineer</p><br/>"
        expected = "Senior Python Developer & Data Engineer"
        self.assertEqual(strip_html(raw), expected)

    def test_normalize_city_danish_variants(self):
        city, region = normalize_city("København")
        self.assertEqual(city, "Copenhagen")
        self.assertEqual(region, "Hovedstaden")

        city, region = normalize_city("Århus")
        self.assertEqual(city, "Aarhus")
        self.assertEqual(region, "Midtjylland")

        city, region = normalize_city("Kgs. Lyngby")
        self.assertEqual(city, "Lyngby")

    def test_normalize_company_name(self):
        self.assertEqual(normalize_company_name("Novo Nordisk A/S"), "Novo Nordisk")
        self.assertEqual(normalize_company_name("Netcompany ApS"), "Netcompany")
        self.assertEqual(normalize_company_name("Maersk Group"), "Maersk")

    def test_deduplication_exact_republication(self):
        """Republications with identical or near-identical text must be dropped."""
        desc = (
            "We are looking for a Data Engineer to build Azure Databricks lakehouse pipelines "
            "with dbt and PySpark. High standards for automated CI/CD and clean data modeling."
        )
        records = [
            RawJobRecord(
                job_id="REC-1",
                source="jobindex_dk",
                title="Data Engineer",
                company="Trifork A/S",
                description=desc,
                location="Copenhagen",
                url="https://jobindex.dk/job/101"
            ),
            RawJobRecord(
                job_id="REC-2",
                source="the_hub",
                title="Data Engineer",
                company="Trifork",
                description=f"<p>{desc}</p>",  # Same description wrapped in HTML tags
                location="København",
                url="https://thehub.io/jobs/202"
            ),
        ]
        cleaned, report = self.cleaner.clean_records(records)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report.duplicates_removed, 1)

    def test_deduplication_preserves_distinct_vacancies_same_company(self):
        """Two distinct vacancies with the same title at the same company must NOT be dropped."""
        records = [
            RawJobRecord(
                job_id="VAC-101",
                source="jobindex_dk",
                title="Software Engineer",
                company="Novo Nordisk",
                location="Bagsværd",
                description=(
                    "Join our Clinical Trial Analytics platform team. Designing reactive microservices "
                    "in TypeScript, GraphQL, and Node.js for global regulatory submission workflows."
                ),
                url="https://novonordisk.com/jobs/clinical-101"
            ),
            RawJobRecord(
                job_id="VAC-102",
                source="jobindex_dk",
                title="Software Engineer",
                company="Novo Nordisk A/S",
                location="Bagsværd",
                description=(
                    "Join our Supply Chain Automation team. Implementing IoT sensor telemetry ingestion, "
                    "Python backend services, and industrial equipment control integrations."
                ),
                url="https://novonordisk.com/jobs/supply-chain-102"
            ),
        ]
        cleaned, report = self.cleaner.clean_records(records)
        self.assertEqual(len(cleaned), 2, "Distinct vacancies at same employer must be preserved!")
        self.assertEqual(report.duplicates_removed, 0)

    def test_deduplication_exact_url_collision(self):
        """Records with the same application URL are immediate duplicates."""
        records = [
            RawJobRecord(
                job_id="URL-1",
                source="jobindex_dk",
                title="C# Backend Developer",
                company="SimCorp",
                location="Copenhagen",
                description="Developing investment management software.",
                url="https://simcorp.com/careers/csharp-01/"
            ),
            RawJobRecord(
                job_id="URL-2",
                source="linkedin_jobs",
                title="Senior C# Developer",
                company="SimCorp",
                location="Copenhagen",
                description="Repost of the same position on LinkedIn.",
                url="https://simcorp.com/careers/csharp-01"  # Trailing slash difference
            ),
        ]
        cleaned, report = self.cleaner.clean_records(records)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(report.duplicates_removed, 1)

    def test_validation_rejects_invalid_salaries(self):
        invalid_job = {
            "job_id": "VAL-1",
            "source": "synthetic_demo",
            "title": "Software Engineer",
            "salary_min": 60000,
            "salary_max": 40000  # min > max should fail
        }
        is_valid, err = validate_job_record(invalid_job)
        self.assertFalse(is_valid)
        self.assertIn("cannot exceed", err)

if __name__ == "__main__":
    unittest.main()
