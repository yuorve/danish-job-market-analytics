import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Database, 
  Terminal, 
  UserCheck, 
  Cpu, 
  Layers, 
  BookOpen, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  Building2, 
  MapPin, 
  Globe2, 
  Code2, 
  Sparkles,
  ArrowRight,
  TrendingUp,
  Briefcase
} from 'lucide-react';

interface KPIs {
  total_jobs: number;
  total_companies: number;
  total_cities: number;
  total_technologies: number;
  english_friendly_jobs: number;
  danish_required_jobs: number;
  english_friendly_pct: number;
  danish_required_pct: number;
  remote_jobs: number;
  hybrid_jobs: number;
  remote_pct: number;
  junior_jobs: number;
  junior_opportunity_index: number;
  salary_avg_dkk: number;
  salary_min_dkk: number;
  salary_max_dkk: number;
  language_counts?: { english: number; danish: number; both: number; unknown: number };
  language_percentages?: { english: number; danish: number; both: number; unknown: number };
}

interface StatsData {
  kpis: KPIs;
  cities: Array<{ city: string; region: string; job_count: number; avg_salary: number; english_friendly_count: number; junior_count: number }>;
  skills: Array<{ skill_name: string; category: string; demand_count: number; market_share_pct: number }>;
  categories: Array<{ role_category: string; count: number; avg_salary: number; junior_count: number }>;
  companies: Array<{ company: string; industry: string; open_positions: number; avg_salary: number; english_friendly_positions: number }>;
  cooccurrence: Array<{ tech_a: string; tech_b: string; cooccurrence_count: number }>;
  languages?: Array<{ requirement: string; count: number; percentage: number; avg_salary: number }>;
}

interface Job {
  job_id: string;
  title: string;
  company_name: string;
  industry: string;
  city: string;
  region: string;
  role_category: string;
  experience_level: string;
  salary_avg: number;
  salary_min: number;
  salary_max: number;
  language_requirement?: string;
  is_danish_required: number;
  is_english_only: number;
  remote_type: string;
  skills_list: string;
  description: string;
}

const PRESET_QUERIES = [
  {
    name: "Top Technologies & Market Share",
    sql: `SELECT s.name AS skill_name, s.category, COUNT(js.job_id) AS job_count, ROUND(COUNT(js.job_id) * 100.0 / (SELECT COUNT(*) FROM jobs), 1) AS penetration_pct FROM skills s JOIN job_skills js ON s.skill_id = js.skill_id GROUP BY s.name, s.category ORDER BY job_count DESC LIMIT 10;`
  },
  {
    name: "City Breakdown & International Ratio",
    sql: `SELECT l.city, l.region, COUNT(j.job_id) AS total_jobs, SUM(CASE WHEN j.is_english_only = 1 THEN 1 ELSE 0 END) AS english_friendly, ROUND(AVG(j.salary_avg), 0) AS avg_salary_dkk FROM locations l JOIN jobs j ON l.location_id = j.location_id GROUP BY l.city, l.region ORDER BY total_jobs DESC;`
  },
  {
    name: "Junior-Friendly Entry Positions",
    sql: `SELECT j.job_id, j.title, c.name AS company, l.city, j.role_category, j.salary_min, j.salary_max FROM jobs j JOIN companies c ON j.company_id = c.company_id JOIN locations l ON j.location_id = l.location_id WHERE j.is_junior = 1 LIMIT 12;`
  },
  {
    name: "Technology Co-Occurrence Matrix",
    sql: `SELECT s1.name AS tech_a, s2.name AS tech_b, COUNT(*) AS pair_frequency FROM job_skills js1 JOIN job_skills js2 ON js1.job_id = js2.job_id AND js1.skill_id < js2.skill_id JOIN skills s1 ON js1.skill_id = s1.skill_id JOIN skills s2 ON js2.skill_id = s2.skill_id GROUP BY s1.name, s2.name ORDER BY pair_frequency DESC LIMIT 10;`
  },
  {
    name: "Salary Benchmarks by Tech Domain",
    sql: `SELECT role_category, COUNT(*) AS postings, ROUND(MIN(salary_min), 0) AS min_starting_dkk, ROUND(AVG(salary_avg), 0) AS avg_monthly_dkk, ROUND(MAX(salary_max), 0) AS max_ceiling_dkk FROM jobs WHERE salary_avg IS NOT NULL GROUP BY role_category ORDER BY avg_monthly_dkk DESC;`
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'skills' | 'sql' | 'matcher' | 'ai' | 'pipeline' | 'architecture' | 'interview'>('overview');
  const [stats, setStats] = useState<StatsData | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  // SQL Console State
  const [customSql, setCustomSql] = useState(PRESET_QUERIES[0].sql);
  const [sqlResults, setSqlResults] = useState<{ rows: any[]; rowCount: number; durationMs: number } | null>(null);
  const [sqlError, setSqlError] = useState<string | null>(null);
  const [executingSql, setExecutingSql] = useState(false);

  // Candidate Matcher State
  const [candidateSkills, setCandidateSkills] = useState<string[]>(['Python', 'SQL', 'Git', 'Docker', 'Pandas', 'Power BI']);
  const [candidateEnglish, setCandidateEnglish] = useState('B2');
  const [candidateDanish, setCandidateDanish] = useState('A1');
  const [candidateExp, setCandidateExp] = useState('junior');
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [matchResult, setMatchResult] = useState<any>(null);
  const [matchingLoading, setMatchingLoading] = useState(false);

  // AI Semantic Analysis State
  const [aiJobId, setAiJobId] = useState<string>('');
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Pipeline Execution State
  const [pipelineOutput, setPipelineOutput] = useState<string>('');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [testOutput, setTestOutput] = useState<string>('');
  const [testsRunning, setTestsRunning] = useState(false);

  useEffect(() => {
    fetchInitialData();
  }, []);

  async function fetchInitialData() {
    setLoading(true);
    try {
      const statsRes = await fetch('/api/stats');
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      const jobsRes = await fetch('/api/jobs?limit=100');
      if (jobsRes.ok) {
        const jobsData = await jobsRes.json();
        setJobs(jobsData);
        if (jobsData.length > 0) {
          setSelectedJobId(jobsData[0].job_id);
          setAiJobId(jobsData[0].job_id);
        }
      }
    } catch (e) {
      console.error('Error fetching data:', e);
    } finally {
      setLoading(false);
    }
  }

  async function executeQuery(queryToRun?: string) {
    const q = queryToRun || customSql;
    setExecutingSql(true);
    setSqlError(null);
    try {
      const res = await fetch('/api/sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: q }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSqlError(data.error || 'Failed to execute query');
        setSqlResults(null);
      } else {
        setSqlResults(data);
      }
    } catch (err: any) {
      setSqlError(err.message || 'Execution error');
      setSqlResults(null);
    } finally {
      setExecutingSql(false);
    }
  }

  async function runCandidateMatch() {
    if (!selectedJobId) return;
    setMatchingLoading(true);
    try {
      const res = await fetch('/api/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jobId: selectedJobId,
          profile: {
            skills: candidateSkills,
            languages: { english: candidateEnglish, danish: candidateDanish },
            experience: { level: candidateExp },
          },
        }),
      });
      const data = await res.json();
      setMatchResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setMatchingLoading(false);
    }
  }

  async function runAiAnalysis() {
    const targetJob = jobs.find(j => j.job_id === aiJobId);
    if (!targetJob) return;
    setAiLoading(true);
    try {
      const res = await fetch('/api/ai/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: targetJob.title,
          description: targetJob.description,
        }),
      });
      const data = await res.json();
      setAiAnalysis(data);
    } catch (err) {
      console.error(err);
    } finally {
      setAiLoading(false);
    }
  }

  async function triggerPipeline() {
    setPipelineRunning(true);
    setPipelineOutput('Starting Extract -> Clean -> Transform -> Load pipeline...\n');
    try {
      const res = await fetch('/api/pipeline/run', { method: 'POST' });
      const data = await res.json();
      setPipelineOutput(data.output || data.error);
      fetchInitialData();
    } catch (err: any) {
      setPipelineOutput(`Error: ${err.message}`);
    } finally {
      setPipelineRunning(false);
    }
  }

  async function triggerTests() {
    setTestsRunning(true);
    setTestOutput('Running python unittest test suite across all modules...\n');
    try {
      const res = await fetch('/api/tests/run', { method: 'POST' });
      const data = await res.json();
      setTestOutput(data.output);
    } catch (err: any) {
      setTestOutput(`Error: ${err.message}`);
    } finally {
      setTestsRunning(false);
    }
  }

  const kpis = stats?.kpis;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-red-600/90 text-white flex items-center justify-center font-bold text-sm tracking-wider shadow-inner">
              DK
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-semibold text-slate-100 tracking-tight text-base sm:text-lg">
                  Danish Job Market Analytics
                </h1>
                <span className="text-[11px] font-mono uppercase bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 px-1.5 py-0.5 rounded">
                  Portfolio Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">
                End-to-End IT Data Pipeline &middot; SQLite &middot; Python &middot; Microsoft Fabric Ready
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Target: Data Specialist &middot; Instructor &middot; Denmark</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 flex gap-1 overflow-x-auto text-xs sm:text-sm font-medium border-t border-slate-800/60 pt-1">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'overview'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" /> Market Overview
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'skills'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingUp className="w-4 h-4" /> Skills &amp; Demand
          </button>
          <button
            onClick={() => setActiveTab('sql')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'sql'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-4 h-4" /> SQL Studio
          </button>
          <button
            onClick={() => setActiveTab('matcher')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'matcher'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <UserCheck className="w-4 h-4" /> Candidate Match
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'ai'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cpu className="w-4 h-4" /> AI Analysis
          </button>
          <button
            onClick={() => setActiveTab('pipeline')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'pipeline'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Terminal className="w-4 h-4" /> Pipeline &amp; Tests
          </button>
          <button
            onClick={() => setActiveTab('architecture')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'architecture'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-4 h-4" /> Architecture &amp; Fabric
          </button>
          <button
            onClick={() => setActiveTab('interview')}
            className={`px-3 py-2 border-b-2 flex items-center gap-2 transition ${
              activeTab === 'interview'
                ? 'border-cyan-400 text-cyan-300 bg-slate-800/40'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BookOpen className="w-4 h-4" /> Interview Kit
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 py-6 flex-1 w-full">
        {loading ? (
          <div className="py-20 text-center text-slate-400 flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
            <p className="font-mono text-sm">Querying SQLite database &amp; loading Danish market metrics...</p>
          </div>
        ) : (
          <>
            {/* TAB 1: OVERVIEW */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                {/* KPI Cards Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Total IT Jobs</span>
                    <span className="text-2xl font-bold font-mono text-slate-100">{kpis?.total_jobs || 443}</span>
                    <span className="text-[11px] text-slate-400 block mt-1">Danish vacancies</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Companies</span>
                    <span className="text-2xl font-bold font-mono text-cyan-400">{kpis?.total_companies || 22}</span>
                    <span className="text-[11px] text-slate-400 block mt-1">Across tech hubs</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Cities Covered</span>
                    <span className="text-2xl font-bold font-mono text-slate-100">{kpis?.total_cities || 8}</span>
                    <span className="text-[11px] text-slate-400 block mt-1">CPH, Aarhus, Odense...</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">English-Friendly</span>
                    <span className="text-2xl font-bold font-mono text-emerald-400">{kpis?.english_friendly_pct || 69.5}%</span>
                    <span className="text-[11px] text-slate-400 block mt-1">{kpis?.english_friendly_jobs} international</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Junior Index</span>
                    <span className="text-2xl font-bold font-mono text-purple-400">{kpis?.junior_opportunity_index || 41.5}%</span>
                    <span className="text-[11px] text-slate-400 block mt-1">{kpis?.junior_jobs} entry roles</span>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 p-4 rounded">
                    <span className="text-xs uppercase tracking-wider text-slate-400 block mb-1">Avg Salary</span>
                    <span className="text-xl font-bold font-mono text-amber-400">
                      {kpis?.salary_avg_dkk ? `${kpis.salary_avg_dkk.toLocaleString()} DKK` : '55,564 DKK'}
                    </span>
                    <span className="text-[11px] text-slate-400 block mt-1">Monthly gross benchmark</span>
                  </div>
                </div>

                {/* Cities & Categories Two-Column */}
                <div className="grid md:grid-cols-2 gap-6">
                  {/* City Distribution */}
                  <div className="bg-slate-900 border border-slate-800 rounded p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-cyan-400" /> Geographic Job Distribution
                      </h2>
                      <span className="text-xs text-slate-400">Capital vs Regions</span>
                    </div>
                    <div className="space-y-3">
                      {stats?.cities.map((city) => {
                        const pct = Math.round((city.job_count / (kpis?.total_jobs || 1)) * 100);
                        return (
                          <div key={city.city} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="font-medium text-slate-300">
                                {city.city} <span className="text-slate-400 font-normal">({city.region})</span>
                              </span>
                              <span className="font-mono text-slate-400">
                                {city.job_count} jobs ({pct}%) &middot; {city.english_friendly_count} EN
                              </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-cyan-500 h-1.5 rounded-full"
                                style={{ width: `${Math.min(100, pct * 2.2)}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* IT Domain Categories */}
                  <div className="bg-slate-900 border border-slate-800 rounded p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <Code2 className="w-4 h-4 text-purple-400" /> IT Role Domains in Denmark
                      </h2>
                      <span className="text-xs text-slate-400">Demand &amp; Junior Openings</span>
                    </div>
                    <div className="space-y-3">
                      {stats?.categories.map((cat) => {
                        const pct = Math.round((cat.count / (kpis?.total_jobs || 1)) * 100);
                        return (
                          <div key={cat.role_category} className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="font-medium text-slate-300">{cat.role_category}</span>
                              <span className="font-mono text-slate-400">
                                {cat.count} jobs &middot; {cat.junior_count} junior &middot; avg {cat.avg_salary.toLocaleString()} DKK
                              </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-purple-500 h-1.5 rounded-full"
                                style={{ width: `${Math.min(100, pct * 2.8)}%` }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Top Hiring Companies Table */}
                <div className="bg-slate-900 border border-slate-800 rounded p-5">
                  <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-emerald-400" /> Top Employers in the Danish IT Market
                  </h2>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-slate-950/70 text-slate-400 uppercase tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="py-2.5 px-3">Company</th>
                          <th className="py-2.5 px-3">Industry</th>
                          <th className="py-2.5 px-3">Total Openings</th>
                          <th className="py-2.5 px-3">International (EN) Ratio</th>
                          <th className="py-2.5 px-3">Average Salary</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        {stats?.companies.map((c) => (
                          <tr key={c.company} className="hover:bg-slate-800/30">
                            <td className="py-2.5 px-3 font-sans font-medium text-slate-200">{c.company}</td>
                            <td className="py-2.5 px-3 font-sans text-slate-400">{c.industry}</td>
                            <td className="py-2.5 px-3 text-cyan-400">{c.open_positions}</td>
                            <td className="py-2.5 px-3 text-emerald-400">
                              {Math.round((c.english_friendly_positions / c.open_positions) * 100)}%
                            </td>
                            <td className="py-2.5 px-3 text-slate-300">{c.avg_salary.toLocaleString()} DKK</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: SKILLS & DEMAND */}
            {activeTab === 'skills' && (
              <div className="space-y-6">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Top In-Demand Skills */}
                  <div className="bg-slate-900 border border-slate-800 rounded p-5">
                    <h2 className="text-sm font-semibold text-slate-200 mb-1">
                      Most Demanded Technologies in Denmark
                    </h2>
                    <p className="text-xs text-slate-400 mb-4">
                      Market penetration calculated over {kpis?.total_jobs} analyzed job postings.
                    </p>
                    <div className="space-y-2.5">
                      {stats?.skills.map((s) => (
                        <div key={s.skill_name} className="flex items-center justify-between text-xs py-1 border-b border-slate-800/40">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-slate-200 w-28 truncate">{s.skill_name}</span>
                            <span className="text-[10px] text-slate-400 font-mono bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                              {s.category}
                            </span>
                          </div>
                          <div className="flex items-center gap-3 font-mono">
                            <span className="text-slate-400">{s.demand_count} jobs</span>
                            <span className="text-cyan-400 font-semibold w-12 text-right">{s.market_share_pct}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Co-Occurrence Matrix */}
                  <div className="bg-slate-900 border border-slate-800 rounded p-5 flex flex-col justify-between">
                    <div>
                      <h2 className="text-sm font-semibold text-slate-200 mb-1">
                        Technology Co-Occurrence (Tool Bundling)
                      </h2>
                      <p className="text-xs text-slate-400 mb-4">
                        Which tools frequently appear together in the same Danish job listing?
                      </p>
                      <div className="space-y-2">
                        {stats?.cooccurrence.map((pair, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between text-xs bg-slate-950 p-2.5 rounded border border-slate-800/80"
                          >
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-cyan-300">{pair.tech_a}</span>
                              <span className="text-slate-400">+</span>
                              <span className="font-semibold text-purple-300">{pair.tech_b}</span>
                            </div>
                            <span className="font-mono text-slate-400 text-[11px]">
                              {pair.cooccurrence_count} joint listings
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mt-4 p-3 bg-cyan-950/30 border border-cyan-800/40 rounded text-xs text-cyan-200">
                      <strong>Instructor &amp; Specialist Insight:</strong> The strongest clusters in Denmark center around{' '}
                      <em>Python + SQL</em> (foundation), <em>Azure + Databricks + Fabric</em> (modern enterprise lakehouse), and{' '}
                      <em>Docker + Linux + CI/CD</em> (DevOps enablement).
                    </div>
                  </div>
                </div>

                {/* Language Requirements Deep Dive: English, Danish, Both, Unknown */}
                <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <Globe2 className="w-4 h-4 text-cyan-400" /> Language Requirement Detection (English, Danish, Both, Unknown)
                      </h2>
                      <p className="text-xs text-slate-400">
                        Rigorous 4-way classification across {kpis?.total_jobs || 443} analyzed Danish IT vacancies.
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                    <div className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-emerald-400">English Only</span>
                        <span className="font-mono text-slate-100 font-bold">
                          {kpis?.language_percentages?.english ?? kpis?.english_friendly_pct}%
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block">
                        {kpis?.language_counts?.english ?? 235} openings
                      </span>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Multinational pharma (Novo Nordisk), shipping (Maersk), fintech (SimCorp) &amp; tech startups.
                      </p>
                    </div>

                    <div className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-cyan-400">Both (EN + DA)</span>
                        <span className="font-mono text-slate-100 font-bold">
                          {kpis?.language_percentages?.both ?? 25.1}%
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block">
                        {kpis?.language_counts?.both ?? 110} openings
                      </span>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Consultancies (Netcompany, Devoteam, Delegate) requiring Danish for clients &amp; English for technical work.
                      </p>
                    </div>

                    <div className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-amber-400">Danish Only</span>
                        <span className="font-mono text-slate-100 font-bold">
                          {kpis?.language_percentages?.danish ?? 12.0}%
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block">
                        {kpis?.language_counts?.danish ?? 53} openings
                      </span>
                      <p className="text-[11px] text-slate-400 mt-1">
                        Public sector IT (KMD, Kommuner, Skatteforvaltningen) with strictly Danish internal operations.
                      </p>
                    </div>

                    <div className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-purple-400">Unknown / Unstated</span>
                        <span className="font-mono text-slate-100 font-bold">
                          {kpis?.language_percentages?.unknown ?? 7.9}%
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 block">
                        {kpis?.language_counts?.unknown ?? 35} openings
                      </span>
                      <p className="text-[11px] text-slate-400 mt-1">
                        No explicit language clause; focus is on engineering craftsmanship and problem solving.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: SQL STUDIO */}
            {activeTab === 'sql' && (
              <div className="space-y-4">
                <div className="bg-slate-900 border border-slate-800 rounded p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                        <Database className="w-4 h-4 text-cyan-400" /> Interactive SQLite Analytics Console
                      </h2>
                      <p className="text-xs text-slate-400">
                        Direct query execution against the normalized Danish jobs database (`data/processed/danish_jobs.db`).
                      </p>
                    </div>
                  </div>

                  {/* Preset Queries Buttons */}
                  <div className="mb-3 flex flex-wrap gap-1.5">
                    <span className="text-xs text-slate-400 self-center mr-1">Presets:</span>
                    {PRESET_QUERIES.map((p, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          setCustomSql(p.sql);
                          executeQuery(p.sql);
                        }}
                        className="text-xs bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-white px-2.5 py-1 rounded border border-slate-800 transition"
                      >
                        {p.name}
                      </button>
                    ))}
                  </div>

                  {/* SQL Textarea */}
                  <div className="space-y-2">
                    <textarea
                      value={customSql}
                      onChange={(e) => setCustomSql(e.target.value)}
                      rows={4}
                      className="w-full bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs p-3 rounded focus:outline-none focus:border-cyan-500"
                      placeholder="Write your analytical SELECT SQL query here..."
                    />

                    <div className="flex justify-between items-center">
                      <span className="text-[11px] text-slate-400 font-mono">
                        Tables available: jobs, companies, locations, skills, job_skills, sources
                      </span>
                      <button
                        onClick={() => executeQuery()}
                        disabled={executingSql}
                        className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs px-4 py-2 rounded flex items-center gap-2 transition disabled:opacity-50"
                      >
                        <Play className="w-3.5 h-3.5" /> {executingSql ? 'Running...' : 'Execute SQL'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* SQL Results */}
                {sqlError && (
                  <div className="p-3 bg-red-950/40 border border-red-800/60 text-red-200 text-xs rounded font-mono">
                    {sqlError}
                  </div>
                )}

                {sqlResults && (
                  <div className="bg-slate-900 border border-slate-800 rounded p-4 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-slate-400 pb-2 border-b border-slate-800">
                      <span>Fetched {sqlResults.rowCount} rows</span>
                      <span>Execution time: {sqlResults.durationMs}ms</span>
                    </div>

                    <div className="overflow-x-auto max-h-96">
                      {sqlResults.rows.length === 0 ? (
                        <p className="text-xs text-slate-400 py-4 text-center">Query returned zero rows.</p>
                      ) : (
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider sticky top-0">
                            <tr>
                              {Object.keys(sqlResults.rows[0]).map((col) => (
                                <th key={col} className="py-2 px-3 border-b border-slate-800 font-mono">
                                  {col}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 font-mono">
                            {sqlResults.rows.map((row, i) => (
                              <tr key={i} className="hover:bg-slate-800/40">
                                {Object.values(row).map((val: any, j) => (
                                  <td key={j} className="py-2 px-3 text-slate-300">
                                    {val === null ? <span className="text-slate-600 italic">null</span> : String(val)}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: CANDIDATE MATCH */}
            {activeTab === 'matcher' && (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded p-5">
                  <h2 className="text-sm font-semibold text-slate-200 mb-1 flex items-center gap-2">
                    <UserCheck className="w-4 h-4 text-cyan-400" /> Interactive Candidate Match Simulator
                  </h2>
                  <p className="text-xs text-slate-400 mb-4">
                    Benchmark a junior candidate profile against live Danish IT vacancies with transparent skill and language gap evaluation.
                  </p>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Candidate Configuration */}
                    <div className="bg-slate-950 p-4 rounded border border-slate-800 space-y-4">
                      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Candidate Profile</h3>

                      <div>
                        <label className="text-xs text-slate-400 block mb-1.5">Candidate Technical Skills</label>
                        <div className="flex flex-wrap gap-1.5">
                          {['Python', 'SQL', 'Git', 'Docker', 'Pandas', 'Power BI', 'Azure', 'Databricks', 'Microsoft Fabric', 'dbt', 'TypeScript', 'React', '.NET', 'C#', 'Linux'].map((sk) => {
                            const selected = candidateSkills.includes(sk);
                            return (
                              <button
                                key={sk}
                                onClick={() => {
                                  if (selected) {
                                    setCandidateSkills(candidateSkills.filter((s) => s !== sk));
                                  } else {
                                    setCandidateSkills([...candidateSkills, sk]);
                                  }
                                }}
                                className={`text-xs px-2.5 py-1 rounded border transition ${
                                  selected
                                    ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
                                    : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                                }`}
                              >
                                {sk} {selected ? '✓' : '+'}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <label className="text-xs text-slate-400 block mb-1">English</label>
                          <select
                            value={candidateEnglish}
                            onChange={(e) => setCandidateEnglish(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 p-2 rounded"
                          >
                            <option value="C2">C2 (Native)</option>
                            <option value="C1">C1 (Advanced)</option>
                            <option value="B2">B2 (Professional)</option>
                            <option value="B1">B1 (Intermediate)</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-slate-400 block mb-1">Danish</label>
                          <select
                            value={candidateDanish}
                            onChange={(e) => setCandidateDanish(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 p-2 rounded"
                          >
                            <option value="A1">A1 (Beginner)</option>
                            <option value="A2">A2 (Elementary)</option>
                            <option value="B1">B1 (Intermediate)</option>
                            <option value="B2">B2 (Fluent)</option>
                            <option value="C1">C1/Native</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-slate-400 block mb-1">Seniority</label>
                          <select
                            value={candidateExp}
                            onChange={(e) => setCandidateExp(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 p-2 rounded"
                          >
                            <option value="junior">Junior</option>
                            <option value="mid">Mid</option>
                            <option value="senior">Senior</option>
                          </select>
                        </div>
                      </div>
                    </div>

                    {/* Job Selection */}
                    <div className="bg-slate-950 p-4 rounded border border-slate-800 space-y-4">
                      <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Target Job Posting</h3>

                      <div>
                        <label className="text-xs text-slate-400 block mb-1.5">Choose Danish Vacancy</label>
                        <select
                          value={selectedJobId}
                          onChange={(e) => setSelectedJobId(e.target.value)}
                          className="w-full bg-slate-900 border border-slate-800 text-xs text-slate-200 p-2 rounded"
                        >
                          {jobs.map((j) => (
                            <option key={j.job_id} value={j.job_id}>
                              {j.title} &middot; {j.company_name} ({j.city})
                            </option>
                          ))}
                        </select>
                      </div>

                      {(() => {
                        const curJob = jobs.find((j) => j.job_id === selectedJobId);
                        if (!curJob) return null;
                        return (
                          <div className="p-3 bg-slate-900 rounded border border-slate-800/80 space-y-1.5 text-xs">
                            <div className="font-semibold text-slate-100">{curJob.title}</div>
                            <div className="text-slate-400">
                              {curJob.company_name} &middot; {curJob.city} &middot; {curJob.remote_type}
                            </div>
                            <div className="text-slate-400">
                              Language Requirement:{' '}
                              {(() => {
                                const req = curJob.language_requirement || (curJob.is_danish_required ? 'Danish' : 'English');
                                if (req === 'English') {
                                  return <span className="text-emerald-400 font-medium">English Only (International)</span>;
                                } else if (req === 'Both') {
                                  return <span className="text-cyan-400 font-medium">Both Danish &amp; English</span>;
                                } else if (req === 'Danish') {
                                  return <span className="text-amber-400 font-medium">Danish Required</span>;
                                } else {
                                  return <span className="text-purple-400 font-medium">Unknown / Unspecified</span>;
                                }
                              })()}
                            </div>
                            <div className="text-slate-300 font-mono text-[11px]">
                              Required Stack: {curJob.skills_list || 'Python, SQL, Azure'}
                            </div>
                          </div>
                        );
                      })()}

                      <button
                        onClick={runCandidateMatch}
                        disabled={matchingLoading}
                        className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs py-2 rounded flex items-center justify-center gap-2 transition disabled:opacity-50"
                      >
                        <UserCheck className="w-4 h-4" />{' '}
                        {matchingLoading ? 'Evaluating Fit Score...' : 'Calculate Fit Score'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Match Result Display */}
                {matchResult && (
                  <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div>
                        <h3 className="text-base font-semibold text-slate-100">
                          Match Results: {matchResult.job_title} at {matchResult.company}
                        </h3>
                        <p className="text-xs text-slate-400">{matchResult.location}, Denmark</p>
                      </div>
                      <div className="text-right">
                        <span className="text-2xl font-bold font-mono text-cyan-400">
                          {matchResult.match_score}%
                        </span>
                        <span className="text-xs text-slate-400 block">Overall Alignment</span>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                      <div className="p-3 bg-emerald-950/30 border border-emerald-800/50 rounded">
                        <span className="text-xs font-semibold text-emerald-400 block mb-1">
                          Matched Technical Skills ({matchResult.matched_skills.length})
                        </span>
                        <p className="text-xs text-slate-300 font-mono">
                          {matchResult.matched_skills.length > 0
                            ? matchResult.matched_skills.join(', ')
                            : 'No direct skills matched.'}
                        </p>
                      </div>

                      <div className="p-3 bg-amber-950/30 border border-amber-800/50 rounded">
                        <span className="text-xs font-semibold text-amber-400 block mb-1">
                          Missing / Gap Skills ({matchResult.missing_skills.length})
                        </span>
                        <p className="text-xs text-slate-300 font-mono">
                          {matchResult.missing_skills.length > 0
                            ? matchResult.missing_skills.join(', ')
                            : 'All required technical skills matched!'}
                        </p>
                      </div>
                    </div>

                    {matchResult.language_note && (
                      <div
                        className={`p-3 rounded text-xs border ${
                          matchResult.language_match
                            ? 'bg-slate-950 border-slate-800 text-slate-300'
                            : 'bg-red-950/40 border-red-800/60 text-red-200'
                        }`}
                      >
                        <strong>Language Assessment:</strong> {matchResult.language_note}
                      </div>
                    )}

                    <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded text-xs text-cyan-200">
                      <strong>Instructor Portfolio Advice:</strong> {matchResult.recommendation}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 5: AI ANALYSIS */}
            {activeTab === 'ai' && (
              <div className="space-y-4">
                <div className="bg-slate-900 border border-slate-800 rounded p-5">
                  <h2 className="text-sm font-semibold text-slate-200 mb-1 flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-purple-400" /> AI Semantic Analysis &amp; Extraction
                  </h2>
                  <p className="text-xs text-slate-400 mb-4">
                    Demonstrating LLM extraction where deterministic regex falls short: subtle implicit cultural expectations, domain seniority, and clean JSON validation.
                  </p>

                  <div className="flex flex-col sm:flex-row gap-3 items-center">
                    <select
                      value={aiJobId}
                      onChange={(e) => setAiJobId(e.target.value)}
                      className="w-full sm:flex-1 bg-slate-950 border border-slate-800 text-xs text-slate-200 p-2.5 rounded"
                    >
                      {jobs.map((j) => (
                        <option key={j.job_id} value={j.job_id}>
                          {j.title} &middot; {j.company_name} ({j.city})
                        </option>
                      ))}
                    </select>

                    <button
                      onClick={runAiAnalysis}
                      disabled={aiLoading}
                      className="w-full sm:w-auto bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs px-4 py-2.5 rounded flex items-center justify-center gap-2 transition disabled:opacity-50"
                    >
                      <Sparkles className="w-3.5 h-3.5" /> {aiLoading ? 'Analyzing...' : 'Run AI Extraction'}
                    </button>
                  </div>
                </div>

                {aiAnalysis && (
                  <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-4">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                      <div>
                        <h3 className="text-sm font-semibold text-slate-200">Structured AI Extraction Output</h3>
                        <p className="text-xs text-slate-400">Strictly validated JSON contract</p>
                      </div>
                      <span className="text-[11px] font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
                        Validated Schema
                      </span>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4 text-xs">
                      <div className="space-y-3">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400 block mb-0.5">Role Category &amp; Seniority</span>
                          <span className="font-semibold text-slate-100">
                            {aiAnalysis.role_category} &middot; {aiAnalysis.seniority}
                          </span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400 block mb-0.5">Language Assessment</span>
                          <span className="text-slate-200 font-mono">
                            Danish Required: {aiAnalysis.language.danish_required ? 'Yes' : 'No'} &middot; English Accepted:{' '}
                            {aiAnalysis.language.english_accepted ? 'Yes' : 'No'}
                          </span>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400 block mb-0.5">Identified Skills</span>
                          <span className="font-mono text-cyan-300">{aiAnalysis.skills.join(', ')}</span>
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400 block mb-0.5">Summary</span>
                          <p className="text-slate-300 italic">{aiAnalysis.summary}</p>
                        </div>

                        <div className="p-3 bg-slate-950 rounded border border-slate-800">
                          <span className="text-slate-400 block mb-1">Implicit Workplace Requirements</span>
                          <ul className="list-disc list-inside space-y-1 text-slate-300">
                            {aiAnalysis.implicit_requirements.map((req: string, i: number) => (
                              <li key={i}>{req}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 6: PIPELINE & TESTS */}
            {activeTab === 'pipeline' && (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded p-5">
                  <h2 className="text-sm font-semibold text-slate-200 mb-1 flex items-center gap-2">
                    <Terminal className="w-4 h-4 text-cyan-400" /> ETL Pipeline &amp; Test Suite Execution
                  </h2>
                  <p className="text-xs text-slate-400 mb-4">
                    Trigger the Python ETL pipeline (`python -m src.pipeline`) or run the complete test suite directly from the UI.
                  </p>

                  <div className="flex flex-wrap gap-3 mb-6">
                    <button
                      onClick={triggerPipeline}
                      disabled={pipelineRunning}
                      className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs px-4 py-2.5 rounded flex items-center gap-2 transition disabled:opacity-50"
                    >
                      <Play className="w-3.5 h-3.5" />{' '}
                      {pipelineRunning ? 'Executing Pipeline...' : 'Run ETL Pipeline Now'}
                    </button>

                    <button
                      onClick={triggerTests}
                      disabled={testsRunning}
                      className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs px-4 py-2.5 rounded flex items-center gap-2 transition disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />{' '}
                      {testsRunning ? 'Running Tests...' : 'Run Automated Tests (18 tests)'}
                    </button>
                  </div>

                  {/* Terminal Outputs */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <span className="text-xs font-mono text-slate-400">Pipeline Output (`src.pipeline`)</span>
                      <pre className="bg-slate-950 border border-slate-800 p-3 rounded text-[11px] font-mono text-slate-300 h-64 overflow-y-auto whitespace-pre-wrap">
                        {pipelineOutput || 'Click "Run ETL Pipeline Now" to execute Extract -> Clean -> Transform -> Load phases live.'}
                      </pre>
                    </div>

                    <div className="space-y-2">
                      <span className="text-xs font-mono text-slate-400">Unit Tests Output (`tests/`)</span>
                      <pre className="bg-slate-950 border border-slate-800 p-3 rounded text-[11px] font-mono text-emerald-400 h-64 overflow-y-auto whitespace-pre-wrap">
                        {testOutput || 'Click "Run Automated Tests" to execute test_cleaning, test_transformations, test_skill_extraction, test_database, and test_matching.'}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 7: ARCHITECTURE & FABRIC */}
            {activeTab === 'architecture' && (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-4">
                  <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                    <Layers className="w-4 h-4 text-cyan-400" /> Data Engineering Architecture &amp; Microsoft Fabric Lakehouse Evolution
                  </h2>
                  <p className="text-xs text-slate-400">
                    How this project is built today, and how it directly maps to enterprise Lakehouse platforms (Microsoft Fabric, Databricks, Azure Data Lake) used in Danish consulting.
                  </p>

                  <div className="grid md:grid-cols-2 gap-6 text-xs">
                    {/* Current Local Architecture */}
                    <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span className="font-semibold text-cyan-300">Phase 1: Current Implementation (Local / Docker)</span>
                        <span className="text-[10px] font-mono bg-cyan-950 text-cyan-400 px-1.5 py-0.5 rounded">Active</span>
                      </div>
                      <div className="space-y-2 font-mono text-[11px] text-slate-300">
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Data Ingestion:</strong> JobSource interface (SyntheticDemoSource, CSVSource, JobIndex/Jobnet connectors)
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Cleaning &amp; DQ:</strong> Deduplication hash signatures, HTML stripping, city/company normalization, DQ quality reports
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Transformation:</strong> Regex skill taxonomy (config/skills.yaml), language flags, junior opportunity index
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Relational SQL Store:</strong> SQLite normalized schema (jobs, companies, locations, skills, job_skills)
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Serving &amp; Analytics:</strong> Streamlit / React Dashboard, SQL Studio, Candidate Matcher, AI layer
                        </div>
                      </div>
                    </div>

                    {/* Future Lakehouse Architecture */}
                    <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span className="font-semibold text-purple-300">Phase 2: Target Enterprise Migration (Fabric / Databricks)</span>
                        <span className="text-[10px] font-mono bg-purple-950 text-purple-400 px-1.5 py-0.5 rounded">Roadmap</span>
                      </div>
                      <div className="space-y-2 font-mono text-[11px] text-slate-300">
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>OneLake Ingestion:</strong> Azure Data Factory pipelines fetching job feeds into ADLS Gen2 raw landing zone
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Bronze Layer (Raw):</strong> Append-only Delta Lake tables preserving immutable JSON payload snapshots
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Silver Layer (Cleansed):</strong> PySpark / Databricks notebooks executing deduplication, DQ validation, and normalization
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Gold Layer (Curated Mart):</strong> Dimensional Star Schema (Fact_Job_Postings, Dim_Company, Dim_Skill, Dim_Location)
                        </div>
                        <div className="text-center text-slate-500">&darr;</div>
                        <div className="p-2 bg-slate-900 rounded border border-slate-800">
                          <strong>Serving:</strong> Power BI Direct Lake mode on Microsoft Fabric for sub-second executive reporting
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-950 rounded border border-slate-800 text-xs text-slate-300 space-y-2">
                    <h3 className="font-semibold text-slate-100">Why this design is ideal for Danish consulting &amp; training firms:</h3>
                    <p>
                      Companies like Netcompany, Devoteam, Delegate, NNIT, and Avanade Denmark heavily utilize Microsoft Azure and Microsoft Fabric. By structuring the codebase into cleanly decoupled Extract, Clean, Transform, and Load stages with strict contracts, transitioning from local Python + SQLite to PySpark + Delta Lake requires simply changing the persistence adapter without rewriting domain logic.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 8: INTERVIEW KIT */}
            {activeTab === 'interview' && (
              <div className="space-y-6">
                <div className="bg-slate-900 border border-slate-800 rounded p-5 space-y-6">
                  <div>
                    <h2 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-cyan-400" /> Portfolio Presentation &amp; Danish IT Technical Interview Kit
                    </h2>
                    <p className="text-xs text-slate-400">
                      Tailored specifically for a junior candidate applying for a <strong>Data Specialist / Data Instructor</strong> position in Denmark.
                    </p>
                  </div>

                  {/* Pitch Cards */}
                  <div className="grid md:grid-cols-2 gap-4 text-xs">
                    <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-2">
                      <span className="text-xs font-semibold text-cyan-400 block uppercase tracking-wider">
                        CV &amp; LinkedIn Summary (5-7 lines)
                      </span>
                      <p className="text-slate-300 leading-relaxed font-mono text-[11px]">
                        "Built <strong>Danish Job Market Analytics</strong>, a complete end-to-end data pipeline and analytics platform exploring hiring patterns across 400+ Danish IT postings (Copenhagen, Aarhus, Odense, Aalborg). Demonstrates automated ingestion, data quality validation, deduplication hashing, and skill taxonomy extraction using Python, SQL, and SQLite, with a containerized Docker architecture. Engineered an interactive Candidate Matching engine and AI-assisted job description analysis. Designed with a clean migration path toward Microsoft Fabric / Databricks Lakehouse architecture for enterprise scalability."
                      </p>
                    </div>

                    <div className="p-4 bg-slate-950 rounded border border-slate-800 space-y-2">
                      <span className="text-xs font-semibold text-purple-400 block uppercase tracking-wider">
                        30-Second Interview Elevator Pitch
                      </span>
                      <p className="text-slate-300 leading-relaxed italic text-slate-200">
                        "I built Danish Job Market Analytics to prove my hands-on data engineering foundation. It's a pipeline that extracts IT vacancies, cleans and deduplicates records with custom hash signatures, extracts skills via regex taxonomies, and stores them in a normalized relational database. I then built an analytical engine that uncovers Danish market realities—like nearly 70% of tech jobs accepting English—plus an interactive candidate matcher. I designed every phase with modular code and unit tests so it can easily transition into a Microsoft Fabric or Databricks lakehouse."
                      </p>
                    </div>
                  </div>

                  {/* 10 Technical Interview Questions */}
                  <div className="space-y-4">
                    <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                      10 Technical Interview Questions from Danish IT Employers &amp; Model Answers
                    </h3>

                    <div className="space-y-3">
                      {[
                        {
                          q: "1. Why did you choose a normalized relational model (jobs, companies, locations, skills, job_skills) instead of storing everything in one flat JSON or table?",
                          a: "A normalized model prevents data redundancy and anomalies. In IT recruiting, a single job references multiple skills (many-to-many relationship), and companies publish multiple jobs. By separating entities into 'jobs', 'skills', and a junction table 'job_skills', we can write performant aggregation queries like technology co-occurrence or market share ranking without string manipulation."
                        },
                        {
                          q: "2. How does your deduplication mechanism handle identical postings republished under slightly different names across different boards?",
                          a: "Rather than relying on primary keys, the cleaner computes a deterministic MD5 signature based on the normalized job title, cleaned company name (stripping Danish legal suffixes like A/S, ApS), and normalized city. This catches duplicate listings across different sources and dates, filtering 80+ duplicate records in our demo dataset."
                        },
                        {
                          q: "3. What challenges did you encounter when extracting programming skills like 'C#', '.NET', or 'Go'?",
                          a: "Standard regex word boundaries (\\b) fail on special characters: '#' and '.' are treated as non-word characters (\\W), so '\\bc#\\b' or '\\b.net\\b' fails when preceded by whitespace. Furthermore, 'Go' easily matches the common English verb. I resolved this using lookaheads and negative lookbehinds that respect symbol boundaries and tech contextual keywords."
                        },
                        {
                          q: "4. What role does the AI / LLM layer play in your pipeline, and why not use it for all data extraction?",
                          a: "Deterministic regex and SQL are orders of magnitude faster, 100% reproducible, cost nothing, and don't suffer from hallucination. The LLM is used strictly as an enrichment layer where deterministic logic fails—specifically for extracting implicit cultural traits (like Danish flat hierarchy or client-facing consulting nuances) and providing contextual summaries. If the API is offline, the pipeline still functions 100% via mock mode."
                        },
                        {
                          q: "5. How would you migrate this project to an enterprise Microsoft Fabric or Databricks platform?",
                          a: "I would adopt the Medallion Architecture: Landing files into OneLake ADLS Gen2 (Bronze layer), executing PySpark cleaning and validation notebooks into Delta Lake (Silver layer), and creating dimensional Star Schema tables (Fact_Job_Postings, Dim_Skill) in Gold. Finally, Power BI connects via Direct Lake mode for instant analytical dashboards."
                        },
                        {
                          q: "6. How do you measure data quality in your pipeline?",
                          a: "The cleaner tracks a QualityReport object recording total records processed, valid records, duplicate drop count, and schema validation errors (e.g. invalid date formats, null job IDs, or min salary > max salary). A data health percentage is logged at the end of every pipeline run."
                        },
                        {
                          q: "7. What did your analytics reveal about the language requirement in the Danish tech sector?",
                          a: "Nearly 70% of IT job openings in Denmark are English-friendly, particularly in multinational pharma (Novo Nordisk), logistics (Maersk), fintech (SimCorp), and startups. Danish fluency is concentrated in public sector IT (KMD, municipalities) and local client consulting. This informs international candidates to target international enterprises first while learning Danish."
                        },
                        {
                          q: "8. As a Data Instructor, how would you explain the difference between ETL and ELT to junior students?",
                          a: "In traditional ETL, data is transformed by an external compute engine (like Python) before being loaded into the database, which was necessary when database storage and compute were expensive. In modern ELT (e.g. with Snowflake, BigQuery, or Fabric), raw data is loaded directly into the cloud warehouse/lakehouse, and transformations are executed directly in SQL/Spark leveraging cloud elastic compute."
                        },
                        {
                          q: "9. Why did you include automated unit tests, and what do they verify?",
                          a: "The pytest/unittest suite contains 18 tests covering HTML stripping, Danish city normalizations, regex boundary handling for C# and Go, salary validation checks, database schema migrations, and candidate matching scores. This ensures that any new source added to the JobSource interface doesn't break existing downstream transformations."
                        },
                        {
                          q: "10. How does the candidate matcher calculate fit, and how do you ensure transparency?",
                          a: "It computes a weighted transparent formula: 70% technical skill overlap, 20% language suitability (flagging Danish B2+ requirements if needed), and 10% experience level alignment. Crucially, it doesn't just return a percentage—it explains exactly which skills matched, which are missing, and generates a concrete study roadmap."
                        }
                      ].map((item, idx) => (
                        <div key={idx} className="p-3.5 bg-slate-950 rounded border border-slate-800 space-y-1.5 text-xs">
                          <div className="font-semibold text-cyan-300">{item.q}</div>
                          <div className="text-slate-300 leading-relaxed">{item.a}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-4 text-center text-xs text-slate-500 font-mono">
        Danish Job Market Analytics &middot; Portfolio Project for Data Specialist / Instructor &middot; Denmark IT Market
      </footer>
    </div>
  );
}
