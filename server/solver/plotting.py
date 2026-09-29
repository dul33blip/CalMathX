"""Graph data for single-variable results: sampled curves, tangent lines, key points, shading.

The client draws the graph; this module only samples y-values (None where the function is
undefined or not real) and describes what to draw. Zooming/panning re-samples via plot_op.
"""
import math

import mpmath
from sympy import lambdify, N

from common import SolverError, latex, parse, parse_symbol

SAMPLES = 480


def fnum(v):
    """Finite float value of a SymPy number, else None."""
    try:
        f = float(N(v))
        return f if math.isfinite(f) else None
    except Exception:
        return None


def sample(expr, x, xmin, xmax, n=SAMPLES):
    try:
        f = lambdify(x, expr, modules="mpmath")
    except Exception:
        return [[xmin + (xmax - xmin) * i / n, None] for i in range(n + 1)]
    pts = []
    for i in range(n + 1):
        xv = xmin + (xmax - xmin) * i / n
        try:
            y = f(mpmath.mpf(xv))
            if isinstance(y, mpmath.mpc):
                y = float(y.real) if abs(y.imag) < 1e-9 * max(1.0, abs(y.real)) else None
            else:
                y = float(y)
            if y is not None and not math.isfinite(y):
                y = None
        except Exception:
            y = None
        pts.append([round(xv, 12), y])
    return pts


def window(xs=(), half=5.0, pad=0.3, center=None):
    """x-range covering the given values with padding, or center ± half."""
    vals = [v for v in (fnum(c) for c in xs) if v is not None]
    if vals:
        lo, hi = min(vals), max(vals)
        span = hi - lo
        if span < 1e-9:
            h = max(half, abs(lo) * 0.5)
            return lo - h, hi + h
        return lo - span * pad, hi + span * pad
    c = fnum(center) if center is not None else 0.0
    c = c or 0.0
    h = max(half, abs(c) * 0.5)
    return c - h, c + h


class Graph:
    def __init__(self, x, xmin, xmax):
        self.x, self.xmin, self.xmax = x, float(xmin), float(xmax)
        self.series, self.points, self.vlines, self.shade = [], [], [], None
        self._exprs = []

    def curve(self, expr, label, role="f"):
        if expr.free_symbols - {self.x}:
            return None  # other free parameters: can't graph
        self.series.append({"expr": str(expr), "label": label, "role": role})
        self._exprs.append(expr)
        return len(self.series) - 1

    def point(self, xv, yv, label=None, hollow=False):
        px, py = fnum(xv), fnum(yv)
        if px is not None and py is not None:
            self.points.append({"x": px, "y": py, "label": label, "hollow": hollow})

    def vline(self, xv, label=None):
        px = fnum(xv)
        if px is not None:
            self.vlines.append({"x": px, "label": label})

    def shade_between(self, a, b, top, bottom=None):
        fa, fb = fnum(a), fnum(b)
        if top is None:
            return
        if fa is None:
            fa = self.xmin
        if fb is None:
            fb = self.xmax
        self.shade = {"a": fa, "b": fb, "top": top, "bottom": bottom}

    def spec(self):
        if not self.series:
            return None
        for s, e in zip(self.series, self._exprs):
            s["points"] = sample(e, self.x, self.xmin, self.xmax)
        if all(y is None for s in self.series for _, y in s["points"]):
            return None
        return {"var": self.x.name, "xmin": self.xmin, "xmax": self.xmax, "series": self.series,
                "points": self.points, "vlines": self.vlines, "shade": self.shade}


def single_var(expr, x):
    return expr.free_symbols <= {x}


def attach(res, build):
    """Add a graph to a result dict; graphing problems never break the solve itself."""
    try:
        g = build()
        spec = g.spec() if g else None
        if spec:
            res["plot"] = spec
    except Exception:
        pass
    return res


def fx(x, expr):
    return f"f({latex(x)}) = {latex(expr)}"


def tangent_line(expr, fp, x, a):
    fa, m = expr.subs(x, a), fp.subs(x, a)
    return (fa + m * (x - a)), fa, m


def plot_op(p):
    """Re-sample existing curves for a new x-window (zoom/pan)."""
    x = parse_symbol(p.get("var") or "x")
    try:
        xmin, xmax = float(p["xmin"]), float(p["xmax"])
    except (TypeError, ValueError, KeyError):
        raise SolverError("Invalid graph window.")
    if not (math.isfinite(xmin) and math.isfinite(xmax)) or not 1e-9 < xmax - xmin < 1e7:
        raise SolverError("Invalid graph window.")
    exprs = list(p.get("exprs") or [])[:6]
    return {"series": [sample(parse(e), x, xmin, xmax) for e in exprs]}
