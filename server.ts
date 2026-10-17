import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import { execFile } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json({ limit: '1mb' }));

  // Concurrency & rate-limiting guards for heavy workloads
  let isPipelineRunning = false;
  let isTestsRunning = false;
  let lastPipelineRunAt = 0;
  let lastTestsRunAt = 0;
  const RUN_COOLDOWN_MS = 8000; // 8 seconds cooldown between runs

  /**
   * Safe Python bridge invoker.
   * Spawns /usr/bin/python3 directly (shell: false) and pipes JSON over stdin.
   * Completely eliminates shell injection and Python code injection.
   */
  function invokePythonBridge(action: string, params: Record<string, any> = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify({ action, params });
      
      const child = execFile(
        'python3',
        ['-m', 'src.api_bridge'],
        {
          cwd: __dirname,
          timeout: 20000,
          maxBuffer: 10 * 1024 * 1024,
          shell: false, // Explicitly disable shell interpretation
        },
        (error, stdout, stderr) => {
          if (error) {
            let errorMsg = stderr ? stderr.trim() : error.message;
            try {
              const parsedErr = JSON.parse(stderr);
              if (parsedErr.error) errorMsg = parsedErr.error;
            } catch {
              // Not JSON
            }
            return reject(new Error(errorMsg));
          }

          try {
            const data = JSON.parse(stdout);
            resolve(data);
          } catch (jsonErr: any) {
            reject(new Error(`Failed to parse Python output: ${jsonErr.message}`));
          }
        }
      );

      // Write parameters securely over stdin
      child.stdin?.write(payload);
      child.stdin?.end();
    });
  }

  // 1. Overview KPIs & Stats API
  app.get('/api/stats', async (_req, res) => {
    try {
      const result = await invokePythonBridge('get_stats');
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 2. Jobs List API with input sanitization
  app.get('/api/jobs', async (req, res) => {
    try {
      const rawLimit = Number(req.query.limit);
      const limit = Number.isInteger(rawLimit) && rawLimit > 0 ? Math.min(rawLimit, 300) : 100;
      
      const category = typeof req.query.category === 'string' && req.query.category.trim().length <= 100
        ? req.query.category.trim()
        : undefined;

      const city = typeof req.query.city === 'string' && req.query.city.trim().length <= 100
        ? req.query.city.trim()
        : undefined;

      const result = await invokePythonBridge('get_jobs', { limit, category, city });
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 3. Execute Custom SQL (Hardened with read-only validation & no shell/code generation)
  app.post('/api/sql', async (req, res) => {
    const { sql } = req.body;
    if (!sql || typeof sql !== 'string') {
      return res.status(400).json({ error: 'SQL query string required' });
    }

    const cleanSql = sql.trim();
    if (cleanSql.length > 3000) {
      return res.status(400).json({ error: 'Query exceeds maximum allowed length (3000 characters)' });
    }

    try {
      const startTime = Date.now();
      const result = await invokePythonBridge('execute_sql', { sql: cleanSql });
      const durationMs = Date.now() - startTime;
      res.json({ rows: result.rows, rowCount: result.rowCount, durationMs });
    } catch (err: any) {
      res.status(400).json({ error: err.message });
    }
  });

  // 4. Candidate Match API
  app.post('/api/match', async (req, res) => {
    const { profile, jobId } = req.body;
    
    if (typeof jobId !== 'string' || !/^[a-zA-Z0-9\-_]{1,64}$/.test(jobId.trim())) {
      return res.status(400).json({ error: 'Invalid jobId parameter' });
    }

    if (!profile || typeof profile !== 'object') {
      return res.status(400).json({ error: 'Valid profile object required' });
    }

    try {
      const result = await invokePythonBridge('match', {
        job_id: jobId.trim(),
        profile,
      });
      res.json(result);
    } catch (err: any) {
      res.status(500).json({ error: err.message });
    }
  });

  // 5. Trigger ETL Pipeline with mutex and cooldown protection
  app.post('/api/pipeline/run', (_req, res) => {
    const now = Date.now();
    if (isPipelineRunning) {
      return res.status(409).json({ error: 'An ETL pipeline run is currently in progress. Please wait.' });
    }
    if (now - lastPipelineRunAt < RUN_COOLDOWN_MS) {
      const remainingSec = Math.ceil((RUN_COOLDOWN_MS - (now - lastPipelineRunAt)) / 1000);
      return res.status(429).json({ error: `Pipeline recently executed. Cooldown active for ${remainingSec}s.` });
    }

    isPipelineRunning = true;
    lastPipelineRunAt = now;

    // Direct process invocation without shell
    execFile(
      'python3',
      ['-m', 'src.pipeline'],
      { cwd: __dirname, timeout: 60000, shell: false },
      (error, stdout, stderr) => {
        isPipelineRunning = false;
        if (error) {
          return res.status(500).json({ error: stderr || error.message, output: stdout });
        }
        res.json({ output: stdout, error: stderr });
      }
    );
  });

  // 6. Run Pytest / Unittest Suite with mutex and cooldown protection
  app.post('/api/tests/run', (_req, res) => {
    const now = Date.now();
    if (isTestsRunning) {
      return res.status(409).json({ error: 'Test suite execution is already in progress. Please wait.' });
    }
    if (now - lastTestsRunAt < RUN_COOLDOWN_MS) {
      const remainingSec = Math.ceil((RUN_COOLDOWN_MS - (now - lastTestsRunAt)) / 1000);
      return res.status(429).json({ error: `Tests recently executed. Cooldown active for ${remainingSec}s.` });
    }

    isTestsRunning = true;
    lastTestsRunAt = now;

    // Direct process invocation without shell
    execFile(
      'python3',
      ['-m', 'unittest', 'discover', 'tests', '-v'],
      { cwd: __dirname, timeout: 30000, shell: false },
      (error, stdout, stderr) => {
        isTestsRunning = false;
        const combined = `${stdout}\n${stderr}`.trim();
        if (error) {
          return res.json({ output: combined, success: false });
        }
        res.json({ output: combined, success: true });
      }
    );
  });

  // 7. AI Semantic Analysis (Safe string pass-through via JSON)
  app.post('/api/ai/analyze', async (req, res) => {
    const { title, description } = req.body;
    const cleanTitle = typeof title === 'string' ? title.slice(0, 200) : '';
    const cleanDesc = typeof description === 'string' ? description.slice(0, 3000) : '';

    try {
      const result = await invokePythonBridge('ai_analyze', {
        title: cleanTitle,
        description: cleanDesc,
      });
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
    app.get('*', (_req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Danish Job Market Analytics server listening securely on http://0.0.0.0:${PORT}`);
  });
}

startServer();
