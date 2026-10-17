"""
Analytical Engine for Danish Job Market Analytics.
Computes KPIs, geographic distribution, language demand, salary stats,
technology co-occurrence matrices, and the Junior Opportunity Index.
"""

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional
from src.database.repository import JobRepository

class MarketAnalyzer:
    def __init__(self, repository: JobRepository):
        self.repo = repository

    def compute_overview_kpis(self) -> Dict[str, Any]:
        """High level overview KPIs for dashboard and reports."""
        with self.repo.get_conn() as conn:
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*) FROM jobs")
            total_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(DISTINCT company_id) FROM jobs")
            total_companies = c.fetchone()[0]

            c.execute("SELECT COUNT(DISTINCT location_id) FROM jobs")
            total_cities = c.fetchone()[0]

            c.execute("SELECT COUNT(DISTINCT skill_id) FROM job_skills")
            total_technologies = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE language_requirement = 'English'")
            english_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE language_requirement = 'Danish'")
            danish_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE language_requirement = 'Both'")
            both_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE language_requirement = 'Unknown' OR language_requirement IS NULL")
            unknown_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE is_english_only = 1")
            english_friendly = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE is_danish_required = 1")
            danish_required = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE is_remote = 1")
            remote_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE is_hybrid = 1")
            hybrid_jobs = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM jobs WHERE is_junior = 1")
            junior_jobs = c.fetchone()[0]

            c.execute("SELECT AVG(salary_avg), MIN(salary_min), MAX(salary_max) FROM jobs WHERE salary_avg IS NOT NULL")
            sal_row = c.fetchone()
            avg_salary = round(sal_row[0] or 0)
            min_salary = round(sal_row[1] or 0)
            max_salary = round(sal_row[2] or 0)

        junior_opp_index = round((junior_jobs / total_jobs * 100), 1) if total_jobs else 0
        english_ratio = round((english_jobs / total_jobs * 100), 1) if total_jobs else 0
        danish_ratio = round((danish_jobs / total_jobs * 100), 1) if total_jobs else 0
        both_ratio = round((both_jobs / total_jobs * 100), 1) if total_jobs else 0
        unknown_ratio = round((unknown_jobs / total_jobs * 100), 1) if total_jobs else 0
        remote_ratio = round((remote_jobs / total_jobs * 100), 1) if total_jobs else 0

        return {
            "total_jobs": total_jobs,
            "total_companies": total_companies,
            "total_cities": total_cities,
            "total_technologies": total_technologies,
            "language_counts": {
                "english": english_jobs,
                "danish": danish_jobs,
                "both": both_jobs,
                "unknown": unknown_jobs
            },
            "language_percentages": {
                "english": english_ratio,
                "danish": danish_ratio,
                "both": both_ratio,
                "unknown": unknown_ratio
            },
            "english_friendly_jobs": english_friendly,
            "danish_required_jobs": danish_required,
            "english_friendly_pct": english_ratio,
            "danish_required_pct": round(danish_ratio + both_ratio, 1),
            "remote_jobs": remote_jobs,
            "hybrid_jobs": hybrid_jobs,
            "remote_pct": remote_ratio,
            "junior_jobs": junior_jobs,
            "junior_opportunity_index": junior_opp_index,
            "salary_avg_dkk": avg_salary,
            "salary_min_dkk": min_salary,
            "salary_max_dkk": max_salary
        }

    def get_language_distribution(self) -> List[Dict[str, Any]]:
        """Return breakdown of English, Danish, Both, and Unknown requirements."""
        sql = """
            SELECT 
                COALESCE(language_requirement, 'Unknown') AS requirement,
                COUNT(*) AS count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) AS percentage,
                ROUND(AVG(salary_avg), 0) AS avg_salary
            FROM jobs
            GROUP BY COALESCE(language_requirement, 'Unknown')
            ORDER BY count DESC;
        """
        return self.repo.execute_query(sql)

    def get_jobs_by_city(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                l.city,
                l.region,
                COUNT(j.job_id) as job_count,
                ROUND(AVG(j.salary_avg), 0) as avg_salary,
                SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) as english_friendly_count,
                SUM(CASE WHEN j.is_junior = 1 THEN 1 ELSE 0 END) as junior_count
            FROM locations l
            JOIN jobs j ON l.location_id = j.location_id
            GROUP BY l.city, l.region
            ORDER BY job_count DESC;
        """
        return self.repo.execute_query(sql)

    def get_top_skills(self, limit: int = 20, category: Optional[str] = None) -> List[Dict[str, Any]]:
        filter_clause = "WHERE s.category = ?" if category else ""
        sql = f"""
            SELECT 
                s.name as skill_name,
                s.category,
                COUNT(js.job_id) as demand_count,
                ROUND(COUNT(js.job_id) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) as market_share_pct
            FROM skills s
            JOIN job_skills js ON s.skill_id = js.skill_id
            {filter_clause}
            GROUP BY s.skill_id, s.name, s.category
            ORDER BY demand_count DESC
            LIMIT ?;
        """
        params = [category, limit] if category else [limit]
        with self.repo.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_skill_cooccurrence(self, top_n: int = 15) -> List[Dict[str, Any]]:
        """Calculate pairs of technologies that most frequently appear together."""
        sql = """
            SELECT 
                s1.name AS tech_a,
                s2.name AS tech_b,
                COUNT(*) AS cooccurrence_count
            FROM job_skills js1
            JOIN job_skills js2 ON js1.job_id = js2.job_id AND js1.skill_id < js2.skill_id
            JOIN skills s1 ON js1.skill_id = s1.skill_id
            JOIN skills s2 ON js2.skill_id = s2.skill_id
            GROUP BY s1.name, s2.name
            ORDER BY cooccurrence_count DESC
            LIMIT ?;
        """
        with self.repo.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (top_n,))
            return [dict(r) for r in cur.fetchall()]

    def get_jobs_by_category(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                role_category,
                COUNT(*) as count,
                ROUND(AVG(salary_avg), 0) as avg_salary,
                SUM(CASE WHEN is_junior = 1 THEN 1 ELSE 0 END) as junior_count
            FROM jobs
            GROUP BY role_category
            ORDER BY count DESC;
        """
        return self.repo.execute_query(sql)

    def get_top_companies(self, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
            SELECT 
                c.name as company,
                c.industry,
                COUNT(j.job_id) as open_positions,
                ROUND(AVG(j.salary_avg), 0) as avg_salary,
                SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) as english_friendly_positions
            FROM companies c
            JOIN jobs j ON c.company_id = j.company_id
            GROUP BY c.company_id, c.name, c.industry
            ORDER BY open_positions DESC
            LIMIT ?;
        """
        with self.repo.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (limit,))
            return [dict(r) for r in cur.fetchall()]
