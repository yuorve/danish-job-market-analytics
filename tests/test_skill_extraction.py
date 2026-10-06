"""
Unit tests for Skill and Technology Extraction.
"""

import unittest
from src.skill_extraction.extractor import SkillExtractor

class TestSkillExtraction(unittest.TestCase):
    def setUp(self):
        self.extractor = SkillExtractor()

    def test_extract_programming_languages(self):
        text = "Looking for an engineer proficient in Python, TypeScript, and Go."
        skills = self.extractor.extract_skills(text)
        names = [s["name"] for s in skills]
        self.assertIn("Python", names)
        self.assertIn("TypeScript", names)
        self.assertIn("Go", names)

    def test_extract_data_and_fabric_stack(self):
        text = "Experience with Microsoft Fabric, Databricks, Apache Spark, dbt, and Power BI."
        skills = self.extractor.extract_skills(text)
        names = [s["name"] for s in skills]
        self.assertIn("Microsoft Fabric", names)
        self.assertIn("Databricks", names)
        self.assertIn("Apache Spark", names)
        self.assertIn("dbt", names)
        self.assertIn("Power BI", names)

    def test_handles_csharp_and_dotnet_boundaries(self):
        text = "Backend built on .NET and C# with Azure SQL."
        skills = self.extractor.extract_skills(text)
        names = [s["name"] for s in skills]
        self.assertIn("C#", names)
        self.assertIn(".NET", names)
        self.assertIn("Azure", names)
        self.assertIn("SQL", names)

    def test_extract_ai_technologies(self):
        text = "Hands-on experience with LLM applications, RAG architecture, and PyTorch."
        skills = self.extractor.extract_skills(text)
        names = [s["name"] for s in skills]
        self.assertIn("LLM", names)
        self.assertIn("RAG", names)
        self.assertIn("PyTorch", names)

if __name__ == "__main__":
    unittest.main()
