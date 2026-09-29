// Keeps one long-lived Python/SymPy worker (solver/main.py) and sends it JSON-line requests.
// SymPy takes ~1s to import, so reusing the process makes each solve fast.
import { spawn } from 'node:child_process';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.join(__dirname, 'solver', 'main.py');
const PYTHON = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
const TIMEOUT_MS = Number(process.env.SOLVE_TIMEOUT_MS || 30000);

let worker = null;
let ready = null;
let nextId = 1;
const pending = new Map(); // id -> { resolve, reject, timer }
let chain = Promise.resolve(); // one request at a time; a timeout restarts the worker

function start() {
  worker = spawn(PYTHON, ['-u', SCRIPT], {
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  ready = new Promise((resolve, reject) => {
    const rl = readline.createInterface({ input: worker.stdout });
    rl.on('line', (line) => {
      let msg;
      try {
        msg = JSON.parse(line);
      } catch {
        return;
      }
      if (msg.ready) return resolve();
      const job = pending.get(msg.id);
      if (!job) return;
      clearTimeout(job.timer);
      pending.delete(msg.id);
      msg.ok ? job.resolve(msg.data) : job.reject(Object.assign(new Error(msg.error), { userFacing: true }));
    });
    worker.once('error', (err) => {
      reject(new Error(`Could not start Python (${PYTHON}): ${err.message}. Set PYTHON in .env.`));
    });
  });

  worker.stderr.on('data', (d) => process.stderr.write(`[solver] ${d}`));
  const self = worker;
  worker.on('exit', (code) => {
    if (worker !== self) return;
    for (const [, job] of pending) {
      clearTimeout(job.timer);
      job.reject(new Error(`Solver process exited (code ${code}).`));
    }
    pending.clear();
    worker = null;
  });
}

function restart() {
  if (worker) {
    const old = worker;
    worker = null;
    old.kill();
  }
  start();
}

export async function warmUp() {
  if (!worker) start();
  await ready;
}

export function solve(op, params) {
  const run = async () => {
    if (!worker) start();
    await ready;
    const id = nextId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(Object.assign(new Error(
          `This problem took longer than ${TIMEOUT_MS / 1000}s. It may not have a closed-form answer; ` +
          'try simplifying it or using definite bounds.'), { userFacing: true }));
        restart(); // SymPy can't be interrupted mid-computation, so replace the worker
      }, TIMEOUT_MS);
      pending.set(id, { resolve, reject, timer });
      worker.stdin.write(JSON.stringify({ id, op, params }) + '\n');
    });
  };
  const result = chain.then(run, run);
  chain = result.catch(() => {});
  return result;
}

export function stop() {
  if (worker) worker.kill();
}
