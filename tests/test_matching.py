"""
Unit tests for Candidate Matching engine and Danish language warning flags.
"""

import unittest
from src.matching.matcher import CandidateMatcher

class TestCandidateMatching(unittest.TestCase):
    def setUp(self):
        self.matcher = CandidateMatcher()

    def test_strong_candidate_match(self):
        candidate = {
            "skills": ["Python", "SQL", "Git", "Docker", "Azure"],
            "languages": {"english": "C1", "danish": "A1"},
            "experience": {"level": "junior"}
        }
        job = {
            "job_id": "TEST-MATCH-1",
            "title": "Junior Data Specialist",
            "company": "Nordic Tech",
            "location": "Copenhagen",
            "skills": ["Python", "SQL", "Azure"],
            "is_danish_required": False,
            "is_english_only": True,
            "experience_level": "Junior"
        }
        res = self.matcher.evaluate_match(candidate, job)
        self.assertGreaterEqual(res.match_score, 85)
        self.assertEqual(len(res.matched_skills), 3)
        self.assertEqual(len(res.missing_skills), 0)
        self.assertTrue(res.language_match)

    def test_danish_requirement_warning(self):
        candidate = {
            "skills": ["Python", "SQL"],
            "languages": {"english": "B2", "danish": "A1"},
            "experience": {"level": "junior"}
        }
        job = {
            "job_id": "TEST-DANISH-1",
            "title": "Data Consultant",
            "company": "KMD",
            "location": "Ballerup",
            "skills": ["Python", "SQL"],
            "is_danish_required": True,
            "experience_level": "Junior"
        }
        res = self.matcher.evaluate_match(candidate, job)
        self.assertFalse(res.language_match)
        self.assertIn("requires Danish fluency", res.language_note)
        self.assertLess(res.match_score, 90)

    def test_missing_skills_identification(self):
        candidate = {
            "skills": ["Python"],
            "languages": {"english": "B2", "danish": "B2"},
            "experience": {"level": "junior"}
        }
        job = {
            "job_id": "TEST-MISSING-1",
            "title": "Lakehouse Engineer",
            "company": "Novo Nordisk",
            "location": "Bagsværd",
            "skills": ["Python", "Databricks", "Microsoft Fabric", "dbt"],
            "is_danish_required": False,
            "experience_level": "Junior"
        }
        res = self.matcher.evaluate_match(candidate, job)
        self.assertIn("Databricks", res.missing_skills)
        self.assertIn("Microsoft Fabric", res.missing_skills)
        self.assertIn("dbt", res.missing_skills)

    def test_unknown_language_treated_as_unverified_warning(self):
        candidate = {
            "skills": ["Python", "SQL"],
            "languages": {"english": "C1", "danish": "A1"},
            "experience": {"level": "junior"}
        }
        job = {
            "job_id": "TEST-UNKNOWN-LANG",
            "title": "Software Developer",
            "company": "Pleo",
            "location": "Copenhagen",
            "skills": ["Python", "SQL"],
            "language_requirement": "Unknown",
            "experience_level": "Junior"
        }
        res = self.matcher.evaluate_match(candidate, job)
        self.assertFalse(res.language_match, "Unknown language must NOT be flagged as a satisfied match!")
        self.assertIn("Warning", res.language_note)
        self.assertIn("unstated", res.language_note.lower())
        # With zero points for language, maximum score is bounded to tech (70) + seniority (10) = 80
        self.assertLessEqual(res.match_score, 80)

if __name__ == "__main__":
    unittest.main()
