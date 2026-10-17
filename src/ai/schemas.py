"""
Data schemas and validation contracts for the AI analysis layer.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class LanguageAssessment:
    danish_required: bool
    english_accepted: bool
    requirement: str = "Unknown"  # "English", "Danish", "Both", or "Unknown"

@dataclass
class JobAnalysisOutput:
    role_category: str
    seniority: str
    skills: List[str]
    language: LanguageAssessment
    implicit_requirements: List[str]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_category": self.role_category,
            "seniority": self.seniority,
            "skills": self.skills,
            "language": {
                "danish_required": self.language.danish_required,
                "english_accepted": self.language.english_accepted,
                "requirement": self.language.requirement
            },
            "implicit_requirements": self.implicit_requirements,
            "summary": self.summary
        }

def validate_ai_response_dict(data: Dict[str, Any]) -> JobAnalysisOutput:
    """Strict validation for LLM JSON output."""
    if not isinstance(data, dict):
        raise ValueError("AI output must be a valid JSON dictionary")

    role_category = str(data.get("role_category", "Data Engineering"))
    seniority = str(data.get("seniority", "Junior"))
    skills = [str(s) for s in data.get("skills", []) if s]
    
    lang_raw = data.get("language", {})
    if not isinstance(lang_raw, dict):
        lang_raw = {}
    danish_req = bool(lang_raw.get("danish_required", False))
    english_acc = bool(lang_raw.get("english_accepted", True))
    
    req_str = str(lang_raw.get("requirement", "")).strip().capitalize()
    if req_str not in ["English", "Danish", "Both", "Unknown"]:
        if danish_req and english_acc:
            req_str = "Both"
        elif danish_req:
            req_str = "Danish"
        elif english_acc:
            req_str = "English"
        else:
            req_str = "Unknown"

    lang = LanguageAssessment(
        danish_required=danish_req,
        english_accepted=english_acc,
        requirement=req_str
    )

    implicit = [str(x) for x in data.get("implicit_requirements", [])]
    summary = str(data.get("summary", "Analysis completed."))

    return JobAnalysisOutput(
        role_category=role_category,
        seniority=seniority,
        skills=skills,
        language=lang,
        implicit_requirements=implicit,
        summary=summary
    )
