"""
Candidate Matching Engine for Danish Job Market Analytics.
Calculates transparent match scores, highlights missing skills, detects Danish language gaps,
and provides tailored learning recommendations for junior developers and data specialists.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class MatchResult:
    job_id: str
    job_title: str
    company: str
    location: str
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    language_match: bool
    language_note: Optional[str]
    experience_match: bool
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_title": self.job_title,
            "company": self.company,
            "location": self.location,
            "match_score": self.match_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "language_match": self.language_match,
            "language_note": self.language_note,
            "experience_match": self.experience_match,
            "recommendation": self.recommendation
        }

class CandidateMatcher:
    def __init__(self):
        pass

    def evaluate_match(self, candidate_profile: Dict[str, Any], job: Dict[str, Any]) -> MatchResult:
        """
        Evaluate match between a candidate profile and a specific job posting.
        candidate_profile structure:
        {
            "skills": ["Python", "SQL", "Git", "Docker", "Linux"],
            "languages": {"english": "B2", "danish": "A1"},
            "experience": {"level": "junior"}
        }
        """
        cand_skills = set(s.lower() for s in candidate_profile.get("skills", []))
        
        # Job skills
        job_skills_raw = job.get("skills") or job.get("skill_names") or []
        if isinstance(job_skills_raw, str):
            job_skills_list = [s.strip() for s in job_skills_raw.split(",") if s.strip()]
        else:
            job_skills_list = [str(s).strip() for s in job_skills_raw if s]

        if not job_skills_list:
            # Fallback if no skills tagged
            job_skills_list = ["Python", "SQL"]

        matched = []
        missing = []
        for js in job_skills_list:
            if js.lower() in cand_skills:
                matched.append(js)
            else:
                missing.append(js)

        # Base technical skill score (weighted 70%)
        tech_ratio = len(matched) / len(job_skills_list) if job_skills_list else 1.0
        tech_score = tech_ratio * 70.0

        # Language alignment (weighted 20%)
        cand_danish = candidate_profile.get("languages", {}).get("danish", "A1").upper()
        cand_english = candidate_profile.get("languages", {}).get("english", "B2").upper()
        
        has_fluent_danish = cand_danish in ["B2", "C1", "C2", "NATIVE", "FLUENT"]
        has_proficient_english = cand_english in ["B2", "C1", "C2", "NATIVE", "FLUENT"]

        job_lang = job.get("language_requirement")
        if not job_lang:
            if bool(job.get("is_danish_required", False)):
                job_lang = "Both" if bool(job.get("is_english_only", False)) else "Danish"
            elif bool(job.get("is_english_only", False)):
                job_lang = "English"
            else:
                job_lang = "Unknown"

        if job_lang == "Danish":
            if has_fluent_danish:
                lang_score = 20.0
                language_match = True
                language_note = "Position requires Danish fluency. Candidate profile satisfies requirement."
            else:
                lang_score = 5.0
                language_match = False
                language_note = f"Position requires Danish fluency. Candidate profile indicates {cand_danish} (B2+ recommended)."
        elif job_lang == "Both":
            if has_fluent_danish and has_proficient_english:
                lang_score = 20.0
                language_match = True
                language_note = "Position requires both Danish and English. Candidate profile satisfies both."
            elif has_proficient_english:
                lang_score = 10.0
                language_match = False
                language_note = f"Position requires both Danish and English. English is satisfied, but Danish is {cand_danish} (B2+ recommended)."
            else:
                lang_score = 5.0
                language_match = False
                language_note = "Position requires both fluent Danish and professional English proficiency."
        elif job_lang == "English":
            if has_proficient_english:
                lang_score = 20.0
                language_match = True
                language_note = "Position is English-only / international corporate language. Danish not required."
            else:
                lang_score = 10.0
                language_match = False
                language_note = f"Position requires professional English proficiency. Candidate indicates {cand_english}."
        else:
            # Unknown / Unstated
            lang_score = 16.0
            language_match = True
            language_note = "Language requirement is unstated in the listing. English is typically standard in Danish IT."

        # Seniority alignment (weighted 10%)
        cand_exp = candidate_profile.get("experience", {}).get("level", "junior").lower()
        job_exp = str(job.get("experience_level", "Mid")).lower()
        
        exp_score = 10.0
        if cand_exp == "junior" and "senior" in job_exp:
            exp_score = 3.0
            exp_match = False
        else:
            exp_match = True

        total_score = min(100, max(10, int(round(tech_score + lang_score + exp_score))))

        # Recommendation logic
        if missing:
            top_missing = missing[:3]
            recommendation = (
                f"To strengthen your fit, consider building a portfolio artifact demonstrating {', '.join(top_missing)}."
            )
        else:
            recommendation = "Strong skill match! Ensure your portfolio clearly showcases your hands-on code for these tools."

        return MatchResult(
            job_id=job.get("job_id", "N/A"),
            job_title=job.get("title", "Software Developer"),
            company=job.get("company") or job.get("company_name", "Danish Employer"),
            location=job.get("location") or job.get("city", "Denmark"),
            match_score=total_score,
            matched_skills=matched,
            missing_skills=missing,
            language_match=language_match,
            language_note=language_note,
            experience_match=exp_match,
            recommendation=recommendation
        )
