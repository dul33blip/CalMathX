"""Applications: tangent lines/planes, extrema, Lagrange multipliers, area, volume, arc length."""
from sympy import (
    Symbol, diff, solve, sqrt, pi, S, oo, Interval, nsimplify, Rational, fraction, together,
    singularities, Abs, simplify,
)

from common import (
    Steps, SolverError, latex, parse, parse_equation, parse_symbol, pick_variable, tidy, result,
    approx, is_finite_number,
)
from derivatives import diff_steps, parse_point
from integrals import definite_steps

X, Y = Symbol("x"), Symbol("y")


def _vars(expr):
    order = {"x": 0, "y": 1, "z": 2}
    return sorted(expr.free_symbols, key=lambda s: (order.get(s.name, 3), s.name))


def _real(sols):
    return [s for s in sols if all(v.is_real is not False for v in (s.values() if isinstance(s, dict) else [s]))]


# ------------------------------------------------------------------ Tangents

def tangent(p):
    expr = parse(p["expr"])
    vs = _vars(expr)
    steps = Steps()
    if len(vs) <= 1:
        x = vs[0] if vs else X
        a = parse(p["point"].split("=")[-1])
        fa = tidy(expr.subs(x, a))
        steps.add("The tangent line at $x = a$ is $y = f(a) + f'(a)(x - a)$.")
        steps.add("### Find the point on the curve",
                  f"f({latex(a)}) = {latex(fa)}")
        steps.add("### Find the slope $f'(x)$")
        fp = tidy(diff_steps(expr, x, steps, 1))
        m = tidy(fp.subs(x, a))
        steps.add("Evaluate the slope at the point.", f"f'({latex(a)}) = {latex(m)}")
        line = tidy(fa + m * (x - a))
        steps.add("Point-slope form, then simplify.",
                  rf"y = {latex(fa)} + {latex(m)}\left({latex(x - a)}\right) \;\Rightarrow\; y = {latex(line)}")
        return result(f"y = {latex(line)}", steps)

    if len(vs) != 2:
        raise SolverError("Tangent planes are supported for z = f(x, y).")
    x, y = vs
    pt = parse_point(p["point"], expr)
    a, b = pt[x], pt[y]
    f0 = tidy(expr.subs(pt))
    steps.add(r"The tangent plane to $z = f(x,y)$ at $(a, b)$ is "
              r"$z = f(a,b) + f_x(a,b)(x - a) + f_y(a,b)(y - b)$.")
    steps.add("Value at the point:", f"f({latex(a)}, {latex(b)}) = {latex(f0)}")
    fx, fy = tidy(diff(expr, x)), tidy(diff(expr, y))
    fxa, fya = tidy(fx.subs(pt)), tidy(fy.subs(pt))
    steps.add("Partial derivatives:", rf"f_x = {latex(fx)} \to {latex(fxa)}, \qquad f_y = {latex(fy)} \to {latex(fya)}")
    plane = tidy(f0 + fxa * (x - a) + fya * (y - b))
    steps.add("Substitute and simplify.", f"z = {latex(plane)}")
    return result(f"z = {latex(plane)}", steps)


# ------------------------------------------------------------------ Extrema

def _classify_1d(f, x, c, fpp, steps):
    v = tidy(fpp.subs(x, c))
    if v.is_positive:
        steps.add(f"$f''({latex(c)}) = {latex(v)} > 0$ → concave up → **local minimum**.", None, 1)
        return "local min"
    if v.is_negative:
        steps.add(f"$f''({latex(c)}) = {latex(v)} < 0$ → concave down → **local maximum**.", None, 1)
        return "local max"
    fp = diff(f, x)
    h = Rational(1, 1000)
    l, r = fp.subs(x, c - h), fp.subs(x, c + h)
    kind = "local min" if l < 0 < r else "local max" if l > 0 > r else "neither"
    steps.add(f"$f''({latex(c)}) = 0$ (test inconclusive). First-derivative test: $f'$ changes from "
              f"{'−' if l < 0 else '+'} to {'−' if r < 0 else '+'} → **{kind}**.", None, 1)
    return kind


def extrema(p):
    expr = parse(p["expr"])
    vs = _vars(expr)
    steps = Steps()
    if len(vs) <= 1:
        return _extrema_1d(expr, vs[0] if vs else X, p, steps)
    if len(vs) == 2:
        return _extrema_2d(expr, vs, steps)
    raise SolverError("Extrema supports functions of one or two variables.")


def _extrema_1d(f, x, p, steps):
    interval = None
    if p.get("lower") not in (None, "") and p.get("upper") not in (None, ""):
        interval = (parse(p["lower"]), parse(p["upper"]))
    steps.add("### Step 1: find $f'(x)$")
    fp = tidy(diff_steps(f, x, steps, 1))
    steps.add(f"$f'({latex(x)}) = {latex(fp)}$")
    steps.add("### Step 2: find critical points ($f'(x) = 0$ or undefined)")
    crit = [c for c in solve(fp, x) if c.is_real]
    den = fraction(together(fp))[1]
    undefined = [c for c in solve(den, x) if c.is_real and is_finite_number(f.subs(x, c))] if den.has(x) else []
    crit = sorted(set(crit + undefined), key=lambda c: float(c))
    if interval:
        crit = [c for c in crit if interval[0] <= c <= interval[1]]
    steps.add(f"Solve ${latex(fp)} = 0$:" if crit else "There are no critical points" + (" in the interval." if interval else "."),
              ", ".join(f"{latex(x)} = {latex(c)}" for c in crit) or None)
    if undefined:
        steps.add(f"$f'$ is undefined at ${', '.join(latex(u) for u in undefined)}$ (also critical).")

    summary = []
    if crit:
        steps.add("### Step 3: second derivative test")
        fpp = tidy(diff(fp, x))
        steps.add(f"$f''({latex(x)}) = {latex(fpp)}$")
        for c in crit:
            kind = _classify_1d(f, x, c, fpp, steps)
            val = tidy(f.subs(x, c))
            summary.append((c, val, kind))

        # Increasing / decreasing intervals
        pts = [-oo] + crit + [oo] if not interval else [interval[0]] + crit + [interval[1]]
        rows = []
        for lo, hi in zip(pts, pts[1:]):
            test = (hi - 1 if lo == -oo else lo + 1 if hi == oo else (lo + hi) / 2)
            s = fp.subs(x, test)
            if s.is_number and s != 0:
                rows.append(rf"({latex(lo)}, {latex(hi)}): \ f' {'> 0' if s > 0 else '< 0'} \Rightarrow "
                            rf"\text{{{'increasing' if s > 0 else 'decreasing'}}}")
        if rows:
            steps.add("### Increasing / decreasing (test a point in each interval)", r"\\ ".join(rows))

    if interval:
        a, b = interval
        steps.add("### Absolute extrema on the closed interval: compare $f$ at critical points and endpoints")
        cands = [(a, tidy(f.subs(x, a)))] + [(c, v) for c, v, _ in summary] + [(b, tidy(f.subs(x, b)))]
        for c, v in cands:
            steps.add("", f"f({latex(c)}) = {latex(v)}" + (rf" \approx {approx(v)}" if approx(v) and approx(v) != latex(v) else ""), 1)
        mx = max(cands, key=lambda t: float(t[1]))
        mn = min(cands, key=lambda t: float(t[1]))
        steps.add(f"**Absolute max** ${latex(mx[1])}$ at $x = {latex(mx[0])}$; "
                  f"**absolute min** ${latex(mn[1])}$ at $x = {latex(mn[0])}$.")
        return result(rf"\max = {latex(mx[1])} \text{{ at }} x={latex(mx[0])},\quad "
                      rf"\min = {latex(mn[1])} \text{{ at }} x={latex(mn[0])}", steps)

    if not summary:
        return result(r"\text{No local extrema}", steps)
    parts = [rf"\text{{{k}}} \text{{ at }} ({latex(c)}, {latex(v)})" for c, v, k in summary]
    return result(r",\quad ".join(parts), steps)


def _extrema_2d(f, vs, steps):
    x, y = vs
    fx, fy = tidy(diff(f, x)), tidy(diff(f, y))
    steps.add("### Step 1: partial derivatives", rf"f_{latex(x)} = {latex(fx)}, \qquad f_{latex(y)} = {latex(fy)}")
    steps.add(f"### Step 2: critical points — solve $f_{latex(x)} = 0$ and $f_{latex(y)} = 0$ together")
    sols = _real(solve([fx, fy], [x, y], dict=True))
    if not sols:
        steps.add("No real critical points.")
        return result(r"\text{No critical points}", steps)
    steps.add("Critical points:", ", ".join(f"({latex(s[x])}, {latex(s[y])})" for s in sols))
    fxx, fyy, fxy = tidy(diff(fx, x)), tidy(diff(fy, y)), tidy(diff(fx, y))
    D = tidy(fxx * fyy - fxy ** 2)
    steps.add("### Step 3: second derivative test with $D = f_{xx}f_{yy} - (f_{xy})^2$",
              rf"f_{{xx}} = {latex(fxx)},\ f_{{yy}} = {latex(fyy)},\ f_{{xy}} = {latex(fxy)},\ D = {latex(D)}")
    parts = []
    for s in sols:
        d, a = tidy(D.subs(s)), tidy(fxx.subs(s))
        val = tidy(f.subs(s))
        if d > 0:
            kind = "local min" if a > 0 else "local max"
            why = f"$D > 0$ and $f_{{xx}} {'> 0' if a > 0 else '< 0'}$"
        elif d < 0:
            kind, why = "saddle point", "$D < 0$"
        else:
            kind, why = "inconclusive", "$D = 0$"
        steps.add(f"At $({latex(s[x])}, {latex(s[y])})$: $D = {latex(d)}$, $f_{{xx}} = {latex(a)}$. "
                  f"{why} → **{kind}**, $f = {latex(val)}$.", None, 1)
        parts.append(rf"\text{{{kind}}} \text{{ at }} ({latex(s[x])}, {latex(s[y])}, {latex(val)})")
    return result(r",\quad ".join(parts), steps)


def lagrange(p):
    f = parse(p["expr"])
    eq = parse_equation(p["constraint"])
    g = eq.lhs - eq.rhs
    vs = sorted((f.free_symbols | g.free_symbols), key=lambda s: ({"x": 0, "y": 1, "z": 2}.get(s.name, 3), s.name))
    lam = Symbol("lambda")
    steps = Steps()
    steps.add(r"**Lagrange multipliers:** at an extremum on the constraint, $\nabla f = \lambda \nabla g$.",
              rf"f = {latex(f)}, \qquad g = {latex(g)} = 0")
    eqs = []
    for v in vs:
        fv, gv = tidy(diff(f, v)), tidy(diff(g, v))
        eqs.append(fv - lam * gv)
        steps.add(f"${latex(v)}$-component:", rf"{latex(fv)} = \lambda \left({latex(gv)}\right)", 1)
    eqs.append(g)
    steps.add("Together with the constraint:", f"{latex(eq.lhs)} = {latex(eq.rhs)}", 1)
    steps.add("Solve this system of equations.")
    sols = _real(solve(eqs, vs + [lam], dict=True))
    if not sols:
        raise SolverError("No real solutions to the Lagrange system were found.")
    vals = []
    for s in sols:
        v = tidy(f.subs(s))
        vals.append((s, v))
        steps.add("", "(" + ", ".join(latex(s.get(v_, v_)) for v_ in vs) + rf"),\ \lambda = {latex(s.get(lam, '?'))}"
                  rf" \Rightarrow f = {latex(v)}", 1)
    numeric = [t for t in vals if t[1].is_number]
    pt = lambda s: "(" + ", ".join(latex(s[v_]) for v_ in vs) + ")"
    if len({t[1] for t in numeric}) == 1:
        s0, v0 = numeric[0]
        kind = _classify_single(f, g, vs, s0, v0)
        steps.add(f"There is one candidate value, $f = {latex(v0)}$. Comparing with another point on the "
                  f"constraint shows it is a **{kind}**.")
        return result(rf"\{'max' if kind == 'maximum' else 'min'} = {latex(v0)} \text{{ at }} {pt(s0)}", steps)
    mx = max(numeric, key=lambda t: float(t[1]))
    mn = min(numeric, key=lambda t: float(t[1]))
    steps.add(f"Compare the values: **maximum** ${latex(mx[1])}$ at ${pt(mx[0])}$, "
              f"**minimum** ${latex(mn[1])}$ at ${pt(mn[0])}$.")
    return result(rf"\max = {latex(mx[1])} \text{{ at }} {pt(mx[0])},\quad \min = {latex(mn[1])} \text{{ at }} {pt(mn[0])}", steps)


def _classify_single(f, g, vs, s0, v0):
    """Nudge the first variable, solve the constraint for the last, and compare f."""
    first, last = vs[0], vs[-1]
    for delta in (Rational(1, 2), Rational(-1, 2), 1):
        trial = {v: s0[v] for v in vs[1:-1]}
        trial[first] = s0[first] + delta
        for sol in solve(g.subs(trial), last):
            if sol.is_real:
                trial[last] = sol
                other = f.subs(trial)
                if other.is_number and other != v0:
                    return "maximum" if other < v0 else "minimum"
    return "extremum"


# ------------------------------------------------------------------ Calc 2 applications

def area(p):
    f, g = parse(p["expr"]), parse(p.get("expr2") or "0")
    x = pick_variable(f + g + Symbol("x"), None)
    steps = Steps()
    if p.get("lower") not in (None, "") and p.get("upper") not in (None, ""):
        a, b = parse(p["lower"]), parse(p["upper"])
    else:
        pts = sorted([s for s in solve(f - g, x) if s.is_real], key=float)
        if len(pts) < 2:
            raise SolverError("The curves don't enclose a region; please enter bounds.")
        a, b = pts[0], pts[-1]
        steps.add("Find where the curves intersect.", f"{latex(f)} = {latex(g)} \\Rightarrow "
                  + ", ".join(f"{latex(x)} = {latex(s)}" for s in pts))
    mid = (a + b) / 2
    top, bot = (f, g) if (f - g).subs(x, mid) >= 0 else (g, f)
    steps.add(rf"Area $= \int_a^b (\text{{top}} - \text{{bottom}})\,dx$. Testing $x = {latex(mid)}$ shows "
              f"${latex(top)}$ is on top.", rf"A = \int_{{{latex(a)}}}^{{{latex(b)}}} \left({latex(top - bot)}\right)dx")
    val = definite_steps(tidy(top - bot), x, a, b, steps, 1)
    steps.add("**Area:**", f"A = {latex(val)}")
    return result(latex(val), steps, approx(val))


def volume(p):
    f = parse(p["expr"])
    g = parse(p.get("expr2") or "0")
    x = pick_variable(f + g + Symbol("x"), None)
    a, b = parse(p["lower"]), parse(p["upper"])
    method = p.get("method") or "disk"
    axis = p.get("axis") or "x"
    steps = Steps()
    if method == "shell":
        if axis != "y":
            raise SolverError("With y = f(x), the shell method is for rotation about the y-axis.")
        h = tidy(f - g)
        steps.add(r"**Shell method** about the $y$-axis: $V = 2\pi \int_a^b (\text{radius})(\text{height})\,dx$ "
                  f"with radius $= {latex(x)}$ and height $= {latex(h)}$.",
                  rf"V = 2\pi \int_{{{latex(a)}}}^{{{latex(b)}}} {latex(x)}\left({latex(h)}\right)dx")
        integrand = tidy(x * h)
        val = tidy(2 * pi * definite_steps(integrand, x, a, b, steps, 1))
        steps.add(r"Multiply by $2\pi$.", f"V = {latex(val)}")
    else:
        if axis != "x":
            raise SolverError("With y = f(x), the disk/washer method is for rotation about the x-axis.")
        if g == 0:
            steps.add(r"**Disk method** about the $x$-axis: $V = \pi \int_a^b [f(x)]^2\,dx$.",
                      rf"V = \pi \int_{{{latex(a)}}}^{{{latex(b)}}} \left({latex(f)}\right)^2 dx")
        else:
            steps.add(r"**Washer method** about the $x$-axis: $V = \pi \int_a^b (R^2 - r^2)\,dx$ "
                      f"with outer radius $R = {latex(f)}$, inner radius $r = {latex(g)}$.",
                      rf"V = \pi \int_{{{latex(a)}}}^{{{latex(b)}}} \left(({latex(f)})^2 - ({latex(g)})^2\right) dx")
        integrand = tidy(f ** 2 - g ** 2)
        val = tidy(pi * definite_steps(integrand, x, a, b, steps, 1))
        steps.add(r"Multiply by $\pi$.", f"V = {latex(val)}")
    return result(latex(val), steps, approx(val))


def arc_length(p):
    f = parse(p["expr"])
    x = pick_variable(f)
    a, b = parse(p["lower"]), parse(p["upper"])
    steps = Steps()
    steps.add(r"Arc length: $L = \int_a^b \sqrt{1 + [f'(x)]^2}\,dx$.")
    steps.add("### Find $f'(x)$")
    fp = tidy(diff_steps(f, x, steps, 1))
    integrand = tidy(sqrt(1 + fp ** 2))
    steps.add("Build the integrand.", rf"\sqrt{{1 + \left({latex(fp)}\right)^2}} = {latex(integrand)}")
    steps.add("### Integrate")
    val = definite_steps(integrand, x, a, b, steps, 1)
    steps.add("**Arc length:**", f"L = {latex(val)}")
    return result(latex(val), steps, approx(val))
