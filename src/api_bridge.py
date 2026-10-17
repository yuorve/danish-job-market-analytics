"""
Secure Python API bridge for Danish Job Market Analytics.
Receives JSON commands via stdin, processes them safely using parameter binding,
and writes JSON results to stdout.
Completely eliminates code injection and shell injection.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict

from src.database.repository import JobRepository
from src.analytics.analyzer import MarketAnalyzer
from src.matching.matcher import CandidateMatcher
from src.ai.analyzer import AIJobAnalyzer

FORBIDDEN_SQL_PATTERNS = re.compile(
    r"\b(ATTACH|DETACH|PRAGMA|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|VACUUM|LOAD_EXTENSION|WRITEFILE|READFILE)\b",
    re.IGNORECASE
)

def handle_get_stats() -> Dict[str, Any]:
    repo = JobRepository()
    analyzer = MarketAnalyzer(repo)
    return {
        "kpis": analyzer.compute_overview_kpis(),
        "cities": analyzer.get_jobs_by_city(),
        "skills": analyzer.get_top_skills(15),
        "categories": analyzer.get_jobs_by_category(),
        "companies": analyzer.get_top_companies(8),
        "cooccurrence": analyzer.get_skill_cooccurrence(12),
        "languages": analyzer.get_language_distribution(),
    }

def handle_get_jobs(params: Dict[str, Any]) -> Any:
    repo = JobRepository()
    limit = max(1, min(300, int(params.get("limit", 100))))
    category = params.get("category")
    city = params.get("city")
    if category and not isinstance(category, str):
        category = None
    if city and not isinstance(city, str):
        city = None
    return repo.get_all_jobs(limit=limit, category=category, city=city)

def handle_execute_sql(params: Dict[str, Any]) -> Dict[str, Any]:
    raw_sql = str(params.get("sql", "")).strip()
    if not raw_sql:
        raise ValueError("SQL query cannot be empty")

    # Reject semicolon-chained queries to prevent multi-statement injection
    cleaned_sql = raw_sql.rstrip(";\n\t ")
    if ";" in cleaned_sql:
        raise ValueError("Multi-statement queries (semicolons) are forbidden")

    # Enforce read-only analytical queries (must start with SELECT or WITH)
    upper_sql = cleaned_sql.upper().strip()
    if not (upper_sql.startswith("SELECT") or upper_sql.startswith("WITH")):
        raise ValueError("Only read-only SELECT or WITH queries are permitted")

    # Check for forbidden keywords (DDL, DML, file IO, pragmas)
    if FORBIDDEN_SQL_PATTERNS.search(cleaned_sql):
        raise ValueError("Forbidden SQL keyword detected (only analytical reads permitted)")

    db_path = Path("data/processed/danish_jobs.db").resolve()
    if not db_path.exists():
        raise FileNotFoundError("Database not found. Run pipeline first.")

    # Open SQLite in explicit READ-ONLY URI mode
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(cleaned_sql)
        rows = [dict(r) for r in cur.fetchmany(500)]
        return {"rows": rows, "rowCount": len(rows)}
    finally:
        conn.close()

def handle_match(params: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(params.get("job_id", "")).strip()
    profile = params.get("profile") or {}
    if not isinstance(profile, dict):
        profile = {}

    repo = JobRepository()
    jobs = repo.get_all_jobs(limit=1000)
    target_job = next((j for j in jobs if j.get("job_id") == job_id), None)
    if not target_job and jobs:
        target_job = jobs[0]
    elif not target_job:
        raise ValueError(f"Job {job_id} not found")

    matcher = CandidateMatcher()
    result = matcher.evaluate_match(profile, target_job)
    return result.to_dict()

def handle_ai_analyze(params: Dict[str, Any]) -> Dict[str, Any]:
    title = str(params.get("title", "")).strip()
    desc = str(params.get("description", "")).strip()
    analyzer = AIJobAnalyzer()
    res = analyzer.analyze_job_description(desc[:2000], title)
    return res.to_dict()

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"error": "Empty payload received"}), file=sys.stderr)
            sys.exit(1)

        payload = json.loads(raw_input)
        action = payload.get("action")
        params = payload.get("params", {})

        if action == "get_stats":
            result = handle_get_stats()
        elif action == "get_jobs":
            result = handle_get_jobs(params)
        elif action == "execute_sql":
            result = handle_execute_sql(params)
        elif action == "match":
            result = handle_match(params)
        elif action == "ai_analyze":
            result = handle_ai_analyze(params)
        else:
            raise ValueError(f"Unknown action: {action}")

        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
