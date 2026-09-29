import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from './api.js';
import Graph from './components/Graph.jsx';
import History from './components/History.jsx';
import { MathBlock } from './components/MathText.jsx';
import OpForm from './components/OpForm.jsx';
import StepList from './components/StepList.jsx';
import { GROUPS, OPS, emptyParams } from './ops.js';

const store = {
  get(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      return v == null ? fallback : JSON.parse(v);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* storage unavailable */
    }
  },
};

function prepare(op, params) {
  const p = { ...params };
  if (op === 'volume') p.axis = p.method === 'shell' ? 'y' : 'x';
  return p;
}

export default function App() {
  const [op, setOp] = useState(() => (OPS[store.get('cmx.op')] ? store.get('cmx.op') : 'derivative'));
  const [paramsByOp, setParamsByOp] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDetail, setShowDetail] = useState(() => store.get('cmx.detail', true));
  const [theme, setTheme] = useState(() => store.get('cmx.theme', null));
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState({ db: false, items: [] });
  const [copied, setCopied] = useState(false);

  const spec = OPS[op];
  const params = paramsByOp[op] || emptyParams(op);
  const setParams = useCallback(
    (updater) => setParamsByOp((all) => {
      const cur = all[op] || emptyParams(op);
      return { ...all, [op]: typeof updater === 'function' ? updater(cur) : updater };
    }),
    [op],
  );

  useEffect(() => store.set('cmx.op', op), [op]);
  useEffect(() => store.set('cmx.detail', showDetail), [showDetail]);
  useEffect(() => {
    store.set('cmx.theme', theme);
    if (theme) document.documentElement.dataset.theme = theme;
    else delete document.documentElement.dataset.theme;
  }, [theme]);

  const refreshHistory = useCallback(() => {
    api.history().then(setHistory).catch(() => setHistory({ db: false, items: [] }));
  }, []);
  useEffect(refreshHistory, [refreshHistory]);

  function selectOp(next) {
    setOp(next);
    setResult(null);
    setError('');
  }

  async function solve(forOp = op, forParams = params) {
    const missing = OPS[forOp].fields.filter(
      (f) => !f.optional && ['expr', 'text', 'number'].includes(f.type) && !String(forParams[f.name] ?? '').trim(),
    );
    if (missing.length) {
      setResult(null);
      setError(`Please fill in: ${missing.map((f) => f.label.replace(/\s*=\s*$/, '')).join(', ')}.`);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.solve(forOp, prepare(forOp, forParams));
      setResult({ ...data, op: forOp, key: Date.now() });
      if (data.id) refreshHistory();
    } catch (e) {
      setResult(null);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function loadExample(ex) {
    const next = { ...emptyParams(op), ...ex };
    setParams(next);
    solve(op, next);
  }

  function loadHistory(item) {
    setOp(item.op);
    const next = { ...emptyParams(item.op), ...item.params };
    setParamsByOp((all) => ({ ...all, [item.op]: next }));
    setHistoryOpen(false);
    solve(item.op, next);
  }

  const groupOf = useMemo(() => GROUPS.find((g) => g.ops.includes(op)), [op]);

  function copyAnswer() {
    navigator.clipboard?.writeText(result.answer).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  }

  const hasSubsteps = result?.steps?.some((s) => s.depth > 0);

  return (
    <div className={`app ${historyOpen ? 'with-history' : ''}`}>
      <header className="topbar">
        <div className="brand">
          <span className="logo">CMX</span>
          <div>
            <h1>CalMathX</h1>
            <p className="tagline">Step-by-step solutions for algebra and Calculus 1–3</p>
          </div>
        </div>
        <div className="top-actions">
          <button
            className="icon-btn"
            onClick={() => setTheme(theme === 'dark' ? 'light' : theme === 'light' ? null : 'dark')}
            title={`Theme: ${theme || 'system'}`}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☾' : theme === 'light' ? '☀' : '◐'}
          </button>
          <button className="pill-btn" onClick={() => { setHistoryOpen((o) => !o); refreshHistory(); }}>
            History{history.items.length ? ` (${history.items.length})` : ''}
          </button>
        </div>
      </header>

      <nav className="sidebar" aria-label="Problem types">
        {GROUPS.map((g) => (
          <div key={g.id} className="nav-group">
            <h3>{g.label}</h3>
            {g.ops.map((o) => (
              <button key={o} className={`nav-item ${o === op ? 'active' : ''}`} onClick={() => selectOp(o)}>
                {OPS[o].title}
              </button>
            ))}
          </div>
        ))}
      </nav>

      <main className="main">
        <section className="card">
          <div className="card-head">
            <span className="badge">{groupOf?.label}</span>
            <h2>{spec.title}</h2>
            <p className="muted">{spec.blurb}</p>
          </div>

          <OpForm op={op} spec={spec} params={params} setParams={setParams} onSubmit={() => solve()} loading={loading} />

          <div className="examples">
            <span className="muted small">Try:</span>
            {spec.examples.map((ex, i) => (
              <button key={i} className="chip" onClick={() => loadExample(ex)} disabled={loading}>
                {ex.expr || ex.equation || ex.term || ex.field}
                {ex.point && op === 'limit' ? ` → ${ex.point}` : ''}
                {ex.lower != null && ex.upper != null && op !== 'multiple' ? ` [${ex.lower}, ${ex.upper}]` : ''}
                {ex.order ? ` (n=${ex.order})` : ''}
                {ex.vars ? ` ∂${ex.vars}` : ''}
              </button>
            ))}
          </div>
        </section>

        {error && (
          <section className="card error-card" role="alert">
            <strong>Couldn't solve that.</strong> {error}
          </section>
        )}

        {result && !error && (
          <section className="card result-card">
            <div className="answer-head">
              <h3>Answer</h3>
              <button className="link-btn" onClick={copyAnswer}>{copied ? 'Copied!' : 'Copy LaTeX'}</button>
            </div>
            <MathBlock tex={result.answer} className="answer" />
            {result.expression && (
              <div className="muted small">
                General form: <MathBlock tex={result.expression} className="inline-block" />
              </div>
            )}
            {result.approx && <p className="approx">≈ {result.approx}</p>}

            {result.plot && (
              <div className="graph-section">
                <h3>Graph</h3>
                <Graph key={result.key} spec={result.plot} />
              </div>
            )}

            <div className="steps-head">
              <h3>Step-by-step solution</h3>
              {hasSubsteps && (
                <label className="toggle">
                  <input type="checkbox" checked={showDetail} onChange={(e) => setShowDetail(e.target.checked)} />
                  Show detailed sub-steps
                </label>
              )}
            </div>
            <StepList steps={result.steps} showDetail={showDetail} />
          </section>
        )}

        {!result && !error && !loading && (
          <section className="empty muted">
            Enter a problem above or tap an example. Every answer comes with the full worked solution.
          </section>
        )}
      </main>

      {historyOpen && (
        <History
          items={history.items}
          db={history.db}
          onLoad={loadHistory}
          onClose={() => setHistoryOpen(false)}
          onFavorite={(it) => api.favorite(it._id, !it.favorite).then(refreshHistory)}
          onRemove={(it) => api.remove(it._id).then(refreshHistory)}
          onClear={() => api.clear().then(refreshHistory)}
        />
      )}
    </div>
  );
}
