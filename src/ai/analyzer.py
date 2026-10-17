"""
AI Layer for extracting subtle implicit nuances, summarizing job postings,
and performing structured classification.
Supports AI_MODE=mock (offline / portfolio verification) and AI_MODE=gemini / openai.
"""

import json
import logging
import os
import re
from typing import Any, Dict, Optional
from .schemas import JobAnalysisOutput, LanguageAssessment, validate_ai_response_dict

logger = logging.getLogger(__name__)

class AIJobAnalyzer:
    def __init__(self, mode: Optional[str] = None):
        self.mode = mode or os.getenv("AI_MODE", "mock").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def analyze_job_description(self, description: str, title: str = "") -> JobAnalysisOutput:
        """
        Analyze job description to produce structured insights.
        Falls back to robust mock heuristic when external APIs are unavailable.
        """
        if self.mode == "gemini" and self.gemini_key:
            try:
                return self._call_gemini_api(description, title)
            except Exception as e:
                logger.warning(f"Gemini API call failed, falling back to mock parser: {e}")
                return self._mock_analysis(description, title)

        return self._mock_analysis(description, title)

    def _mock_analysis(self, description: str, title: str) -> JobAnalysisOutput:
        """
        Deterministic mock analyzer parsing realistic traits.
        Ensures 100% offline reproducibility for portfolio review.
        """
        text = f"{title} {description}".lower()

        # Seniority detection
        if any(w in text for w in ["junior", "graduate", "nyuddannet", "entry level", "student"]):
            seniority = "Junior"
        elif any(w in text for w in ["senior", "lead", "principal", "architect"]):
            seniority = "Senior"
        else:
            seniority = "Mid"

        # Domain classification
        if any(w in text for w in ["spark", "databricks", "fabric", "data engineer", "dbt", "etl"]):
            role_category = "Data Engineering"
        elif any(w in text for w in ["machine learning", "pytorch", "llm", "rag", "computer vision"]):
            role_category = "AI & Machine Learning"
        elif any(w in text for w in ["kubernetes", "terraform", "devops", "cloud platform"]):
            role_category = "Cloud & DevOps"
        elif any(w in text for w in ["power bi", "tableau", "bi analyst", "business intelligence"]):
            role_category = "BI & Analytics"
        else:
            role_category = "Software Development"

        # Language detection: English, Danish, Both, or Unknown
        danish_req = any(w in text for w in ["flydende dansk", "dansk på modersmålsniveau", "taler dansk", "danish required", "gode danskkundskaber"])
        english_cues = any(w in text for w in ["english", "corporate language is english", "english only", "international"])
        english_exclusive = any(w in text for w in ["corporate language is english", "english only", "danish is not required"])

        if english_exclusive:
            lang_req_cat = "English"
            danish_req = False
            english_acc = True
        elif danish_req and english_cues:
            lang_req_cat = "Both"
            english_acc = True
        elif danish_req:
            lang_req_cat = "Danish"
            english_acc = False
        elif english_cues:
            lang_req_cat = "English"
            english_acc = True
        else:
            lang_req_cat = "Unknown"
            english_acc = True

        # Skills detected
        detected_skills = []
        for sk in ["Python", "SQL", "Databricks", "Microsoft Fabric", "Azure", "Docker", "Power BI", "dbt", "FastAPI", "React", ".NET", "Git"]:
            if sk.lower() in text:
                detected_skills.append(sk)
        if not detected_skills:
            detected_skills = ["Python", "SQL"]

        # Implicit requirements
        implicit = []
        if "agile" in text or "scrum" in text:
            implicit.append("Experience with Agile/Scrum ceremonies and team collaboration")
        if "azure" in text or "cloud" in text:
            implicit.append("Familiarity with cloud security and resource governance")
        if "pension" in text or "denmark" in text:
            implicit.append("Understanding of Danish workplace culture and flat hierarchy")
        if not implicit:
            implicit.append("Autonomous problem-solving and eagerness to learn new platforms quickly")

        summary = (
            f"Opportunity for a {seniority} {role_category} professional. "
            f"Focuses on modern tech stack ({', '.join(detected_skills[:3])}) "
            f"with language requirement: {lang_req_cat}."
        )

        raw_dict = {
            "role_category": role_category,
            "seniority": seniority,
            "skills": detected_skills,
            "language": {
                "danish_required": danish_req,
                "english_accepted": english_acc,
                "requirement": lang_req_cat
            },
            "implicit_requirements": implicit,
            "summary": summary
        }
        return validate_ai_response_dict(raw_dict)

    def _call_gemini_api(self, description: str, title: str) -> JobAnalysisOutput:
        """Call Gemini API using standard library urllib request for zero-dependency execution."""
        import urllib.request

        prompt = f"""You are an expert Data & IT recruiter in Denmark. Analyze this job description and output ONLY valid JSON matching this schema:
{{
  "role_category": "Data Engineering | AI & Machine Learning | Cloud & DevOps | Software Development | BI & Analytics",
  "seniority": "Junior | Mid | Senior",
  "skills": ["Skill1", "Skill2"],
  "language": {{
    "danish_required": false,
    "english_accepted": true
  }},
  "implicit_requirements": ["Requirement 1", "Requirement 2"],
  "summary": "Brief 2-sentence summary"
}}

Job Title: {title}
Description:
{description[:1500]}
"""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidate_text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Extract JSON block
            json_match = re.search(r"\{.*\}", candidate_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                return validate_ai_response_dict(parsed)

        raise ValueError("Invalid response format from Gemini API")
