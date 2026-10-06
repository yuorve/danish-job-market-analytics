-- Danish Job Market Analytics - Normalized Relational Schema
-- Designed for SQLite / PostgreSQL compatibility

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT,
    is_synthetic BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    normalized_name TEXT NOT NULL,
    industry TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT UNIQUE NOT NULL,
    region TEXT NOT NULL,
    country TEXT DEFAULT 'Denmark'
);

CREATE TABLE IF NOT EXISTS skills (
    skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    company_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    normalized_title TEXT NOT NULL,
    role_category TEXT NOT NULL,
    description TEXT,
    remote_type TEXT,
    employment_type TEXT DEFAULT 'Full-time',
    published_date TEXT NOT NULL,
    salary_min REAL,
    salary_max REAL,
    salary_avg REAL,
    currency TEXT DEFAULT 'DKK',
    url TEXT,
    language_requirements TEXT,
    is_danish_required BOOLEAN DEFAULT 0,
    is_english_only BOOLEAN DEFAULT 0,
    is_remote BOOLEAN DEFAULT 0,
    is_hybrid BOOLEAN DEFAULT 0,
    is_junior BOOLEAN DEFAULT 0,
    is_data_role BOOLEAN DEFAULT 0,
    is_ai_role BOOLEAN DEFAULT 0,
    is_devops_role BOOLEAN DEFAULT 0,
    is_cloud_role BOOLEAN DEFAULT 0,
    experience_level TEXT,
    education_requirements TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES sources(source_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id)
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id TEXT NOT NULL,
    skill_id INTEGER NOT NULL,
    PRIMARY KEY (job_id, skill_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_published ON jobs(published_date);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location_id);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(role_category);
CREATE INDEX IF NOT EXISTS idx_jobs_seniority ON jobs(experience_level);
CREATE INDEX IF NOT EXISTS idx_job_skills_skill ON job_skills(skill_id);
