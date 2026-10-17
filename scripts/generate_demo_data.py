#!/usr/bin/env python3
"""
Generate realistic synthetic dataset of 520+ Danish IT job postings.
Every job is marked with source = 'synthetic_demo'.
Reflects realistic Danish tech ecosystem:
- Locations: Copenhagen, Hillerød, Aarhus, Odense, Aalborg, Roskilde, Lyngby, Ballerup.
- Real employer archetypes in Denmark (Novo Nordisk, Maersk, Netcompany, LEGO, Ørsted, etc.)
- Danish salary benchmarks (DKK per month).
- Language realities: ~65% English-friendly/international, ~35% Danish-required.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Fix seed for reproducibility
random.seed(42)

LOCATIONS = [
    {"city": "Copenhagen", "region": "Hovedstaden", "weight": 42},
    {"city": "Aarhus", "region": "Midtjylland", "weight": 20},
    {"city": "Lyngby", "region": "Hovedstaden", "weight": 9},
    {"city": "Ballerup", "region": "Hovedstaden", "weight": 8},
    {"city": "Odense", "region": "Syddanmark", "weight": 7},
    {"city": "Aalborg", "region": "Nordjylland", "weight": 6},
    {"city": "Hillerød", "region": "Hovedstaden", "weight": 5},
    {"city": "Roskilde", "region": "Sjælland", "weight": 3},
]

COMPANIES = [
    {"name": "Novo Nordisk", "industry": "Life Sciences & Pharma", "languages": ["English"], "danish_pct": 0.15},
    {"name": "Netcompany", "industry": "IT Consulting & GovTech", "languages": ["Danish", "English"], "danish_pct": 0.65},
    {"name": "Maersk", "industry": "Global Logistics & Tech", "languages": ["English"], "danish_pct": 0.10},
    {"name": "SimCorp", "industry": "FinTech & Investment Tech", "languages": ["English"], "danish_pct": 0.20},
    {"name": "LEGO Group", "industry": "Consumer Tech & Retail", "languages": ["English"], "danish_pct": 0.15},
    {"name": "Ørsted", "industry": "Renewable Energy & IoT", "languages": ["English"], "danish_pct": 0.25},
    {"name": "Trifork", "industry": "Software & AI Solutions", "languages": ["English", "Danish"], "danish_pct": 0.35},
    {"name": "Danske Bank", "industry": "Banking & FinTech", "languages": ["English", "Danish"], "danish_pct": 0.40},
    {"name": "KMD", "industry": "Public IT Systems", "languages": ["Danish"], "danish_pct": 0.80},
    {"name": "Devoteam Denmark", "industry": "Cloud & Data Consulting", "languages": ["English", "Danish"], "danish_pct": 0.45},
    {"name": "Delegate", "industry": "Microsoft Solutions Partner", "languages": ["Danish", "English"], "danish_pct": 0.50},
    {"name": "Vestas", "industry": "Wind Energy & Industrial IoT", "languages": ["English"], "danish_pct": 0.20},
    {"name": "Milestone Systems", "industry": "Computer Vision & Video Tech", "languages": ["English"], "danish_pct": 0.15},
    {"name": "Unity Technologies", "industry": "Gaming & Real-time 3D", "languages": ["English"], "danish_pct": 0.05},
    {"name": "Nordea Denmark", "industry": "Financial Services", "languages": ["English"], "danish_pct": 0.30},
    {"name": "NNIT", "industry": "Pharma IT Consulting", "languages": ["English", "Danish"], "danish_pct": 0.40},
    {"name": "Danfoss", "industry": "Industrial Automation", "languages": ["English"], "danish_pct": 0.25},
    {"name": "Grundfos", "industry": "Water Tech & Industrial IoT", "languages": ["English"], "danish_pct": 0.25},
    {"name": "Peak Consulting", "industry": "Management & IT Advisory", "languages": ["Danish", "English"], "danish_pct": 0.60},
    {"name": "Sitecore", "industry": "MarTech & Digital Experience", "languages": ["English"], "danish_pct": 0.10},
    {"name": "Demant", "industry": "Hearing Healthcare Tech", "languages": ["English"], "danish_pct": 0.20},
    {"name": "Copenhagen Atomics", "industry": "DeepTech & Simulation", "languages": ["English"], "danish_pct": 0.10},
]

ROLES_CATALOG = [
    {
        "category": "Data Engineering",
        "templates": [
            ("Junior Data Engineer", "Junior", 38000, 46000, ["Python", "SQL", "Azure", "dbt", "Docker", "Git"], "Build modern data pipelines using Python, SQL, and Azure. You will collaborate with senior data engineers to extract, transform, and load analytical data."),
            ("Azure Data Platform Engineer", "Mid", 52000, 68000, ["Python", "SQL", "Azure", "Databricks", "Apache Spark", "Microsoft Fabric", "Terraform"], "Design scalable lakehouse architecture on Azure using Databricks, Apache Spark, and Microsoft Fabric. Build automated Delta Lake pipelines."),
            ("Data Specialist / Instructor", "Junior", 42000, 50000, ["Python", "SQL", "Pandas", "Power BI", "Docker", "Git"], "Join our technical training academy in Denmark. Deliver hands-on data workshops, mentor junior candidates on SQL, Python, and modern data platforms, and assist client consultancies."),
            ("Senior Data Lakehouse Architect", "Senior", 72000, 88000, ["Databricks", "Microsoft Fabric", "Apache Spark", "Delta Lake", "Terraform", "CI/CD", "Kafka"], "Lead enterprise data lakehouse migration on Microsoft Fabric and Databricks. Establish medallion architecture governance and streaming pipelines."),
            ("Data Ops & Analytics Engineer", "Mid", 50000, 64000, ["SQL", "dbt", "Snowflake", "Apache Airflow", "Python", "Docker"], "Transform raw business data into clean marts using dbt, Snowflake, and Apache Airflow orchestration."),
            ("Junior Data Analyst / ETL Developer", "Junior", 37000, 44000, ["SQL", "Pandas", "Python", "Power BI", "PostgreSQL"], "Support our reporting teams by writing clean SQL queries, Python ETL scripts, and building interactive Power BI dashboards."),
        ]
    },
    {
        "category": "AI & Machine Learning",
        "templates": [
            ("Junior AI Specialist", "Junior", 40000, 48000, ["Python", "PyTorch", "Machine Learning", "LLM", "Docker"], "Train and evaluate predictive models and build proof-of-concept GenAI prototypes using Python, PyTorch, and LangChain."),
            ("Machine Learning Engineer", "Mid", 55000, 70000, ["Python", "PyTorch", "Docker", "Kubernetes", "Machine Learning", "Azure OpenAI", "MLflow"], "Deploy machine learning microservices to Kubernetes. Build training pipelines and monitor drift for predictive models."),
            ("LLM & Generative AI Solutions Engineer", "Mid", 58000, 75000, ["Python", "LLM", "Generative AI", "RAG", "LangChain", "OpenAI", "FastAPI"], "Develop production RAG (Retrieval Augmented Generation) architectures with vector search, OpenAI embeddings, and FastAPI services."),
            ("Computer Vision Researcher", "Senior", 70000, 86000, ["Python", "Computer Vision", "Deep Learning", "TensorFlow", "PyTorch", "C++"], "Develop computer vision models for real-time video surveillance and edge processing using PyTorch and C++."),
        ]
    },
    {
        "category": "Cloud & DevOps",
        "templates": [
            ("Junior Cloud Engineer", "Junior", 39000, 46000, ["Azure", "Linux", "Docker", "Bash", "CI/CD", "Git"], "Automate cloud resources on Azure. Maintain Docker containers, configure CI/CD GitHub Actions workflows, and support infrastructure teams."),
            ("DevOps Specialist", "Mid", 54000, 68000, ["Kubernetes", "Docker", "Terraform", "CI/CD", "Azure", "Linux"], "Automate multi-cluster Kubernetes deployments with Terraform and GitOps. Ensure 99.99% availability."),
            ("Cloud Platform Engineer (AWS/Azure)", "Senior", 68000, 85000, ["AWS", "Azure", "Terraform", "Kubernetes", "Linux", "Go"], "Architect resilient multi-cloud foundations across AWS and Azure with Infrastructure-as-Code."),
        ]
    },
    {
        "category": "Software Development",
        "templates": [
            ("Junior Python Developer", "Junior", 38000, 45000, ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"], "Build clean RESTful microservices with Python, FastAPI, and PostgreSQL. Participate in agile code reviews."),
            ("Full Stack .NET & React Developer", "Mid", 52000, 67000, [".NET", "C#", "React", "TypeScript", "SQL", "Azure"], "Develop modern enterprise web solutions using .NET 8 C# on the backend and React/TypeScript on the frontend."),
            ("Senior Backend Engineer (Go / Java)", "Senior", 68000, 84000, ["Go", "Java", "Kubernetes", "Kafka", "PostgreSQL", "Docker"], "Architect high-throughput event-driven microservices handling millions of events daily with Kafka and Go."),
            ("Junior Frontend Developer", "Junior", 36000, 43000, ["React", "TypeScript", "JavaScript", "REST API", "Git"], "Create responsive, accessible user interfaces using React, TypeScript, and modern CSS frameworks."),
        ]
    },
    {
        "category": "BI & Analytics",
        "templates": [
            ("Power BI & Data Consultant", "Mid", 48000, 62000, ["Power BI", "SQL", "Microsoft Fabric", "DAX", "Excel"], "Bridge business requirements and data modeling. Build executive Power BI dashboards integrated with Microsoft Fabric."),
            ("Junior BI Analyst", "Junior", 36000, 43000, ["Power BI", "SQL", "Tableau", "Excel"], "Create operational dashboards, clean ad-hoc tabular datasets, and assist cross-functional stakeholders with weekly KPIs."),
        ]
    }
]

def generate_dataset(num_records=525):
    jobs = []
    base_date = datetime.now() - timedelta(days=90)
    
    # Pre-calculate cumulative weights for location
    loc_weights = [loc["weight"] for loc in LOCATIONS]
    
    for i in range(num_records):
        job_id = f"DK-JOB-{2024000 + i}"
        loc = random.choices(LOCATIONS, weights=loc_weights, k=1)[0]
        comp = random.choice(COMPANIES)
        
        # Pick category & role template
        cat_obj = random.choice(ROLES_CATALOG)
        role_tpl = random.choice(cat_obj["templates"])
        title, seniority, sal_min_base, sal_max_base, primary_skills, desc_base = role_tpl
        
        # Randomize salary slightly around base (+/- 10%)
        jitter = random.uniform(0.93, 1.08)
        salary_min = int((sal_min_base * jitter) // 1000 * 1000)
        salary_max = int((sal_max_base * jitter) // 1000 * 1000)
        
        # Remote policy
        remote_chance = random.random()
        if remote_chance < 0.18:
            remote_type = "Remote"
        elif remote_chance < 0.72:
            remote_type = "Hybrid"
        else:
            remote_type = "On-site"
            
        # Language requirement distribution: English, Both, Danish, Unknown
        lang_roll = random.random()
        if lang_roll < 0.55:
            # English only
            lang_req = "English only / English corporate language"
            lang_desc = "Our corporate working language is English. Danish is not required for this international role."
        elif lang_roll < 0.80:
            # Both Danish and English
            lang_req = "Both Danish and English required"
            lang_desc = "Vi forventer gode danskkundskaber både skriftligt og mundtligt, da en del af kundekontakten foregår på dansk. Professional English proficiency is also required."
        elif lang_roll < 0.92:
            # Danish only
            lang_req = "Danish required (fluent spoken/written)"
            lang_desc = "Flydende dansk på modersmålsniveau er et ufravigeligt krav til denne stilling. Al intern og ekstern dokumentation foregår på dansk."
        else:
            # Unknown / unspecified
            lang_req = "Unspecified / Not stated"
            lang_desc = "We focus on engineering craftsmanship, problem-solving, and clean architectural design."
            
        # Published date
        days_offset = random.randint(0, 89)
        pub_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        # Education requirement
        edu = random.choice([
            "Bachelor's or Master's in Computer Science, Data Science, Software Engineering or equivalent experience",
            "Technical degree (Datamatiker, BSc, or equivalent practical portfolio experience)",
            "Master's in STEM / Information Technology",
            "Open to self-taught candidates and bootcamp graduates with a verified project portfolio"
        ])
        
        # Additional optional skills
        extra_skills_pool = ["Docker", "Git", "Linux", "CI/CD", "FastAPI", "PostgreSQL", "Power BI", "dbt", "REST API", "Pandas"]
        combined_skills = list(set(primary_skills + random.sample(extra_skills_pool, k=random.randint(1, 3))))
        
        # Full realistic job description
        description = f"""
About the role at {comp['name']}:
We are looking for a {title} to join our technology team in {loc['city']}, Denmark ({loc['region']}).
{desc_base}

Key Responsibilities:
- Design, build, and maintain high-performing solutions using {', '.join(primary_skills[:3])}.
- Collaborate closely with colleagues across Denmark in an agile sprint cadence.
- Ensure automated testing, clean documentation, and code review standards.
- Work with cloud platforms and data services to support business goals.

Required & Valued Qualifications:
- Experience or strong academic/portfolio foundation in {', '.join(combined_skills[:4])}.
- Familiarity with modern developer tooling: Git, CI/CD, and containerization.
- Analytical mindset and passion for continuous learning in Danish tech ecosystems.

Language & Culture:
- {lang_desc}
- Work arrangement: {remote_type} ({'Flexible office hub in ' + loc['city'] if remote_type != 'Remote' else 'Anywhere in Denmark'}).
- Education: {edu}.
- Salary benchmark: DKK {salary_min:,} - {salary_max:,} / month + Danish pension scheme (typical 8-10% employer contribution) and health insurance.
        """.strip()

        job = {
            "job_id": job_id,
            "source": "synthetic_demo",
            "title": title,
            "company": comp["name"],
            "description": description,
            "location": loc["city"],
            "region": loc["region"],
            "remote": remote_type,
            "employment_type": "Full-time",
            "published_date": pub_date,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "currency": "DKK",
            "url": f"https://jobindex.dk/synthetic-demo/{job_id.lower()}",
            "language_requirements": lang_req,
            "experience_level": seniority,
            "education_requirements": edu,
            "technologies": combined_skills,
            "skills": combined_skills,
            "industry": comp["industry"]
        }
        jobs.append(job)

    # Add a couple of realistic raw edges to test data cleaning:
    # 1 duplicate job from another mock source
    dup = dict(jobs[0])
    dup["job_id"] = f"DK-JOB-DUP-001"
    dup["source"] = "synthetic_demo"
    dup["title"] = jobs[0]["title"].upper()  # Uppercase title
    dup["company"] = jobs[0]["company"] + " A/S"  # Company with Danish legal suffix
    jobs.append(dup)

    # 1 job with HTML tags in description
    html_job = dict(jobs[10])
    html_job["job_id"] = f"DK-JOB-HTML-002"
    html_job["description"] = f"<p><strong>Stilling:</strong> {jobs[10]['title']}</p><p>{jobs[10]['description']}</p><br/>"
    jobs.append(html_job)

    return jobs

def main():
    demo_dir = Path("data/demo")
    demo_dir.mkdir(parents=True, exist_ok=True)
    out_file = demo_dir / "synthetic_jobs.json"
    
    jobs = generate_dataset(525)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {len(jobs)} realistic Danish IT job postings in {out_file}")

if __name__ == "__main__":
    main()
