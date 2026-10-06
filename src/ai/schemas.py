"""
Data schemas and validation contracts for the AI analysis layer.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class LanguageAssessment:
    danish_required: bool
    english_accepted: bool

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
                "english_accepted": self.language.english_accepted
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
    lang = LanguageAssessment(
        danish_required=bool(lang_raw.get("danish_required", False)),
        english_accepted=bool(lang_raw.get("english_accepted", True))
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
