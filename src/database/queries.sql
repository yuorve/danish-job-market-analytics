-- Danish Job Market Analytics - Analytical SQL Queries
-- Demonstrates SQL competency for Data Specialist / Data Instructor portfolio

-- 1. Top Technologies Demanded Across All Jobs
-- Demonstrates aggregation, joins, and ranking
SELECT 
    s.name AS skill_name,
    s.category,
    COUNT(js.job_id) AS job_count,
    ROUND(COUNT(js.job_id) * 100.0 / (SELECT COUNT(*) FROM jobs), 2) AS market_penetration_pct
FROM skills s
JOIN job_skills js ON s.skill_id = js.skill_id
GROUP BY s.skill_id, s.name, s.category
ORDER BY job_count DESC
LIMIT 15;

-- 2. Jobs Distribution by Danish City & Remote Work Ratio
-- Demonstrates conditional aggregation & grouping
SELECT 
    l.city,
    l.region,
    COUNT(j.job_id) AS total_jobs,
    SUM(CASE WHEN j.is_remote = 1 THEN 1 ELSE 0 END) AS remote_jobs,
    SUM(CASE WHEN j.is_hybrid = 1 THEN 1 ELSE 0 END) AS hybrid_jobs,
    ROUND(SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(j.job_id), 1) AS english_friendly_pct,
    ROUND(AVG(j.salary_avg), 0) AS avg_salary_dkk
FROM locations l
JOIN jobs j ON l.location_id = j.location_id
GROUP BY l.location_id, l.city, l.region
ORDER BY total_jobs DESC;

-- 3. English-Only / International Friendly Opportunities
-- Filters out mandatory Danish requirements
SELECT 
    j.job_id,
    j.title,
    c.name AS company,
    l.city,
    j.experience_level,
    j.salary_avg,
    j.url
FROM jobs j
JOIN companies c ON j.company_id = c.company_id
JOIN locations l ON j.location_id = l.location_id
WHERE j.is_english_only = 1
ORDER BY j.published_date DESC
LIMIT 20;

-- 4. Junior-Friendly Positions (Junior Opportunity Index)
-- Identifies entry points for junior engineers and instructors
SELECT 
    j.job_id,
    j.title,
    c.name AS company,
    l.city,
    j.role_category,
    j.salary_min,
    j.salary_max,
    j.is_english_only,
    GROUP_CONCAT(s.name, ', ') AS required_skills
FROM jobs j
JOIN companies c ON j.company_id = c.company_id
JOIN locations l ON j.location_id = l.location_id
LEFT JOIN job_skills js ON j.job_id = js.job_id
LEFT JOIN skills s ON js.skill_id = s.skill_id
WHERE j.is_junior = 1
GROUP BY j.job_id
ORDER BY j.published_date DESC;

-- 5. Technology Co-Occurrence (Which Technologies Appear Together?)
-- Demonstrates self-joins for market synergy analysis
SELECT 
    s1.name AS technology_a,
    s2.name AS technology_b,
    COUNT(*) AS pair_frequency
FROM job_skills js1
JOIN job_skills js2 ON js1.job_id = js2.job_id AND js1.skill_id < js2.skill_id
JOIN skills s1 ON js1.skill_id = s1.skill_id
JOIN skills s2 ON js2.skill_id = s2.skill_id
GROUP BY s1.name, s2.name
ORDER BY pair_frequency DESC
LIMIT 20;

-- 6. Salary Benchmarks by IT Domain Category
-- Shows financial analytics across engineering domains in Denmark
SELECT 
    role_category,
    COUNT(*) AS postings_count,
    ROUND(MIN(salary_min), 0) AS min_starting_dkk,
    ROUND(AVG(salary_avg), 0) AS avg_monthly_dkk,
    ROUND(MAX(salary_max), 0) AS max_ceiling_dkk
FROM jobs
WHERE salary_avg IS NOT NULL
GROUP BY role_category
ORDER BY avg_monthly_dkk DESC;

-- 7. Top Hiring Employers in the Danish Market
SELECT 
    c.name AS company,
    c.industry,
    COUNT(j.job_id) AS total_openings,
    SUM(CASE WHEN j.is_junior = 1 THEN 1 ELSE 0 END) AS junior_openings,
    ROUND(SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(j.job_id), 1) AS english_pct
FROM companies c
JOIN jobs j ON c.company_id = j.company_id
GROUP BY c.company_id, c.name, c.industry
ORDER BY total_openings DESC
LIMIT 10;

-- 8. 4-Way Language Requirement Breakdown (English, Danish, Both, Unknown)
-- Categorizes vacancies into English, Danish, Both, or Unknown with salary benchmarks
SELECT 
    COALESCE(language_requirement, 'Unknown') AS language_category,
    COUNT(*) AS total_postings,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) AS market_percentage,
    ROUND(AVG(salary_avg), 0) AS avg_monthly_salary_dkk,
    SUM(CASE WHEN is_junior = 1 THEN 1 ELSE 0 END) AS junior_friendly_openings
FROM jobs
GROUP BY COALESCE(language_requirement, 'Unknown')
ORDER BY total_postings DESC;

