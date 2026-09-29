import 'dotenv/config';
import cors from 'cors';
import express from 'express';
import mongoose from 'mongoose';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

import Problem from './models/Problem.js';
import { solve, stop, warmUp } from './solverBridge.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.API_PORT || process.env.PORT || 5000);
const MONGO_URI = process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/calmathx';

const OPS = new Set([
  'evaluate', 'solve', 'derivative', 'implicit', 'limit', 'tangent', 'extrema',
  'integral', 'area', 'volume', 'arclength', 'taylor', 'convergence',
  'partial', 'gradient', 'directional', 'multiple', 'lagrange', 'divergence', 'curl',
]);

mongoose.set('bufferCommands', false); // fail fast instead of hanging when Mongo is down
const dbReady = () => mongoose.connection.readyState === 1;

const app = express();
app.use(cors());
app.use(express.json({ limit: '20kb' }));

// Reject oversized inputs before they reach the solver
function validParams(params) {
  if (!params || typeof params !== 'object' || Array.isArray(params)) return false;
  return JSON.stringify(params).length <= 4000;
}

app.get('/api/health', (req, res) => {
  res.json({ ok: true, db: dbReady() });
});

app.post('/api/preview', async (req, res) => {
  const text = String(req.body?.text ?? '');
  if (!text.trim() || text.length > 500) return res.json({ latex: '' });
  try {
    res.json(await solve('preview', { text }));
  } catch (err) {
    res.json({ latex: '', error: err.message });
  }
});

// Re-sample graph curves for a new window (zoom/pan). Not saved to history.
app.post('/api/plot', async (req, res) => {
  const { exprs, var: v, xmin, xmax } = req.body || {};
  if (!Array.isArray(exprs) || exprs.length > 6 || !validParams({ exprs, v })) {
    return res.status(400).json({ error: 'Invalid graph request.' });
  }
  try {
    res.json(await solve('plot', { exprs: exprs.map(String), var: String(v || 'x'), xmin, xmax }));
  } catch (err) {
    res.status(err.userFacing ? 422 : 500).json({ error: err.message });
  }
});

app.post('/api/solve', async (req, res) => {
  const { op, params } = req.body || {};
  if (!OPS.has(op)) return res.status(400).json({ error: `Unknown operation '${op}'.` });
  if (!validParams(params)) return res.status(400).json({ error: 'Invalid or too-long input.' });
  try {
    const data = await solve(op, params);
    let id = null;
    if (dbReady()) {
      try {
        const doc = await Problem.create({ op, params, answer: data.answer, approx: data.approx });
        id = doc._id;
      } catch (e) {
        console.warn('History save failed:', e.message);
      }
    }
    res.json({ ...data, id });
  } catch (err) {
    res.status(err.userFacing ? 422 : 500).json({ error: err.message });
  }
});

app.get('/api/history', async (req, res) => {
  if (!dbReady()) return res.json({ db: false, items: [] });
  const limit = Math.min(Number(req.query.limit) || 50, 200);
  const items = await Problem.find().sort({ favorite: -1, createdAt: -1 }).limit(limit).lean();
  res.json({ db: true, items });
});

app.patch('/api/history/:id', async (req, res) => {
  if (!dbReady()) return res.status(503).json({ error: 'Database not connected.' });
  if (!mongoose.isValidObjectId(req.params.id)) return res.status(400).json({ error: 'Bad id.' });
  const doc = await Problem.findByIdAndUpdate(
    req.params.id, { favorite: Boolean(req.body?.favorite) }, { new: true }).lean();
  doc ? res.json(doc) : res.status(404).json({ error: 'Not found.' });
});

app.delete('/api/history/:id', async (req, res) => {
  if (!dbReady()) return res.status(503).json({ error: 'Database not connected.' });
  if (!mongoose.isValidObjectId(req.params.id)) return res.status(400).json({ error: 'Bad id.' });
  await Problem.findByIdAndDelete(req.params.id);
  res.json({ ok: true });
});

app.delete('/api/history', async (req, res) => {
  if (!dbReady()) return res.status(503).json({ error: 'Database not connected.' });
  await Problem.deleteMany({ favorite: false });
  res.json({ ok: true });
});

// In production, serve the built React app
const dist = path.join(__dirname, '..', 'client', 'dist');
if (fs.existsSync(dist)) {
  app.use(express.static(dist));
  app.get(/^(?!\/api).*/, (req, res) => res.sendFile(path.join(dist, 'index.html')));
}

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: 'Server error.' });
});

mongoose
  .connect(MONGO_URI, { serverSelectionTimeoutMS: 3000 })
  .then(() => console.log('MongoDB connected: history enabled'))
  .catch((e) => console.warn(`MongoDB not available (${e.message}). Solving still works; history is disabled.`));

warmUp()
  .then(() => console.log('Solver ready'))
  .catch((e) => console.error(e.message));

const server = app.listen(PORT, () => console.log(`CalMathX API on http://localhost:${PORT}`));

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    stop();
    server.close(() => process.exit(0));
  });
}
