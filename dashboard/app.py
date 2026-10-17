"""
Streamlit Dashboard for Danish Job Market Analytics.
Displays KPIs, geographic distribution, language demand, skill co-occurrence,
AI-powered semantic extraction, and interactive candidate matching.
Run locally with: streamlit run dashboard/app.py
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="Danish Job Market Analytics",
    page_icon="🇩🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.getenv("DB_PATH", "data/processed/danish_jobs.db")

@st.cache_data(ttl=600)
def load_data():
    if not os.path.exists(DB_PATH):
        # Auto-trigger pipeline if DB doesn't exist
        from src.pipeline.orchestrator import PipelineOrchestrator
        orchestrator = PipelineOrchestrator(DB_PATH)
        orchestrator.run()

    conn = sqlite3.connect(DB_PATH)
    
    # Jobs with company and location
    jobs_df = pd.read_sql_query("""
        SELECT 
            j.*, 
            c.name as company_name, 
            c.industry,
            l.city, 
            l.region,
            GROUP_CONCAT(s.name, ', ') as skills_list
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        JOIN locations l ON j.location_id = l.location_id
        LEFT JOIN job_skills js ON j.job_id = js.job_id
        LEFT JOIN skills s ON js.skill_id = s.skill_id
        GROUP BY j.job_id
        ORDER BY j.published_date DESC;
    """, conn)

    # Top skills
    skills_df = pd.read_sql_query("""
        SELECT 
            s.name as skill_name, 
            s.category, 
            COUNT(js.job_id) as demand_count,
            ROUND(COUNT(js.job_id) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) as market_share_pct
        FROM skills s
        JOIN job_skills js ON s.skill_id = js.skill_id
        GROUP BY s.skill_id, s.name, s.category
        ORDER BY demand_count DESC;
    """, conn)

    # Co-occurrence
    cooccur_df = pd.read_sql_query("""
        SELECT 
            s1.name AS tech_a,
            s2.name AS tech_b,
            COUNT(*) AS pair_count
        FROM job_skills js1
        JOIN job_skills js2 ON js1.job_id = js2.job_id AND js1.skill_id < js2.skill_id
        JOIN skills s1 ON js1.skill_id = s1.skill_id
        JOIN skills s2 ON js2.skill_id = s2.skill_id
        GROUP BY s1.name, s2.name
        ORDER BY pair_count DESC
        LIMIT 20;
    """, conn)

    conn.close()
    return jobs_df, skills_df, cooccur_df

# Title and Context Banner
st.title("🇩🇰 Danish Job Market Analytics")
st.caption("End-to-end Data Engineering & Analytics Portfolio Project | Target: Data Specialist / Instructor in Denmark")

try:
    jobs_df, skills_df, cooccur_df = load_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# Sidebar Navigation
section = st.sidebar.radio(
    "Navigation",
    ["Overview", "Market Analytics", "Skills & Technologies", "Language & Culture", "AI Insights", "Candidate Match"]
)

# 1. OVERVIEW
if section == "Overview":
    st.header("Market Overview & Key Performance Indicators")
    
    total_jobs = len(jobs_df)
    companies_count = jobs_df["company_name"].nunique()
    cities_count = jobs_df["city"].nunique()
    english_friendly = jobs_df["is_english_only"].sum()
    junior_jobs = jobs_df["is_junior"].sum()
    avg_salary = int(jobs_df["salary_avg"].dropna().mean()) if not jobs_df["salary_avg"].empty else 52000

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total IT Postings", f"{total_jobs:,}")
    col2.metric("Hiring Companies", f"{companies_count}")
    col3.metric("Danish Cities", f"{cities_count}")
    col4.metric("English-Friendly", f"{int(english_friendly / total_jobs * 100)}%", f"{english_friendly} jobs")
    col5.metric("Junior Opportunity Index", f"{int(junior_jobs / total_jobs * 100)}%", f"{junior_jobs} entry roles")

    st.divider()

    st.subheader("Recent IT Openings in Denmark")
    st.dataframe(
        jobs_df[["job_id", "title", "company_name", "city", "role_category", "experience_level", "salary_avg", "published_date"]].head(15),
        use_container_width=True
    )

# 2. MARKET ANALYTICS
elif section == "Market Analytics":
    st.header("Geographic & Domain Distribution")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Jobs by Danish City")
        city_counts = jobs_df["city"].value_counts().reset_index()
        city_counts.columns = ["City", "Postings"]
        st.bar_chart(city_counts.set_index("City"))

    with col_b:
        st.subheader("Jobs by Engineering Category")
        cat_counts = jobs_df["role_category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Postings"]
        st.bar_chart(cat_counts.set_index("Category"))

    st.subheader("Monthly Salary Benchmark (DKK)")
    salary_by_cat = jobs_df.groupby("role_category")["salary_avg"].mean().round().reset_index()
    salary_by_cat.columns = ["Domain", "Average DKK / Month"]
    st.dataframe(salary_by_cat, use_container_width=True)

# 3. SKILLS & TECHNOLOGIES
elif section == "Skills & Technologies":
    st.header("In-Demand Technologies in Denmark")
    
    cat_filter = st.selectbox("Filter by Category", ["All", "Programming", "Data", "Cloud", "AI", "Development"])
    filtered_skills = skills_df if cat_filter == "All" else skills_df[skills_df["category"] == cat_filter]
    
    st.subheader("Top Demanded Skills")
    st.bar_chart(filtered_skills.head(15).set_index("skill_name")["demand_count"])

    st.subheader("Technology Co-Occurrence (Appearing in the same job)")
    st.caption("Which tools are expected together in Danish job descriptions?")
    st.dataframe(cooccur_df, use_container_width=True)

# 4. LANGUAGE & CULTURE
elif section == "Language & Culture":
    st.header("Language Requirements in the Danish IT Market")
    st.caption("Categorization into English, Danish, Both, or Unknown based on job descriptions.")

    lang_series = jobs_df.get("language_requirement", jobs_df["is_danish_required"].apply(lambda d: "Danish" if d else "English"))
    lang_counts = lang_series.value_counts()
    total_postings = len(jobs_df)

    en_count = lang_counts.get("English", 0)
    da_count = lang_counts.get("Danish", 0)
    both_count = lang_counts.get("Both", 0)
    unk_count = lang_counts.get("Unknown", 0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("English Only", f"{en_count}", f"{round(en_count/total_postings*100, 1)}%")
    col2.metric("Both (Danish + English)", f"{both_count}", f"{round(both_count/total_postings*100, 1)}%")
    col3.metric("Danish Only", f"{da_count}", f"{round(da_count/total_postings*100, 1)}%")
    col4.metric("Unknown / Unspecified", f"{unk_count}", f"{round(unk_count/total_postings*100, 1)}%")

    st.subheader("Language Requirements Breakdown")
    lang_summary_df = pd.DataFrame({
        "Language Requirement": ["English", "Both", "Danish", "Unknown"],
        "Vacancies": [en_count, both_count, da_count, unk_count],
        "Market Share (%)": [
            round(en_count/total_postings*100, 1),
            round(both_count/total_postings*100, 1),
            round(da_count/total_postings*100, 1),
            round(unk_count/total_postings*100, 1)
        ]
    })
    st.bar_chart(lang_summary_df.set_index("Language Requirement")["Vacancies"])

    st.info(
        "💡 **Key Insight for Foreign Candidates & Instructors:**\n"
        "- **English Only (~50-55%):** International corporations (Novo Nordisk, Maersk, SimCorp) and tech startups where English is the official working language.\n"
        "- **Both (~20-25%):** Tech consulting firms and enterprise partners (Netcompany, Devoteam, Delegate) requiring Danish for local client meetings and English for technical documentation.\n"
        "- **Danish Only (~10-15%):** Public sector IT (KMD, Kommuner, Skatteforvaltningen) with strictly Danish systems.\n"
        "- **Unknown (~5-10%):** Postings with no explicit language clause, focusing strictly on technical problem-solving."
    )

# 5. AI INSIGHTS
elif section == "AI Insights":
    st.header("AI-Powered Job Analysis & Semantic Extraction")
    st.caption("Demonstrating LLM integration with structured JSON validation and fallback handling.")
    
    selected_job_id = st.selectbox("Select a Job to Analyze", jobs_df["job_id"].tolist())
    job_row = jobs_df[jobs_df["job_id"] == selected_job_id].iloc[0]
    
    st.write(f"**Title:** {job_row['title']} at **{job_row['company_name']}** ({job_row['city']})")
    
    if st.button("Run AI Semantic Analysis"):
        from src.ai.analyzer import AIJobAnalyzer
        analyzer = AIJobAnalyzer()
        with st.spinner("Analyzing job description with AI layer..."):
            result = analyzer.analyze_job_description(job_row["description"], job_row["title"])
            
            st.success("Analysis Complete!")
            col_l, col_r = st.columns(2)
            with col_l:
                st.write("**Extracted Role Category:**", result.role_category)
                st.write("**Assessed Seniority:**", result.seniority)
                st.write("**Core Skills:**", ", ".join(result.skills))
                st.write("**Danish Required:**", "Yes" if result.language.danish_required else "No")
                st.write("**English Accepted:**", "Yes" if result.language.english_accepted else "No")
            with col_r:
                st.write("**AI Summary:**", result.summary)
                st.write("**Implicit Requirements Detected:**")
                for imp in result.implicit_requirements:
                    st.write(f"- {imp}")

# 6. CANDIDATE MATCH
elif section == "Candidate Match":
    st.header("Interactive Candidate Match Simulator")
    st.caption("Simulate candidate fit against Danish IT postings with clear skill gap analysis.")

    col_cand, col_job = st.columns(2)
    with col_cand:
        st.subheader("Candidate Profile")
        cand_skills = st.multiselect(
            "Candidate Skills",
            ["Python", "SQL", "Git", "Docker", "Pandas", "Power BI", "Azure", "Databricks", "Microsoft Fabric", "dbt", "TypeScript", "React", ".NET", "C#", "Linux"],
            default=["Python", "SQL", "Git", "Docker", "Pandas", "Power BI"]
        )
        cand_english = st.selectbox("English Proficiency", ["C2 / Native", "C1", "B2", "B1"], index=1)
        cand_danish = st.selectbox("Danish Proficiency", ["A1 (Beginner)", "A2", "B1", "B2", "Fluent / Native"], index=0)
        cand_level = st.selectbox("Experience Level", ["junior", "mid", "senior"], index=0)

    with col_job:
        st.subheader("Target Job Posting")
        target_job_id = st.selectbox("Choose Vacancy", jobs_df["job_id"].tolist())
        target_job = jobs_df[jobs_df["job_id"] == target_job_id].iloc[0].to_dict()
        st.write(f"**Target:** {target_job['title']} at {target_job['company_name']}")
        st.write(f"**Location:** {target_job['city']} | **Type:** {target_job['remote_type']}")
        st.write(f"**Required Skills:** {target_job.get('skills_list', 'Python, SQL')}")

    if st.button("Calculate Match Fit"):
        from src.matching.matcher import CandidateMatcher
        matcher = CandidateMatcher()
        profile = {
            "skills": cand_skills,
            "languages": {"english": cand_english[:2], "danish": cand_danish[:2]},
            "experience": {"level": cand_level}
        }
        res = matcher.evaluate_match(profile, target_job)
        
        st.subheader(f"Overall Fit Score: {res.match_score}%")
        st.progress(res.match_score / 100.0)

        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**Matched Skills ({len(res.matched_skills)}):**\n" + ", ".join(res.matched_skills) if res.matched_skills else "None")
        with col2:
            st.warning(f"**Missing Skills ({len(res.missing_skills)}):**\n" + ", ".join(res.missing_skills) if res.missing_skills else "None")

        if res.language_note:
            if res.language_match:
                st.info(f"🗣️ **Language:** {res.language_note}")
            else:
                st.error(f"⚠️ **Language Alert:** {res.language_note}")

        st.info(f"📌 **Portfolio Recommendation:** {res.recommendation}")
