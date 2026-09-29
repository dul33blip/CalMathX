import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { DEFAULT_BOUNDS } from '../ops.js';
import { renderTex } from './MathText.jsx';

const KEYS = [
  ['x²', '^2'], ['xⁿ', '^'], ['√', 'sqrt(', ')'], ['π', 'pi'], ['e', 'e'], ['∞', 'inf'],
  ['sin', 'sin(', ')'], ['cos', 'cos(', ')'], ['tan', 'tan(', ')'], ['ln', 'ln(', ')'],
  ['eˣ', 'e^(', ')'], ['|x|', 'abs(', ')'], ['( )', '(', ')'], ['/', '/'],
];

function usePreview(text) {
  const [state, setState] = useState({ latex: '', error: '' });
  useEffect(() => {
    if (!text || !text.trim()) {
      setState({ latex: '', error: '' });
      return;
    }
    const ctrl = new AbortController();
    const t = setTimeout(() => {
      api.preview(text, ctrl.signal)
        .then((r) => setState({ latex: r.latex || '', error: r.error || '' }))
        .catch(() => {});
    }, 350);
    return () => {
      clearTimeout(t);
      ctrl.abort();
    };
  }, [text]);
  return state;
}

function ExprField({ field, value, onChange, inputRef, onFocus }) {
  const { latex, error } = usePreview(value);
  return (
    <label className="field wide">
      <span className="field-label">{field.label}</span>
      <input
        ref={inputRef}
        className="expr-input"
        value={value}
        placeholder={field.placeholder}
        onChange={(e) => onChange(e.target.value)}
        onFocus={onFocus}
        autoComplete="off"
        spellCheck={false}
      />
      <div className={`preview ${error ? 'preview-error' : ''}`} aria-live="polite">
        {error ? error : latex ? <span dangerouslySetInnerHTML={{ __html: renderTex(latex) }} /> : <span className="muted">Preview appears here</span>}
      </div>
    </label>
  );
}

function BoundsField({ value, onChange, coords }) {
  const rows = value || DEFAULT_BOUNDS.cartesian;
  const set = (i, key, v) => onChange(rows.map((r, j) => (j === i ? { ...r, [key]: v } : r)));
  const hint = coords === 'polar' ? 'Use r and theta' : coords === 'cylindrical' ? 'Use z, r and theta'
    : coords === 'spherical' ? 'Use rho, phi and theta' : 'Leave the third row empty for a double integral';
  return (
    <div className="field wide">
      <span className="field-label">Bounds (innermost integral first) <span className="muted">· {hint}</span></span>
      <div className="bounds">
        {rows.map((r, i) => (
          <div className="bounds-row" key={i}>
            <span className="bounds-idx">{i + 1}</span>
            <input value={r.var} placeholder="var" onChange={(e) => set(i, 'var', e.target.value)} className="bounds-var" />
            <span className="muted">from</span>
            <input value={r.lower} placeholder="lower" onChange={(e) => set(i, 'lower', e.target.value)} />
            <span className="muted">to</span>
            <input value={r.upper} placeholder="upper" onChange={(e) => set(i, 'upper', e.target.value)} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function OpForm({ op, spec, params, setParams, onSubmit, loading }) {
  const lastInput = useRef(null);
  const exprRefs = useRef({});

  const set = (name, v) => setParams((p) => {
    const next = { ...p, [name]: v };
    if (op === 'multiple' && name === 'coords') next.bounds = DEFAULT_BOUNDS[v].map((b) => ({ ...b }));
    return next;
  });

  function insert([, before, after = '']) {
    const el = lastInput.current || Object.values(exprRefs.current)[0];
    if (!el) return;
    const name = el.dataset.name;
    const cur = params[name] ?? '';
    const s = el.selectionStart ?? cur.length;
    const e = el.selectionEnd ?? cur.length;
    const next = cur.slice(0, s) + before + cur.slice(s, e) + after + cur.slice(e);
    set(name, next);
    requestAnimationFrame(() => {
      el.focus();
      const caret = s + before.length + (e - s);
      el.setSelectionRange(caret, caret);
    });
  }

  return (
    <form
      className="op-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <div className="fields">
        {spec.fields.map((f) => {
          const v = params[f.name];
          if (f.type === 'expr') {
            return (
              <ExprField
                key={f.name}
                field={f}
                value={v ?? ''}
                onChange={(val) => set(f.name, val)}
                inputRef={(el) => {
                  if (el) {
                    el.dataset.name = f.name;
                    exprRefs.current[f.name] = el;
                  }
                }}
                onFocus={(e) => (lastInput.current = e.target)}
              />
            );
          }
          if (f.type === 'bounds') {
            return <BoundsField key={f.name} value={v} coords={params.coords} onChange={(val) => set(f.name, val)} />;
          }
          if (f.type === 'select') {
            return (
              <label key={f.name} className={`field ${f.small ? '' : 'medium'}`}>
                <span className="field-label">{f.label}</span>
                <select value={v ?? f.options[0][0]} onChange={(e) => set(f.name, e.target.value)}>
                  {f.options.map(([val, label]) => <option key={val} value={val}>{label}</option>)}
                </select>
              </label>
            );
          }
          return (
            <label key={f.name} className={`field ${f.small ? '' : 'medium'}`}>
              <span className="field-label">{f.label}</span>
              <input
                type={f.type === 'number' ? 'number' : 'text'}
                min={f.min}
                max={f.max}
                value={v ?? ''}
                placeholder={f.placeholder}
                onChange={(e) => set(f.name, e.target.value)}
                onFocus={(e) => {
                  e.target.dataset.name = f.name;
                  if (f.type === 'text') lastInput.current = e.target;
                }}
                autoComplete="off"
                spellCheck={false}
              />
            </label>
          );
        })}
      </div>

      <div className="keypad" aria-label="Math keypad">
        {KEYS.map((k) => (
          <button type="button" key={k[0]} onMouseDown={(e) => e.preventDefault()} onClick={() => insert(k)}>
            {k[0]}
          </button>
        ))}
      </div>

      <div className="form-actions">
        <button type="submit" className="solve-btn" disabled={loading}>
          {loading ? <span className="spinner" /> : null}
          {loading ? 'Solving…' : 'Solve step by step'}
        </button>
        <span className="muted hint">Press Enter to solve · use ^ for powers, * is optional (2x, x y)</span>
      </div>
    </form>
  );
}
