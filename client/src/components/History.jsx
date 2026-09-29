import { OPS } from '../ops.js';
import { renderTex } from './MathText.jsx';

function summary(item) {
  const p = item.params || {};
  return p.expr || p.equation || p.term || p.field || '';
}

export default function History({ items, db, onLoad, onFavorite, onRemove, onClear, onClose }) {
  return (
    <aside className="history">
      <div className="history-head">
        <h2>History</h2>
        <div className="history-actions">
          {db && items.length > 0 && (
            <button className="link-btn" onClick={onClear} title="Remove everything except starred problems">Clear</button>
          )}
          <button className="icon-btn" onClick={onClose} aria-label="Close history">✕</button>
        </div>
      </div>
      {!db && (
        <p className="muted small">
          History is off because MongoDB isn't connected. Start MongoDB (or set <code>MONGO_URI</code> in
          <code> server/.env</code>) and restart the server to save your problems.
        </p>
      )}
      {db && items.length === 0 && <p className="muted small">Problems you solve will show up here.</p>}
      <ul className="history-list">
        {items.map((it) => (
          <li key={it._id} className="history-item">
            <button className="history-main" onClick={() => onLoad(it)}>
              <span className="history-op">{OPS[it.op]?.title || it.op}</span>
              <code className="history-input">{summary(it)}</code>
              {it.answer && (
                <span className="history-answer" dangerouslySetInnerHTML={{ __html: renderTex(it.answer) }} />
              )}
            </button>
            <div className="history-tools">
              <button
                className={`icon-btn ${it.favorite ? 'starred' : ''}`}
                onClick={() => onFavorite(it)}
                aria-label={it.favorite ? 'Unstar' : 'Star'}
                title={it.favorite ? 'Unstar' : 'Star (kept when clearing)'}
              >
                {it.favorite ? '★' : '☆'}
              </button>
              <button className="icon-btn" onClick={() => onRemove(it)} aria-label="Delete">🗑</button>
            </div>
          </li>
        ))}
      </ul>
    </aside>
  );
}
