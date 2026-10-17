"""
Repository layer providing data access methods for the Danish Job Market database.
"""

import sqlite3
from typing import Any, Dict, List, Optional
from .connection import get_connection

class JobRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    def upsert_source(self, source_id: str, name: str, base_url: str = "", is_synthetic: bool = False) -> None:
        with self.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sources (source_id, name, base_url, is_synthetic)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name = excluded.name,
                    base_url = excluded.base_url,
                    is_synthetic = excluded.is_synthetic;
                """,
                (source_id, name, base_url, int(is_synthetic))
            )
            conn.commit()

    def get_or_create_company(self, name: str, normalized_name: str, industry: Optional[str] = None) -> int:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT company_id FROM companies WHERE normalized_name = ?", (normalized_name,))
            row = cursor.fetchone()
            if row:
                return row["company_id"]
            cursor.execute(
                "INSERT INTO companies (name, normalized_name, industry) VALUES (?, ?, ?)",
                (name, normalized_name, industry or "Technology")
            )
            conn.commit()
            return cursor.lastrowid

    def get_or_create_location(self, city: str, region: str, country: str = "Denmark") -> int:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT location_id FROM locations WHERE city = ?", (city,))
            row = cursor.fetchone()
            if row:
                return row["location_id"]
            cursor.execute(
                "INSERT INTO locations (city, region, country) VALUES (?, ?, ?)",
                (city, region, country)
            )
            conn.commit()
            return cursor.lastrowid

    def get_or_create_skill(self, name: str, category: str) -> int:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT skill_id FROM skills WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row["skill_id"]
            cursor.execute(
                "INSERT INTO skills (name, category) VALUES (?, ?)",
                (name, category)
            )
            conn.commit()
            return cursor.lastrowid

    def upsert_job(self, job_data: Dict[str, Any]) -> None:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            salary_min = job_data.get("salary_min")
            salary_max = job_data.get("salary_max")
            salary_avg = (salary_min + salary_max) / 2 if (salary_min and salary_max) else None

            cursor.execute(
                """
                INSERT INTO jobs (
                    job_id, source_id, company_id, location_id, title, normalized_title,
                    role_category, description, remote_type, employment_type, published_date,
                    salary_min, salary_max, salary_avg, currency, url, language_requirements,
                    language_requirement,
                    is_danish_required, is_english_only, is_remote, is_hybrid, is_junior,
                    is_data_role, is_ai_role, is_devops_role, is_cloud_role,
                    experience_level, education_requirements
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(job_id) DO UPDATE SET
                    title = excluded.title,
                    normalized_title = excluded.normalized_title,
                    role_category = excluded.role_category,
                    description = excluded.description,
                    remote_type = excluded.remote_type,
                    salary_min = excluded.salary_min,
                    salary_max = excluded.salary_max,
                    salary_avg = excluded.salary_avg,
                    language_requirement = excluded.language_requirement,
                    is_danish_required = excluded.is_danish_required,
                    is_english_only = excluded.is_english_only,
                    is_junior = excluded.is_junior,
                    experience_level = excluded.experience_level;
                """,
                (
                    job_data["job_id"],
                    job_data["source_id"],
                    job_data["company_id"],
                    job_data["location_id"],
                    job_data["title"],
                    job_data["normalized_title"],
                    job_data["role_category"],
                    job_data.get("description", ""),
                    job_data.get("remote_type", "On-site"),
                    job_data.get("employment_type", "Full-time"),
                    job_data["published_date"],
                    salary_min,
                    salary_max,
                    salary_avg,
                    job_data.get("currency", "DKK"),
                    job_data.get("url", ""),
                    job_data.get("language_requirements", ""),
                    job_data.get("language_requirement", "Unknown"),
                    int(bool(job_data.get("is_danish_required", False))),
                    int(bool(job_data.get("is_english_only", False))),
                    int(bool(job_data.get("is_remote", False))),
                    int(bool(job_data.get("is_hybrid", False))),
                    int(bool(job_data.get("is_junior", False))),
                    int(bool(job_data.get("is_data_role", False))),
                    int(bool(job_data.get("is_ai_role", False))),
                    int(bool(job_data.get("is_devops_role", False))),
                    int(bool(job_data.get("is_cloud_role", False))),
                    job_data.get("experience_level", "Mid"),
                    job_data.get("education_requirements", "")
                )
            )

            # Insert job_skills
            skill_ids = job_data.get("skill_ids", [])
            cursor.execute("DELETE FROM job_skills WHERE job_id = ?", (job_data["job_id"],))
            for s_id in skill_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO job_skills (job_id, skill_id) VALUES (?, ?)",
                    (job_data["job_id"], s_id)
                )
            conn.commit()

    def get_all_jobs(self, limit: int = 100, category: Optional[str] = None, city: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                j.*, 
                c.name AS company_name, 
                c.industry,
                l.city, 
                l.region,
                GROUP_CONCAT(s.name, ', ') AS skills_list
            FROM jobs j
            JOIN companies c ON j.company_id = c.company_id
            JOIN locations l ON j.location_id = l.location_id
            LEFT JOIN job_skills js ON j.job_id = js.job_id
            LEFT JOIN skills s ON js.skill_id = s.skill_id
            WHERE 1=1
        """
        params = []
        if category:
            query += " AND j.role_category = ?"
            params.append(category)
        if city:
            query += " AND l.city = ?"
            params.append(city)
        query += " GROUP BY j.job_id ORDER BY j.published_date DESC LIMIT ?"
        params.append(limit)

        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_query(self, sql_query: str) -> List[Dict[str, Any]]:
        with self.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql_query)
            return [dict(row) for row in cursor.fetchall()]
