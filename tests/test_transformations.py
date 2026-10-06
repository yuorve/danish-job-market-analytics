"""
Unit tests for data transformations and derived feature calculations.
"""

import unittest
from src.skill_extraction.extractor import SkillExtractor
from src.transformation.transformer import DataTransformer

class TestDataTransformations(unittest.TestCase):
    def setUp(self):
        self.extractor = SkillExtractor()
        self.transformer = DataTransformer(self.extractor)

    def test_danish_language_requirement_flag(self):
        job = {
            "title": "Data Specialist",
            "description": "Vi søger en kollega til kundeprojekter. Flydende dansk både skriftligt og mundtligt er et krav.",
            "language_requirements": "Danish required"
        }
        transformed = self.transformer.transform_record(job)
        self.assertTrue(transformed["is_danish_required"])
        self.assertFalse(transformed["is_english_only"])

    def test_english_friendly_flag(self):
        job = {
            "title": "Cloud Platform Engineer",
            "description": "Our corporate language is English. Danish is not required for this role.",
            "language_requirements": "English only"
        }
        transformed = self.transformer.transform_record(job)
        self.assertFalse(transformed["is_danish_required"])
        self.assertTrue(transformed["is_english_only"])

    def test_junior_flag_derivation(self):
        job1 = {"title": "Junior Python Developer", "description": "Entry level position for graduates."}
        res1 = self.transformer.transform_record(job1)
        self.assertTrue(res1["is_junior"])
        self.assertEqual(res1["experience_level"], "Junior")

        job2 = {"title": "Senior Solutions Architect", "description": "10+ years experience required."}
        res2 = self.transformer.transform_record(job2)
        self.assertFalse(res2["is_junior"])
        self.assertEqual(res2["experience_level"], "Senior")

    def test_role_category_data_engineering(self):
        job = {
            "title": "Databricks & Lakehouse Engineer",
            "description": "Building Spark and Microsoft Fabric pipelines using SQL and Python."
        }
        res = self.transformer.transform_record(job)
        self.assertEqual(res["role_category"], "Data Engineering")
        self.assertTrue(res["is_data_role"])

if __name__ == "__main__":
    unittest.main()
