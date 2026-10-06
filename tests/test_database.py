"""
Unit tests for database schema, upsert logic, and analytical queries.
"""

import tempfile
import unittest
from pathlib import Path
from src.database.connection import get_connection, init_database
from src.database.repository import JobRepository

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_jobs.db"
        init_database(self.db_path)
        self.repo = JobRepository(str(self.db_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schema_initialization(self):
        with self.repo.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row["name"] for row in cur.fetchall()]
            self.assertIn("jobs", tables)
            self.assertIn("companies", tables)
            self.assertIn("locations", tables)
            self.assertIn("skills", tables)
            self.assertIn("job_skills", tables)
            self.assertIn("sources", tables)

    def test_upsert_and_retrieve_job(self):
        self.repo.upsert_source("test_source", "Test Source", is_synthetic=True)
        cid = self.repo.get_or_create_company("TestCorp", "TestCorp", "Data")
        lid = self.repo.get_or_create_location("Copenhagen", "Hovedstaden")
        sid = self.repo.get_or_create_skill("Python", "Programming")

        job_data = {
            "job_id": "TEST-01",
            "source_id": "test_source",
            "company_id": cid,
            "location_id": lid,
            "title": "Junior Data Specialist",
            "normalized_title": "Junior Data Specialist",
            "role_category": "Data Engineering",
            "description": "Awesome role",
            "remote_type": "Hybrid",
            "published_date": "2025-01-01",
            "salary_min": 42000,
            "salary_max": 48000,
            "is_danish_required": False,
            "is_english_only": True,
            "is_junior": True,
            "skill_ids": [sid]
        }
        self.repo.upsert_job(job_data)

        jobs = self.repo.get_all_jobs(limit=10)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["job_id"], "TEST-01")
        self.assertEqual(jobs[0]["company_name"], "TestCorp")
        self.assertEqual(jobs[0]["skills_list"], "Python")

if __name__ == "__main__":
    unittest.main()
