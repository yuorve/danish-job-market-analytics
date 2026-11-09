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
- role_category (Multi-signal weighted classifier: title > context > specific skills)
"""

import re
from typing import Any, Dict, List, Optional, Tuple
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

# =========================================================================
# Multi-Signal Role Categorization Patterns
# High precision: Title (10 pts) > Description Context (4 pts) > Specific Tools
# =========================================================================

# 1. Title Patterns
TITLE_DATA_ENG = re.compile(
    r"\b(data\s+engineer(?:ing)?|etl\s+(?:developer|engineer)|data\s+platform\s+engineer|"
    r"lakehouse\s+engineer|analytics\s+engineer|big\s+data\s+engineer|database\s+engineer|"
    r"data\s+infrastructure|data\s+specialist|data\s+warehouse\s+developer)\b",
    re.IGNORECASE
)

TITLE_AI_ML = re.compile(
    r"\b(machine\s+learning|ml\s+engineer|ai\s+engineer|data\s+scientist|deep\s+learning|"
    r"nlp\s+engineer|computer\s+vision|ai\s+researcher|generative\s+ai\s+engineer|prompt\s+engineer)\b",
    re.IGNORECASE
)

TITLE_CLOUD_DEVOPS = re.compile(
    r"\b(devops|platform\s+engineer|sre|site\s+reliability|cloud\s+architect|cloud\s+engineer|"
    r"infrastructure\s+engineer|kubernetes\s+engineer|cloud\s+specialist|sysadmin|systems\s+engineer)\b",
    re.IGNORECASE
)

TITLE_BI_ANALYTICS = re.compile(
    r"\b(bi\s+developer|business\s+intelligence|power\s+bi\s+developer|tableau\s+developer|"
    r"bi\s+consultant|data\s+analyst|reporting\s+specialist|analytics\s+consultant|insights\s+analyst)\b",
    re.IGNORECASE
)

TITLE_SOFTWARE_DEV = re.compile(
    r"\b(software\s+engineer|software\s+developer|full\s*stack|backend|frontend|web\s+developer|"
    r"python\s+developer|c#\s+developer|\.net\s+developer|java\s+developer|application\s+developer|"
    r"system\s+developer|systemudvikler|softwareudvikler|c\+\+\s+developer|go\s+developer|"
    r"rust\s+developer|mobile\s+developer|ios\s+developer|android\s+developer)\b",
    re.IGNORECASE
)

# 2. Description Context Patterns
CONTEXT_DATA_ENG = re.compile(
    r"\b(data\s+pipelines?|lakehouse|etl\s+pipeline|data\s+warehouse|data\s+mesh|delta\s+lake|"
    r"batch\s+processing|stream\s+processing|dbt\s+models|spark\s+jobs|data\s+ingestion)\b",
    re.IGNORECASE
)

CONTEXT_AI_ML = re.compile(
    r"\b(train(?:ing)?\s+models|neural\s+networks?|large\s+language\s+models?|prompt\s+engineering|"
    r"retrieval\s+augmented|generative\s+ai|model\s+evaluation|fine-tuning|hugging\s*face|embeddings)\b",
    re.IGNORECASE
)

CONTEXT_CLOUD_DEVOPS = re.compile(
    r"\b(ci/cd|infrastructure\s+as\s+code|container\s+orchestration|helm\s+charts?|"
    r"cloud\s+infrastructure|terraform\s+modules|monitoring\s+and\s+alerting|gitops)\b",
    re.IGNORECASE
)

CONTEXT_BI_ANALYTICS = re.compile(
    r"\b(dashboards?|business\s+reporting|data\s+visualization|kpis?|executive\s+reports?|"
    r"dax\s+queries|tabular\s+models?|power\s+bi\s+reports?|stakeholder\s+reporting)\b",
    re.IGNORECASE
)

CONTEXT_SOFTWARE_DEV = re.compile(
    r"\b(microservices|rest\s+apis?|frontend\s+architecture|backend\s+services|clean\s+code|"
    r"software\s+architecture|user\s+interfaces?|web\s+applications?|unit\s+testing|object-oriented)\b",
    re.IGNORECASE
)


def detect_language_requirement(text: str, explicit_requirement: Optional[str] = None) -> str:
    """
    Detect language requirement for Danish IT market job postings.
    Returns strictly one of: 'English', 'Danish', 'Both', or 'Unknown'.
    """
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


def classify_role_domain(title: str, description: str, skill_names: List[str]) -> Tuple[str, Dict[str, bool]]:
    """
    Weighted multi-signal role classifier.
    Avoids bias where ubiquitous technologies (like SQL) erroneously misclassify software
    developers, backend engineers, or BI analysts as Data Engineers.

    Weighting:
    - Title Signals: 10 points (dominant indicator)
    - Description Context Signals: 4 points
    - Specialized Technologies: 2-3 points
    - Shared Technologies (e.g. SQL, Git): 1 point evenly distributed across relevant fields
    """
    title_clean = title.strip()
    desc_clean = description.strip()

    scores = {
        "Data Engineering": 0.0,
        "AI & Machine Learning": 0.0,
        "Cloud & DevOps": 0.0,
        "BI & Analytics": 0.0,
        "Software Development": 0.0
    }

    # 1. Title Signals (10 points)
    if TITLE_DATA_ENG.search(title_clean):
        scores["Data Engineering"] += 10.0
    if TITLE_AI_ML.search(title_clean):
        scores["AI & Machine Learning"] += 10.0
    if TITLE_CLOUD_DEVOPS.search(title_clean):
        scores["Cloud & DevOps"] += 10.0
    if TITLE_BI_ANALYTICS.search(title_clean):
        scores["BI & Analytics"] += 10.0
    if TITLE_SOFTWARE_DEV.search(title_clean):
        scores["Software Development"] += 10.0

    # 2. Description Context Signals (4 points)
    if CONTEXT_DATA_ENG.search(desc_clean):
        scores["Data Engineering"] += 4.0
    if CONTEXT_AI_ML.search(desc_clean):
        scores["AI & Machine Learning"] += 4.0
    if CONTEXT_CLOUD_DEVOPS.search(desc_clean):
        scores["Cloud & DevOps"] += 4.0
    if CONTEXT_BI_ANALYTICS.search(desc_clean):
        scores["BI & Analytics"] += 4.0
    if CONTEXT_SOFTWARE_DEV.search(desc_clean):
        scores["Software Development"] += 4.0

    # 3. Technology Signals
    skills_set = set(skill_names)

    # Specialized Data Engineering tech
    for sk in ["Databricks", "Microsoft Fabric", "dbt", "Apache Spark", "Airflow", "Snowflake"]:
        if sk in skills_set:
            scores["Data Engineering"] += 3.0

    # Specialized AI tech
    for sk in ["Machine Learning", "Deep Learning", "LLM", "Generative AI", "PyTorch", "RAG", "Computer Vision", "NLP"]:
        if sk in skills_set:
            scores["AI & Machine Learning"] += 3.0

    # Specialized Cloud & DevOps tech
    for sk in ["Kubernetes", "Terraform", "CI/CD"]:
        if sk in skills_set:
            scores["Cloud & DevOps"] += 3.0

    # Specialized BI tech
    for sk in ["Power BI", "Tableau", "DAX"]:
        if sk in skills_set:
            scores["BI & Analytics"] += 3.0

    # Specialized Software Development tech
    for sk in ["React", "TypeScript", "Node.js", ".NET", "C#", "Java", "Go", "Rust", "FastAPI", "Django", "Spring"]:
        if sk in skills_set:
            scores["Software Development"] += 2.0

    # Generic & Shared Technologies:
    # SQL is ubiquitous: provides balanced foundation, NEVER biases Data Engineering alone!
    if "SQL" in skills_set:
        scores["Data Engineering"] += 1.0
        scores["BI & Analytics"] += 1.0
        scores["Software Development"] += 1.0

    if "Pandas" in skills_set:
        scores["Data Engineering"] += 1.0
        scores["AI & Machine Learning"] += 1.0

    # Cloud platforms: shared across Cloud and modern cloud-native data lakehouses
    for cloud in ["Azure", "AWS", "GCP"]:
        if cloud in skills_set:
            scores["Cloud & DevOps"] += 1.0
            scores["Data Engineering"] += 1.0

    if "Docker" in skills_set:
        scores["Cloud & DevOps"] += 1.5
        scores["Software Development"] += 1.0

    # 4. Resolve Category Winner
    max_score = max(scores.values())
    if max_score > 0:
        # Pick category with highest score
        role_category = max(scores, key=scores.get)
    else:
        role_category = "Software Development"

    # Compute boolean role flags
    is_data = (scores["Data Engineering"] >= 4.0) or bool(TITLE_DATA_ENG.search(title_clean))
    is_ai = (scores["AI & Machine Learning"] >= 4.0) or bool(TITLE_AI_ML.search(title_clean))
    is_devops = (scores["Cloud & DevOps"] >= 4.0) or bool(TITLE_CLOUD_DEVOPS.search(title_clean))
    is_cloud = (
        is_devops or
        any(s in skills_set for s in ["Azure", "AWS", "GCP", "Kubernetes", "Terraform", "Docker"])
    )

    flags = {
        "is_data_role": is_data,
        "is_ai_role": is_ai,
        "is_devops_role": is_devops,
        "is_cloud_role": is_cloud
    }

    return role_category, flags


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

        # 4. Multi-Signal Role Categorization
        role_category, flags = classify_role_domain(
            title=title,
            description=desc,
            skill_names=skill_names
        )

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
            "is_data_role": flags["is_data_role"],
            "is_ai_role": flags["is_ai_role"],
            "is_devops_role": flags["is_devops_role"],
            "is_cloud_role": flags["is_cloud_role"],
            "experience_level": exp_level,
            "salary_avg": sal_avg
        }
