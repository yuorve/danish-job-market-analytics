"""
Data Transformation & Feature Engineering for Danish Job Market Analytics.
Computes domain indicators:
- is_danish_required
- is_english_only
- is_remote
- is_hybrid
- is_junior
- is_data_role
- is_ai_role
- is_devops_role
- is_cloud_role
- role_category
"""

import re
from typing import Any, Dict, List
from src.skill_extraction.extractor import SkillExtractor

# Danish language requirement cues
DANISH_REQUIRED_PATTERNS = re.compile(
    r"\b(flydende\s+dansk|dansk\s+(?:både\s+)?skriftligt|dansk\s+på\s+modersmålsniveau|"
    r"gode\s+danskkundskaber|danish\s+required|fluent\s+in\s+danish|talende\s+dansk|"
    r"taler\s+og\s+skriver\s+dansk|dansk\s+er\s+et\s+krav)\b",
    re.IGNORECASE
)

ENGLISH_FRIENDLY_PATTERNS = re.compile(
    r"\b(corporate\s+language\s+is\s+english|english\s+only|working\s+language\s+is\s+english|"
    r"danish\s+is\s+not\s+required|international\s+environment|english\s+speaking)\b",
    re.IGNORECASE
)

JUNIOR_PATTERNS = re.compile(
    r"\b(junior|graduate|nyuddannet|entry\s*level|associate|0-2\s+years|recent\s+graduate|"
    r"trainee|student\s+assistant|internship|early\s+career|instructor)\b",
    re.IGNORECASE
)

DATA_PATTERNS = re.compile(
    r"\b(data\s+engineer|data\s+specialist|lakehouse|etl|dbt|spark|databricks|fabric|"
    r"analytics\s+engineer|data\s+platform|sql\s+developer|data\s+warehouse|bi\s+developer)\b",
    re.IGNORECASE
)

AI_PATTERNS = re.compile(
    r"\b(machine\s+learning|ai\s+engineer|llm|generative\s+ai|deep\s+learning|computer\s+vision|nlp|mlops)\b",
    re.IGNORECASE
)

DEVOPS_PATTERNS = re.compile(
    r"\b(devops|platform\s+engineer|sre|site\s+reliability|kubernetes|infrastructure|cloud\s+engineer)\b",
    re.IGNORECASE
)

class DataTransformer:
    def __init__(self, skill_extractor: SkillExtractor):
        self.skill_extractor = skill_extractor

    def transform_record(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich cleaned job dictionary with derived analytical dimensions."""
        title = raw_job.get("title", "")
        desc = raw_job.get("description", "")
        combined_text = f"{title} {desc} {raw_job.get('language_requirements', '')}".lower()

        # 1. Skill Extraction
        explicit_skills = raw_job.get("technologies") or raw_job.get("skills") or []
        extracted = self.skill_extractor.extract_skills(combined_text, explicit_skills)
        skill_names = [s["name"] for s in extracted]

        # 2. Language Requirement Classification
        danish_match = bool(DANISH_REQUIRED_PATTERNS.search(combined_text))
        english_match = bool(ENGLISH_FRIENDLY_PATTERNS.search(combined_text))

        if danish_match:
            is_danish_required = True
            is_english_only = False
        elif english_match:
            is_danish_required = False
            is_english_only = True
        else:
            # Default to English-friendly in Danish IT unless specified
            is_danish_required = False
            is_english_only = True

        # 3. Junior & Experience Classification
        exp_raw = str(raw_job.get("experience_level", "")).lower()
        is_junior = bool(JUNIOR_PATTERNS.search(title)) or ("junior" in exp_raw)

        if is_junior:
            exp_level = "Junior"
        elif "senior" in title.lower() or "senior" in exp_raw or "lead" in title.lower():
            exp_level = "Senior"
        else:
            exp_level = "Mid"

        # 4. Role Domains
        is_data = bool(DATA_PATTERNS.search(f"{title} {desc}")) or any(s in skill_names for s in ["SQL", "Databricks", "Microsoft Fabric", "dbt", "Apache Spark", "Pandas"])
        is_ai = bool(AI_PATTERNS.search(f"{title} {desc}")) or any(s in skill_names for s in ["Machine Learning", "LLM", "Generative AI", "PyTorch", "RAG"])
        is_devops = bool(DEVOPS_PATTERNS.search(f"{title} {desc}")) or any(s in skill_names for s in ["Kubernetes", "Terraform", "CI/CD"])
        is_cloud = "Azure" in skill_names or "AWS" in skill_names or "GCP" in skill_names or "Docker" in skill_names

        # Assign primary role category
        if is_data:
            role_category = "Data Engineering"
        elif is_ai:
            role_category = "AI & Machine Learning"
        elif is_devops:
            role_category = "Cloud & DevOps"
        elif "Power BI" in skill_names or "Tableau" in skill_names:
            role_category = "BI & Analytics"
        else:
            role_category = "Software Development"

        # 5. Remote / Hybrid Policy
        remote_str = str(raw_job.get("remote", "")).lower()
        is_remote = "remote" in remote_str
        is_hybrid = "hybrid" in remote_str

        # 6. Salaries
        sal_min = raw_job.get("salary_min")
        sal_max = raw_job.get("salary_max")
        sal_avg = (sal_min + sal_max) / 2 if (sal_min and sal_max) else (sal_min or sal_max)

        return {
            **raw_job,
            "role_category": role_category,
            "extracted_skills": extracted,
            "skill_names": skill_names,
            "is_danish_required": is_danish_required,
            "is_english_only": is_english_only,
            "is_remote": is_remote,
            "is_hybrid": is_hybrid,
            "is_junior": is_junior,
            "is_data_role": is_data,
            "is_ai_role": is_ai,
            "is_devops_role": is_devops,
            "is_cloud_role": is_cloud,
            "experience_level": exp_level,
            "salary_avg": sal_avg
        }
