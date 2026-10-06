"""
Unit tests for data cleaning, normalizations, and quality validation.
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

    def test_deduplication(self):
        records = [
            RawJobRecord(
                job_id="REC-1",
                source="synthetic_demo",
                title="Python Data Engineer",
                company="Trifork A/S",
                description="Developing data pipelines.",
                location="Copenhagen"
            ),
            RawJobRecord(
                job_id="REC-2",
                source="synthetic_demo",
                title="Python Data Engineer",
                company="Trifork",
                description="Duplicate posting on another board.",
                location="København"
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
