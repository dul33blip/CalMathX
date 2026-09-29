import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../api.js';
import { renderTex } from './MathText.jsx';

// Interactive 2D graph: drag to pan, wheel or buttons to zoom, hover for values.
// The server samples the curves; on zoom/pan we ask it to re-sample the new window.

const ROLE_STYLE = {
  f: { color: 'var(--plot-1)', width: 2.5 },
  g: { color: 'var(--plot-2)', width: 2.5 },
  deriv: { color: 'var(--plot-3)', width: 2 },
  F: { color: 'var(--plot-3)', width: 2 },
  tangent: { color: 'var(--plot-4)', width: 2, dash: '7 5' },
  approx: { color: 'var(--plot-2)', width: 2, dash: '7 5' },
  asymptote: { color: 'var(--muted)', width: 1.5, dash: '4 4' },
};

const PAD = { l: 44, r: 14, t: 14, b: 28 };

function niceStep(span, target) {
  const raw = span / Math.max(1, target);
  const p = 10 ** Math.floor(Math.log10(raw));
  const m = raw / p;
  return (m < 1.5 ? 1 : m < 3.5 ? 2 : m < 7.5 ? 5 : 10) * p;
}

function fmt(v) {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—';
  if (Math.abs(v) < 1e-10) return '0';
  const a = Math.abs(v);
  if (a >= 1e5 || a < 1e-3) return v.toExponential(2);
  return String(Number(v.toPrecision(4)));
}

// y-range from the visible samples, ignoring extreme spikes (asymptotes)
function yRange(seriesData, roles, points, xmin, xmax) {
  const ys = [];
  seriesData.forEach((pts, i) => {
    if (roles[i] === 'tangent') return;
    for (const [x, y] of pts) if (y !== null && x >= xmin && x <= xmax) ys.push(y);
  });
  for (const p of points) if (p.x >= xmin && p.x <= xmax) ys.push(p.y);
  if (!ys.length) return [-5, 5];
  ys.sort((a, b) => a - b);
  const q = (t) => ys[Math.min(ys.length - 1, Math.max(0, Math.round(t * (ys.length - 1))))];
  let lo = q(0.03);
  let hi = q(0.97);
  for (const p of points) {
    if (p.x >= xmin && p.x <= xmax) {
      lo = Math.min(lo, p.y);
      hi = Math.max(hi, p.y);
    }
  }
  let span = hi - lo;
  if (span < 1e-9) {
    const c = lo;
    span = Math.max(2, Math.abs(c));
    lo = c - span / 2;
    hi = c + span / 2;
  }
  // Include the x-axis if it's reasonably close
  if (lo > 0 && lo < span * 0.6) lo = 0;
  if (hi < 0 && -hi < span * 0.6) hi = 0;
  span = hi - lo;
  return [lo - span * 0.1, hi + span * 0.1];
}

export default function Graph({ spec }) {
  const wrapRef = useRef(null);
  const svgRef = useRef(null);
  const [width, setWidth] = useState(640);
  const [view, setView] = useState({ xmin: spec.xmin, xmax: spec.xmax });
  const [data, setData] = useState(() => spec.series.map((s) => s.points));
  const [hoverX, setHoverX] = useState(null);
  const drag = useRef(null);
  const height = Math.round(Math.min(420, Math.max(260, width * 0.62)));

  // Track container width
  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(280, entry.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Re-sample when the window moves away from the original
  useEffect(() => {
    if (view.xmin === spec.xmin && view.xmax === spec.xmax) {
      setData(spec.series.map((s) => s.points));
      return;
    }
    const ctrl = new AbortController();
    const t = setTimeout(() => {
      api.plot({ exprs: spec.series.map((s) => s.expr), var: spec.var, xmin: view.xmin, xmax: view.xmax }, ctrl.signal)
        .then((r) => r.series && setData(r.series))
        .catch(() => {});
    }, 120);
    return () => {
      clearTimeout(t);
      ctrl.abort();
    };
  }, [view, spec]);

  const roles = spec.series.map((s) => s.role);
  const [ymin, ymax] = useMemo(
    () => yRange(data, roles, spec.points, view.xmin, view.xmax),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data, view.xmin, view.xmax, spec],
  );

  const W = width;
  const H = height;
  const iw = W - PAD.l - PAD.r;
  const ih = H - PAD.t - PAD.b;
  const sx = (x) => PAD.l + ((x - view.xmin) / (view.xmax - view.xmin)) * iw;
  const sy = (y) => PAD.t + (1 - (y - ymin) / (ymax - ymin)) * ih;
  const invX = (px) => view.xmin + ((px - PAD.l) / iw) * (view.xmax - view.xmin);

  function pathFor(pts) {
    const span = ymax - ymin;
    let d = '';
    let pen = false;
    let prev = null;
    for (const [x, y] of pts) {
      if (y === null) {
        pen = false;
        prev = null;
        continue;
      }
      // Break the line across vertical asymptotes (huge jump between off-screen extremes)
      if (prev !== null && Math.abs(y - prev) > span * 3 &&
          ((prev > ymax && y < ymin) || (prev < ymin && y > ymax))) pen = false;
      const cy = Math.max(ymin - span * 5, Math.min(ymax + span * 5, y));
      d += `${pen ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(cy).toFixed(1)}`;
      pen = true;
      prev = y;
    }
    return d;
  }

  function shadePath() {
    const s = spec.shade;
    if (!s || s.top == null || !data[s.top]) return null;
    const a = Math.max(s.a, view.xmin);
    const b = Math.min(s.b, view.xmax);
    if (b <= a) return null;
    const top = data[s.top].filter(([x, y]) => x >= a && x <= b && y !== null);
    if (top.length < 2) return null;
    const bottomData = s.bottom != null ? data[s.bottom] : null;
    const bottom = bottomData
      ? bottomData.filter(([x, y]) => x >= a && x <= b && y !== null).reverse()
      : [[top[top.length - 1][0], 0], [top[0][0], 0]];
    const clampY = (y) => Math.max(ymin - (ymax - ymin), Math.min(ymax + (ymax - ymin), y));
    return [...top, ...bottom].map(([x, y], i) => `${i ? 'L' : 'M'}${sx(x).toFixed(1)},${sy(clampY(y)).toFixed(1)}`).join('') + 'Z';
  }

  // Ticks
  const xStep = niceStep(view.xmax - view.xmin, iw / 70);
  const yStep = niceStep(ymax - ymin, ih / 45);
  const xTicks = [];
  for (let v = Math.ceil(view.xmin / xStep) * xStep; v <= view.xmax + 1e-9; v += xStep) xTicks.push(v);
  const yTicks = [];
  for (let v = Math.ceil(ymin / yStep) * yStep; v <= ymax + 1e-9; v += yStep) yTicks.push(v);
  const axisX = ymin <= 0 && ymax >= 0 ? sy(0) : null;
  const axisY = view.xmin <= 0 && view.xmax >= 0 ? sx(0) : null;

  const zoom = useCallback((factor, centerX) => {
    setView((v) => {
      const c = centerX ?? (v.xmin + v.xmax) / 2;
      const span = Math.min(1e6, Math.max(1e-6, (v.xmax - v.xmin) * factor));
      const t = (c - v.xmin) / (v.xmax - v.xmin);
      return { xmin: c - span * t, xmax: c + span * (1 - t) };
    });
  }, []);

  // Wheel zoom (non-passive so the page doesn't scroll while zooming the graph)
  useEffect(() => {
    const el = svgRef.current;
    if (!el) return;
    const onWheel = (e) => {
      e.preventDefault();
      const rect = el.getBoundingClientRect();
      const px = ((e.clientX - rect.left) / rect.width) * W;
      zoom(e.deltaY > 0 ? 1.15 : 1 / 1.15, invX(px));
    };
    el.addEventListener('wheel', onWheel, { passive: false });
    return () => el.removeEventListener('wheel', onWheel);
  });

  function toSvgX(e) {
    const rect = svgRef.current.getBoundingClientRect();
    return ((e.clientX - rect.left) / rect.width) * W;
  }

  function onPointerDown(e) {
    svgRef.current.setPointerCapture(e.pointerId);
    drag.current = { px: toSvgX(e), view };
  }
  function onPointerMove(e) {
    const px = toSvgX(e);
    if (drag.current) {
      const { view: v0, px: p0 } = drag.current;
      const dx = ((px - p0) / iw) * (v0.xmax - v0.xmin);
      setView({ xmin: v0.xmin - dx, xmax: v0.xmax - dx });
      setHoverX(null);
    } else if (px >= PAD.l && px <= W - PAD.r) {
      setHoverX(invX(px));
    }
  }
  function onPointerUp() {
    drag.current = null;
  }

  // Values under the cursor
  const hover = hoverX === null ? null : data.map((pts) => {
    if (!pts.length) return null;
    const x0 = pts[0][0];
    const dx = (pts[pts.length - 1][0] - x0) / (pts.length - 1);
    const i = Math.round((hoverX - x0) / dx);
    return pts[i] ? pts[i][1] : null;
  });

  const shade = shadePath();
  const clipId = useMemo(() => `clip-${Math.random().toString(36).slice(2)}`, []);
  const changed = view.xmin !== spec.xmin || view.xmax !== spec.xmax;

  return (
    <div className="graph" ref={wrapRef}>
      <div className="graph-toolbar">
        <div className="graph-legend">
          {spec.series.map((s, i) => {
            const st = ROLE_STYLE[s.role] || ROLE_STYLE.f;
            return (
              <span key={i} className="legend-item">
                <svg width="22" height="10" aria-hidden="true">
                  <line x1="1" y1="5" x2="21" y2="5" stroke={st.color} strokeWidth="2.5" strokeDasharray={st.dash} />
                </svg>
                <span dangerouslySetInnerHTML={{ __html: renderTex(s.label) }} />
              </span>
            );
          })}
        </div>
        <div className="graph-buttons">
          <button type="button" onClick={() => zoom(1 / 1.5)} aria-label="Zoom in" title="Zoom in">+</button>
          <button type="button" onClick={() => zoom(1.5)} aria-label="Zoom out" title="Zoom out">−</button>
          <button type="button" onClick={() => setView({ xmin: spec.xmin, xmax: spec.xmax })} disabled={!changed} title="Reset view">
            Reset
          </button>
        </div>
      </div>

      <svg
        ref={svgRef}
        viewBox={`0 0 ${W} ${H}`}
        width="100%"
        height={H}
        className="graph-svg"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={() => { setHoverX(null); drag.current = null; }}
        role="img"
        aria-label="Graph of the function"
      >
        <defs>
          <clipPath id={clipId}>
            <rect x={PAD.l} y={PAD.t} width={iw} height={ih} />
          </clipPath>
        </defs>

        {/* grid */}
        {xTicks.map((v) => (
          <line key={`gx${v}`} x1={sx(v)} x2={sx(v)} y1={PAD.t} y2={PAD.t + ih} className="grid" />
        ))}
        {yTicks.map((v) => (
          <line key={`gy${v}`} x1={PAD.l} x2={PAD.l + iw} y1={sy(v)} y2={sy(v)} className="grid" />
        ))}
        <rect x={PAD.l} y={PAD.t} width={iw} height={ih} className="plot-frame" />

        {/* axes */}
        {axisX !== null && <line x1={PAD.l} x2={PAD.l + iw} y1={axisX} y2={axisX} className="axis" />}
        {axisY !== null && <line x1={axisY} x2={axisY} y1={PAD.t} y2={PAD.t + ih} className="axis" />}

        {/* tick labels */}
        {xTicks.map((v) => (
          <text key={`tx${v}`} x={sx(v)} y={H - 8} className="tick" textAnchor="middle">{fmt(v)}</text>
        ))}
        {yTicks.map((v) => (
          <text key={`ty${v}`} x={PAD.l - 6} y={sy(v) + 4} className="tick" textAnchor="end">{fmt(v)}</text>
        ))}

        <g clipPath={`url(#${clipId})`}>
          {shade && <path d={shade} className="shade" />}

          {spec.vlines.map((l, i) => (
            <line key={`v${i}`} x1={sx(l.x)} x2={sx(l.x)} y1={PAD.t} y2={PAD.t + ih} className="vline" />
          ))}

          {data.map((pts, i) => {
            const st = ROLE_STYLE[spec.series[i]?.role] || ROLE_STYLE.f;
            return (
              <path key={i} d={pathFor(pts)} fill="none" stroke={st.color} strokeWidth={st.width}
                strokeDasharray={st.dash} strokeLinejoin="round" strokeLinecap="round" />
            );
          })}

          {spec.points.map((p, i) => (
            <g key={`p${i}`}>
              <circle cx={sx(p.x)} cy={sy(p.y)} r="5" className={p.hollow ? 'pt hollow' : 'pt'} />
              <text x={sx(p.x) + 8} y={sy(p.y) - 8} className="pt-label">
                {p.label ? `${p.label} ` : ''}({fmt(p.x)}, {fmt(p.y)})
              </text>
            </g>
          ))}

          {hoverX !== null && (
            <g className="hover">
              <line x1={sx(hoverX)} x2={sx(hoverX)} y1={PAD.t} y2={PAD.t + ih} className="hover-line" />
              {hover.map((y, i) => (y === null || y < ymin || y > ymax ? null : (
                <circle key={i} cx={sx(hoverX)} cy={sy(y)} r="3.5"
                  fill={(ROLE_STYLE[spec.series[i].role] || ROLE_STYLE.f).color} />
              )))}
            </g>
          )}
        </g>
      </svg>

      <div className="graph-readout" aria-live="polite">
        {hoverX === null ? (
          <span className="muted">Drag to pan · scroll or use +/− to zoom · hover for values</span>
        ) : (
          <>
            <span>{spec.var} = {fmt(hoverX)}</span>
            {hover.map((y, i) => (
              <span key={i} className="readout-item">
                <span className="dot" style={{ background: (ROLE_STYLE[spec.series[i].role] || ROLE_STYLE.f).color }} />
                {fmt(y)}
              </span>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
