import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';
import util from 'util';
import fs from 'fs';

const execPromise = util.promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // Python runner helper to query SQLite
  async function runPythonScript(pyCode: string): Promise<any> {
    const escapedCode = pyCode.replace(/"/g, '\\"');
    const { stdout, stderr } = await execPromise(`python3 -c "${escapedCode}"`);
    if (stderr && !stdout) {
      throw new Error(stderr);
    }
    return JSON.parse(stdout);
  }

  // 1. Overview KPIs & Stats API
  app.get('/api/stats', async (req, res) => {
    try {
      const pyCode = `
import json, sqlite3
from src.database.repository import JobRepository
from src.analytics.analyzer import MarketAnalyzer

repo = JobRepository()
analyzer = MarketAnalyzer(repo)
kpis = analyzer.compute_overview_kpis()
cities = analyzer.get_jobs_by_city()
skills = analyzer.get_top_skills(15)
categories = analyzer.get_jobs_by_category()
companies = analyzer.get_top_companies(8)
cooccur = analyzer.get_skill_cooccurrence(12)

print(json.dumps({
    "kpis": kpis,
    "cities": cities,
    "skills": skills,
    "categories": categories,
    "companies": companies,
    "cooccurrence": cooccur
}))
`;
      const result = await runPythonScript(pyCode);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 2. Jobs List API
  app.get('/api/jobs', async (req, res) => {
    try {
      const limit = Number(req.query.limit) || 100;
      const category = req.query.category ? `"${req.query.category}"` : 'None';
      const city = req.query.city ? `"${req.query.city}"` : 'None';
      
      const pyCode = `
import json
from src.database.repository import JobRepository
repo = JobRepository()
jobs = repo.get_all_jobs(limit=${limit}, category=${category}, city=${city})
print(json.dumps(jobs))
`;
      const result = await runPythonScript(pyCode);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 3. Execute Custom SQL
  app.post('/api/sql', async (req, res) => {
    const { sql } = req.body;
    if (!sql || typeof sql !== 'string') {
      return res.status(400).json({ error: 'SQL query required' });
    }
    const cleanSql = sql.trim();
    // Safety check: allow SELECT queries only
    if (!cleanSql.toUpperCase().startsWith('SELECT')) {
      return res.status(400).json({ error: 'Only SELECT analytical queries are allowed in this console' });
    }

    try {
      const startTime = Date.now();
      const script = `
import json, sqlite3
conn = sqlite3.connect("data/processed/danish_jobs.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("""${cleanSql.replace(/"""/g, '')}""")
rows = [dict(r) for r in cur.fetchall()]
conn.close()
print(json.dumps(rows))
`;
      const tempScriptPath = path.join(__dirname, '.temp_query.py');
      fs.writeFileSync(tempScriptPath, script);
      const { stdout, stderr } = await execPromise(`python3 ${tempScriptPath}`);
      fs.unlinkSync(tempScriptPath);

      const durationMs = Date.now() - startTime;
      const data = JSON.parse(stdout);
      res.json({ rows: data, rowCount: data.length, durationMs });
    } catch (err: any) {
      res.status(400).json({ error: err.message });
    }
  });

  // 4. Candidate Match API
  app.post('/api/match', async (req, res) => {
    const { profile, jobId } = req.body;
    try {
      const script = `
import json
from src.database.repository import JobRepository
from src.matching.matcher import CandidateMatcher

repo = JobRepository()
jobs = repo.get_all_jobs(limit=1000)
target = next((j for j in jobs if j["job_id"] == "${jobId}"), jobs[0] if jobs else None)

matcher = CandidateMatcher()
profile = ${JSON.stringify(profile)}
res = matcher.evaluate_match(profile, target)
print(json.dumps(res.to_dict()))
`;
      const result = await runPythonScript(script);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 5. Trigger ETL Pipeline
  app.post('/api/pipeline/run', async (req, res) => {
    try {
      const { stdout, stderr } = await execPromise('python3 -m src.pipeline');
      res.json({ output: stdout, error: stderr });
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 6. Run Pytest / Unittest Suite
  app.post('/api/tests/run', async (req, res) => {
    try {
      const { stdout, stderr } = await execPromise('python3 -m unittest discover tests -v');
      res.json({ output: stdout + '\n' + stderr, success: true });
    } catch (err: any) {
      res.json({ output: err.stdout + '\n' + err.stderr, success: false });
    }
  });

  // 7. AI Semantic Analysis
  app.post('/api/ai/analyze', async (req, res) => {
    const { title, description } = req.body;
    try {
      const script = `
import json
from src.ai.analyzer import AIJobAnalyzer
analyzer = AIJobAnalyzer()
out = analyzer.analyze_job_description("""${(description || '').slice(0, 1500).replace(/"""/g, '')}""", """${(title || '').replace(/"""/g, '')}""")
print(json.dumps(out.to_dict()))
`;
      const result = await runPythonScript(script);
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // Vite integration in dev vs prod
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Danish Job Market Analytics server listening on http://0.0.0.0:${PORT}`);
  });
}

startServer();
