"""Which curves/points to graph for each single-variable operation."""
from sympy import diff, solve, limit, oo, integrate, series, Integral, simplify, Symbol

from common import latex, parse, parse_equation, pick_variable, tidy
from plotting import Graph, window, fnum, single_var, fx, tangent_line


def _deriv_name(k):
    return {1: "f'", 2: "f''", 3: "f'''"}.get(k, f"f^{{({k})}}")


def _real(vals):
    out = []
    for v in vals:
        f = fnum(v)
        if f is not None and (v.is_real is not False):
            out.append(v)
    return out


def g_evaluate(p):
    expr = parse(p["expr"])
    if expr.is_number or len(expr.free_symbols) != 1:
        return None
    x = next(iter(expr.free_symbols))
    g = Graph(x, -10, 10)
    g.curve(expr, fx(x, expr))
    return g


def g_solve(p):
    eq = parse_equation(p["equation"])
    F = eq.lhs - eq.rhs
    x = pick_variable(F, p.get("var"))
    if not single_var(F, x):
        return None
    sols = _real(solve(F, x))
    lo, hi = window(sols, half=10, pad=0.6) if sols else (-10, 10)
    g = Graph(x, lo, hi)
    g.curve(eq.lhs, f"y = {latex(eq.lhs)}", "f")
    if eq.rhs != 0:
        g.curve(eq.rhs, f"y = {latex(eq.rhs)}", "g")
    for s in sols:
        g.point(s, eq.lhs.subs(x, s), "solution")
    return g


def g_derivative(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    if not single_var(expr, x):
        return None
    order = int(p.get("order") or 1)
    a = parse(p["point"]) if str(p.get("point") or "").strip() else None
    lo, hi = window(center=a, half=5) if a is not None else (-6, 6)
    g = Graph(x, lo, hi)
    g.curve(expr, fx(x, expr), "f")
    g.curve(tidy(diff(expr, x, order)), f"{_deriv_name(order)}({latex(x)})", "deriv")
    if a is not None:
        line, fa, m = tangent_line(expr, diff(expr, x), x, a)
        g.curve(line, rf"\text{{tangent at }} {latex(x)} = {latex(a)}", "tangent")
        g.point(a, fa, "tangent point")
    return g


def g_tangent(p):
    expr = parse(p["expr"])
    if len(expr.free_symbols) > 1:
        return None  # tangent plane: 3D, not graphed
    x = next(iter(expr.free_symbols)) if expr.free_symbols else Symbol("x")
    a = parse(str(p["point"]).split("=")[-1])
    line, fa, m = tangent_line(expr, diff(expr, x), x, a)
    lo, hi = window(center=a, half=4)
    g = Graph(x, lo, hi)
    g.curve(expr, fx(x, expr), "f")
    g.curve(line, f"y = {latex(tidy(line))}", "tangent")
    g.point(a, fa, "point of tangency")
    return g


def g_limit(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    if not single_var(expr, x):
        return None
    a = parse(p.get("point") or "0")
    d = p.get("dir") or "both"
    if a in (oo, -oo):
        lo, hi = (0, 40) if a == oo else (-40, 0)
        g = Graph(x, lo, hi)
        g.curve(expr, fx(x, expr), "f")
        L = limit(expr, x, a)
        if fnum(L) is not None:
            g.curve(L + 0 * x, f"y = {latex(L)}", "asymptote")
        return g

    lo, hi = window(center=a, half=4)
    g = Graph(x, lo, hi)
    g.curve(expr, fx(x, expr), "f")
    g.vline(a, f"x = {fnum(a):g}")
    dirs = {"both": "+-", "+": "+", "-": "-"}[d] if d in ("both", "+", "-") else "+-"
    try:
        L = limit(expr, x, a, dirs)
    except Exception:
        L = None
    fa = expr.subs(x, a)
    if L is not None and fnum(L) is not None:
        defined = fnum(fa) is not None
        if defined and abs(fnum(fa) - fnum(L)) < 1e-9:
            g.point(a, L, "limit = f(a)")
        else:
            g.point(a, L, "limit (hole)", hollow=True)
            if defined:
                g.point(a, fa, "f(a)")
    return g


def g_extrema(p):
    f = parse(p["expr"])
    if len(f.free_symbols) != 1:
        return None
    x = next(iter(f.free_symbols))
    fp, fpp = diff(f, x), diff(f, x, 2)
    crit = _real(solve(fp, x))
    interval = None
    if str(p.get("lower") or "").strip() and str(p.get("upper") or "").strip():
        interval = (parse(p["lower"]), parse(p["upper"]))
        crit = [c for c in crit if fnum(interval[0]) <= fnum(c) <= fnum(interval[1])]
        lo, hi = window(interval, pad=0.2)
    else:
        lo, hi = window(crit, half=6, pad=0.8) if crit else (-6, 6)
    g = Graph(x, lo, hi)
    g.curve(f, fx(x, f), "f")
    for c in crit:
        s = fnum(fpp.subs(x, c))
        label = "local min" if s and s > 0 else "local max" if s and s < 0 else "critical point"
        g.point(c, f.subs(x, c), label)
    if interval:
        for e in interval:
            g.vline(e)
            g.point(e, f.subs(x, e), "endpoint")
    return g


def g_integral(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    if not single_var(expr, x):
        return None
    lower, upper = str(p.get("lower") or "").strip(), str(p.get("upper") or "").strip()
    if lower and upper:
        a, b = parse(lower), parse(upper)
        fa, fb = fnum(a), fnum(b)
        if fa is not None and fb is not None:
            lo, hi = window([a, b], pad=0.35)
        elif fa is not None:
            lo, hi = fa - 2, fa + 12
        elif fb is not None:
            lo, hi = fb - 12, fb + 2
        else:
            lo, hi = -10, 10
        g = Graph(x, lo, hi)
        i = g.curve(expr, fx(x, expr), "f")
        g.shade_between(a, b, i)
        return g
    g = Graph(x, -6, 6)
    g.curve(expr, fx(x, expr), "f")
    F = integrate(expr, x)
    if not F.has(Integral):
        g.curve(tidy(F), rf"F({latex(x)}) = {latex(tidy(F))} \;\; (C = 0)", "F")
    return g


def g_area(p):
    f, g2 = parse(p["expr"]), parse(p.get("expr2") or "0")
    x = pick_variable(f + g2 + Symbol("x"), None)
    if str(p.get("lower") or "").strip() and str(p.get("upper") or "").strip():
        a, b = parse(p["lower"]), parse(p["upper"])
    else:
        pts = sorted(_real(solve(f - g2, x)), key=fnum)
        if len(pts) < 2:
            return None
        a, b = pts[0], pts[-1]
    lo, hi = window([a, b], pad=0.3)
    g = Graph(x, lo, hi)
    i = g.curve(f, f"y = {latex(f)}", "f")
    j = g.curve(g2, f"y = {latex(g2)}", "g") if g2 != 0 else None
    g.shade_between(a, b, i, j)
    for e in (a, b):
        g.point(e, f.subs(x, e), "intersection" if not str(p.get("lower") or "").strip() else None)
    return g


def g_volume(p):
    f, g2 = parse(p["expr"]), parse(p.get("expr2") or "0")
    x = pick_variable(f + g2 + Symbol("x"), None)
    a, b = parse(p["lower"]), parse(p["upper"])
    g = Graph(x, *window([a, b], pad=0.3))
    i = g.curve(f, f"y = {latex(f)}", "f")
    j = g.curve(g2, f"y = {latex(g2)}", "g") if g2 != 0 else None
    g.shade_between(a, b, i, j)
    return g


def g_arclength(p):
    f = parse(p["expr"])
    x = pick_variable(f)
    a, b = parse(p["lower"]), parse(p["upper"])
    g = Graph(x, *window([a, b], pad=0.3))
    g.curve(f, fx(x, f), "f")
    g.vline(a)
    g.vline(b)
    g.point(a, f.subs(x, a), "start")
    g.point(b, f.subs(x, b), "end")
    return g


def g_taylor(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    if not single_var(expr, x):
        return None
    a = parse(p.get("center") or "0")
    n = int(p.get("order") or 5)
    poly = series(expr, x, a, n + 1).removeO()
    lo, hi = window(center=a, half=4)
    g = Graph(x, lo, hi)
    g.curve(expr, fx(x, expr), "f")
    g.curve(poly, rf"P_{{{n}}}({latex(x)})", "approx")
    g.point(a, expr.subs(x, a), "center")
    return g


GRAPHS = {
    "evaluate": g_evaluate,
    "solve": g_solve,
    "derivative": g_derivative,
    "tangent": g_tangent,
    "limit": g_limit,
    "extrema": g_extrema,
    "integral": g_integral,
    "area": g_area,
    "volume": g_volume,
    "arclength": g_arclength,
    "taylor": g_taylor,
}
