"""
Unit tests for data transformations, derived feature calculations,
and 4-way language requirement detection (English, Danish, Both, Unknown).
"""

import unittest
from src.skill_extraction.extractor import SkillExtractor
from src.transformation.transformer import DataTransformer, detect_language_requirement

class TestDataTransformations(unittest.TestCase):
    def setUp(self):
        self.extractor = SkillExtractor()
        self.transformer = DataTransformer(self.extractor)

    def test_language_detection_english_only(self):
        """Verify English classification when Danish is explicitly not required or international corporate language."""
        text = "Our corporate language is English. Danish is not required for this role."
        self.assertEqual(detect_language_requirement(text), "English")

        job = {
            "title": "Cloud Platform Engineer",
            "description": text,
            "language_requirements": "English only"
        }
        res = self.transformer.transform_record(job)
        self.assertEqual(res["language_requirement"], "English")
        self.assertFalse(res["is_danish_required"])
        self.assertTrue(res["is_english_only"])

    def test_language_detection_danish_only(self):
        """Verify Danish classification when Danish fluency is required."""
        text = "Vi søger en kollega til interne projekter. Flydende dansk både skriftligt og mundtligt er et krav."
        self.assertEqual(detect_language_requirement(text), "Danish")

        job = {
            "title": "Data Specialist",
            "description": text,
            "language_requirements": "Danish required"
        }
        res = self.transformer.transform_record(job)
        self.assertEqual(res["language_requirement"], "Danish")
        self.assertTrue(res["is_danish_required"])
        self.assertFalse(res["is_english_only"])

    def test_language_detection_both_languages(self):
        """Verify Both classification when both Danish and English are expected."""
        text1 = "Stillingen kræver både dansk og engelsk på højt niveau."
        self.assertEqual(detect_language_requirement(text1), "Both")

        text2 = "Gode danskkundskaber forventes til kundekontakt, samt fluent English for international code reviews."
        self.assertEqual(detect_language_requirement(text2), "Both")

        job = {
            "title": "IT Consultant",
            "description": text2,
            "language_requirements": "Both Danish and English"
        }
        res = self.transformer.transform_record(job)
        self.assertEqual(res["language_requirement"], "Both")
        self.assertTrue(res["is_danish_required"])
        self.assertFalse(res["is_english_only"])

    def test_language_detection_unknown_unstated(self):
        """Verify Unknown classification when no language requirement is mentioned."""
        text = "We are seeking a Python developer with experience in Docker and PostgreSQL."
        self.assertEqual(detect_language_requirement(text), "Unknown")

        job = {
            "title": "Backend Engineer",
            "description": text,
            "language_requirements": ""
        }
        res = self.transformer.transform_record(job)
        self.assertEqual(res["language_requirement"], "Unknown")
        self.assertFalse(res["is_danish_required"])
        self.assertFalse(res["is_english_only"])

    def test_explicit_language_requirement_field_override(self):
        """Verify explicit language_requirements field values (English, Danish, Both)."""
        self.assertEqual(detect_language_requirement("", "English"), "English")
        self.assertEqual(detect_language_requirement("", "Danish"), "Danish")
        self.assertEqual(detect_language_requirement("", "Both"), "Both")
        self.assertEqual(detect_language_requirement("", "Danish and English"), "Both")
        self.assertEqual(detect_language_requirement("", "Unspecified"), "Unknown")

    def test_danish_negation_not_flagged_as_danish(self):
        """Ensure sentences like 'Danish is not required' or 'intet krav om dansk' do not trigger Danish requirement."""
        text1 = "Work in our Copenhagen hub. Note: Danish is not required, our company language is English."
        self.assertEqual(detect_language_requirement(text1), "English")

        text2 = "Dansk er ikke et krav til denne stilling. Working language is English."
        self.assertEqual(detect_language_requirement(text2), "English")

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
