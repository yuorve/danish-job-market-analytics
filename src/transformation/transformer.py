"""
Data Transformation & Feature Engineering for Danish Job Market Analytics.
Computes domain indicators:
- language_requirement: 'English', 'Danish', 'Both', or 'Unknown'
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
from typing import Any, Dict, List, Optional
from src.skill_extraction.extractor import SkillExtractor

# Danish language requirement cues
DANISH_REQUIRED_PATTERNS = re.compile(
    r"\b(flydende\s+dansk|flydende\s+på\s+dansk|dansk\s+(?:både\s+)?skriftligt|dansk\s+på\s+modersmålsniveau|"
    r"modersmål\s+dansk|gode\s+danskkundskaber|stærke\s+danskkundskaber|danish\s+required|"
    r"fluent\s+in\s+danish|talende\s+dansk|taler\s+og\s+skriver\s+dansk|dansk\s+er\s+et\s+krav|"
    r"krav\s+om\s+dansk|danskkundskaber|dansk\s+tale\s+og\s+skrift|dansk\s+i\s+skrift\s+og\s+tale|"
    r"fluent\s+danish|behersker\s+dansk|dansksproget|dansktalende|arbejdssprog\s+er\s+dansk|"
    r"dansk\s+på\s+forhandlingsniveau|skal\s+kunne\s+begå\s+sig\s+på\s+dansk|dansk\s+som\s+modersmål)\b",
    re.IGNORECASE
)

# Negative Danish cues (explicitly asserting Danish is NOT required)
DANISH_NEGATION_PATTERNS = re.compile(
    r"\b(danish\s+is\s+not\s+required|no\s+danish\s+required|not\s+require\s+danish|without\s+danish|"
    r"dansk\s+er\s+ikke\s+et\s+krav|intet\s+krav\s+om\s+dansk|dansk\s+ikke\s+påkrævet|"
    r"behøver\s+ikke\s+(?:at\s+)?tale\s+dansk)\b",
    re.IGNORECASE
)

# English requirement / friendly cues
ENGLISH_FRIENDLY_PATTERNS = re.compile(
    r"\b(corporate\s+language\s+is\s+english|corporate\s+working\s+language\s+is\s+english|"
    r"working\s+language\s+is\s+english|work\s+language\s+is\s+english|company\s+language\s+is\s+english|"
    r"english\s+is\s+our\s+working\s+language|english\s+only|danish\s+is\s+not\s+required|no\s+danish\s+required|"
    r"international\s+environment|international\s+team|english\s+speaking|english-speaking|"
    r"fluent\s+(?:in\s+)?english|fluent\s+english|english\s+required|professional\s+english|"
    r"english\s+proficiency|good\s+english\s+skills|engelsk\s+på\s+forhandlingsniveau|"
    r"taler\s+og\s+skriver\s+engelsk|flydende\s+engelsk|engelsk\s+i\s+skrift\s+og\s+tale|gode\s+engelskkundskaber)\b",
    re.IGNORECASE
)

# Patterns explicitly asserting English-only / Danish not required
ENGLISH_EXCLUSIVE_PATTERNS = re.compile(
    r"\b(corporate\s+language\s+is\s+english|corporate\s+working\s+language\s+is\s+english|"
    r"working\s+language\s+is\s+english|work\s+language\s+is\s+english|company\s+language\s+is\s+english|"
    r"english\s+is\s+our\s+working\s+language|english\s+only|kun\s+engelsk|"
    r"danish\s+is\s+not\s+required|no\s+danish\s+required|dansk\s+er\s+ikke\s+et\s+krav|"
    r"intet\s+krav\s+om\s+dansk|dansk\s+ikke\s+påkrævet)\b",
    re.IGNORECASE
)

# Patterns asserting both languages
BOTH_LANGUAGES_PATTERNS = re.compile(
    r"\b(både\s+dansk\s+og\s+engelsk|dansk\s+og\s+engelsk|english\s+and\s+danish|danish\s+and\s+english|"
    r"both\s+danish\s+and\s+english|both\s+english\s+and\s+danish|danish\s*(&|\+)\s*english|"
    r"english\s*(&|\+)\s*danish|dansk\s*(&|\+)\s*engelsk|både\s+på\s+dansk\s+og\s+engelsk|"
    r"dansk\s+såvel\s+som\s+engelsk|flydende\s+i\s+både\s+dansk\s+og\s+engelsk|"
    r"taler\s+både\s+dansk\s+og\s+engelsk|flydende\s+dansk\s+og\s+engelsk)\b",
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


def detect_language_requirement(text: str, explicit_requirement: Optional[str] = None) -> str:
    """
    Detect language requirement for Danish IT market job postings.
    Returns strictly one of: 'English', 'Danish', 'Both', or 'Unknown'.

    Evaluation Pipeline:
    1. Check explicit requirement parameter if provided and recognizable.
    2. Check for explicit English-exclusive / Danish-not-required clauses.
    3. Check for bilingual requirement patterns ('Both').
    4. Check for Danish requirement vs English requirement cues:
       - If both Danish and English cues are present -> 'Both'.
       - If only Danish is required (and not negated) -> 'Danish'.
       - If only English is required / international -> 'English'.
       - If no linguistic clauses are stated -> 'Unknown'.
    """
    # 1. Explicit requirement string check
    if explicit_requirement:
        norm_exp = explicit_requirement.strip().lower()
        if re.search(r"^(unspecified|not\s+stated|unknown|none|ikke\s+angivet)(\s*[/,].*)?$", norm_exp):
            pass
        else:
            has_exp_both = bool(re.search(r"\b(both|både|danish\s+and\s+english|english\s+and\s+danish|danish\s*(&|\+)\s*english|english\s*(&|\+)\s*danish|bilingual)\b", norm_exp))
            has_exp_danish = bool(re.search(r"\b(danish|dansk)\b", norm_exp)) and not bool(re.search(r"\b(not\s+required|ikke\s+et\s+krav|no\s+danish)\b", norm_exp))
            has_exp_english = bool(re.search(r"\b(english|engelsk)\b", norm_exp))
            has_exp_english_exclusive = bool(re.search(r"\b(english\s+only|kun\s+engelsk|danish\s+is\s+not\s+required|no\s+danish\s+required|dansk\s+er\s+ikke\s+et\s+krav|intet\s+krav\s+om\s+dansk)\b", norm_exp))

            if has_exp_english_exclusive:
                return "English"
            if has_exp_both or (has_exp_danish and has_exp_english):
                return "Both"
            if has_exp_danish:
                return "Danish"
            if has_exp_english:
                return "English"

    # 2. Text inspection on combined text (title, description, and any requirements text)
    combined_text = f"{text} {explicit_requirement or ''}".lower()

    has_danish_negation = bool(DANISH_NEGATION_PATTERNS.search(combined_text))
    has_english_exclusive = bool(ENGLISH_EXCLUSIVE_PATTERNS.search(combined_text))
    has_both_cue = bool(BOTH_LANGUAGES_PATTERNS.search(combined_text))
    has_danish_cue = bool(DANISH_REQUIRED_PATTERNS.search(combined_text)) and not has_danish_negation
    has_english_cue = bool(ENGLISH_FRIENDLY_PATTERNS.search(combined_text))

    if has_english_exclusive:
        return "English"
    if has_both_cue or (has_danish_cue and has_english_cue):
        return "Both"
    if has_danish_cue:
        return "Danish"
    if has_english_cue:
        return "English"
    return "Unknown"


class DataTransformer:
    def __init__(self, skill_extractor: SkillExtractor):
        self.skill_extractor = skill_extractor

    def transform_record(self, raw_job: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich cleaned job dictionary with derived analytical dimensions."""
        title = raw_job.get("title", "")
        desc = raw_job.get("description", "")

        # 1. Skill Extraction
        combined_text = f"{title} {desc} {raw_job.get('language_requirements', '')}".lower()
        explicit_skills = raw_job.get("technologies") or raw_job.get("skills") or []
        extracted = self.skill_extractor.extract_skills(combined_text, explicit_skills)
        skill_names = [s["name"] for s in extracted]

        # 2. Language Requirement Classification (English, Danish, Both, or Unknown)
        explicit_lang = raw_job.get("language_requirements") or raw_job.get("language_requirement")
        language_requirement = detect_language_requirement(
            text=f"{title} {desc}",
            explicit_requirement=explicit_lang
        )

        is_danish_required = language_requirement in ("Danish", "Both")
        is_english_only = language_requirement == "English"

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
            "language_requirement": language_requirement,
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
