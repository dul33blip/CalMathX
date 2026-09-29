"""Everyday math: evaluate/simplify expressions and solve equations with steps."""
from sympy import (
    Poly, factor, expand, simplify, solve, sqrt, together, fraction, Eq, S, I, N,
    factor_list, degree, nsimplify,
)
from sympy.parsing.sympy_parser import parse_expr

from common import (
    Steps, SolverError, latex, parse, parse_equation, pick_variable, tidy, result, approx,
    LOCALS, TRANSFORMS, _clean,
)


def _unevaluated(text):
    try:
        return latex(parse_expr(_clean(text), local_dict=dict(LOCALS), transformations=TRANSFORMS, evaluate=False))
    except Exception:
        return None


def evaluate(p):
    raw = p["expr"]
    expr = parse(raw)
    steps = Steps()
    shown = _unevaluated(raw) or latex(expr)
    steps.add("Interpret the input:", shown)
    if expr.is_number:
        exact = tidy(expr)
        steps.add("Evaluate exactly.", f"{shown} = {latex(exact)}")
        dec = approx(exact, 15)
        if dec and dec != latex(exact):
            steps.add("Decimal approximation:", rf"\approx {dec}")
        return result(latex(exact), steps, dec)

    forms = []
    for label, fn in (("Expanded", expand), ("Factored", factor), ("Simplified", simplify)):
        try:
            f = fn(expr)
            if all(f != g for _, g in forms):
                forms.append((label, f))
        except Exception:
            pass
    for label, f in forms:
        steps.add(f"**{label} form:**", latex(f))
    best = tidy(expr)
    return result(latex(best), steps, None,
                  {"alternates": [{"label": l, "latex": latex(f)} for l, f in forms]})


def _solve_poly(F, x, steps, depth=0):
    """Solve polynomial F = 0 with steps. Returns list of solutions."""
    P = Poly(F, x)
    d = P.degree()
    if d == 0:
        raise SolverError("After simplifying there's no variable left to solve for.")
    if d == 1:
        a, b = P.all_coeffs()
        sol = -b / a
        steps.add(f"This is linear. Isolate ${latex(x)}$.",
                  rf"{latex(a)}{latex(x)} = {latex(-b)} \;\Rightarrow\; {latex(x)} = {latex(sol)}", depth)
        return [sol]
    if d == 2:
        a, b, c = P.all_coeffs()
        fl = factor_list(F, x)
        linear = [f for f, _ in fl[1] if Poly(f, x).degree() == 1]
        if len(linear) >= 1 and sum(Poly(f, x).degree() * m for f, m in fl[1]) == 2 and len(linear) == len(fl[1]):
            steps.add("**Factor** the quadratic.", f"{latex(factor(F))} = 0", depth)
            sols = []
            for f, _ in fl[1]:
                s = solve(f, x)[0]
                steps.add("**Zero product property:** set each factor to zero.",
                          rf"{latex(f)} = 0 \;\Rightarrow\; {latex(x)} = {latex(s)}", depth + 1)
                sols.append(s)
            return list(dict.fromkeys(sols))
        disc = b ** 2 - 4 * a * c
        steps.add(f"It doesn't factor nicely, so use the **quadratic formula** with "
                  f"$a = {latex(a)}$, $b = {latex(b)}$, $c = {latex(c)}$.",
                  rf"{latex(x)} = \frac{{-b \pm \sqrt{{b^2 - 4ac}}}}{{2a}}", depth)
        steps.add("Compute the discriminant.",
                  rf"b^2 - 4ac = ({latex(b)})^2 - 4({latex(a)})({latex(c)}) = {latex(disc)}", depth)
        if disc < 0:
            steps.add("The discriminant is negative, so the solutions are complex (no real solutions).", None, depth)
        sols = [tidy((-b + sqrt(disc)) / (2 * a)), tidy((-b - sqrt(disc)) / (2 * a))]
        steps.add("Substitute into the formula.",
                  rf"{latex(x)} = \frac{{{latex(-b)} \pm \sqrt{{{latex(disc)}}}}}{{{latex(2 * a)}}}", depth)
        return sols

    fl = factor_list(F, x)
    if len(fl[1]) > 1 or fl[1][0][1] > 1:
        steps.add("**Factor** the polynomial.", f"{latex(factor(F))} = 0", depth)
        steps.add("Set each factor equal to zero and solve.", None, depth)
        sols = []
        for f, _ in fl[1]:
            steps.add(f"Solve ${latex(f)} = 0$:", None, depth + 1)
            sols += _solve_poly(f, x, steps, depth + 2)
        return list(dict.fromkeys(sols))
    sols = solve(F, x)
    steps.add(f"This degree-{d} polynomial doesn't factor over the rationals; solve it algebraically/numerically.",
              ", ".join(f"{latex(x)} = {latex(s)}" for s in sols), depth)
    return sols


def solve_equation(p):
    eq = parse_equation(p["equation"])
    F0 = eq.lhs - eq.rhs
    x = pick_variable(F0, p.get("var"))
    steps = Steps()
    steps.add("Solve the equation:", f"{latex(eq.lhs)} = {latex(eq.rhs)}")
    if eq.rhs != 0:
        F = expand(F0) if F0.is_polynomial(x) else F0
        steps.add("Move everything to one side.", f"{latex(F)} = 0")
    else:
        F = F0

    num, den = fraction(together(F))
    excluded = []
    if den.has(x):
        excluded = solve(den, x)
        steps.add("Combine into one fraction. A fraction is zero exactly when its numerator is zero "
                  "(and the denominator isn't).",
                  rf"\frac{{{latex(num)}}}{{{latex(den)}}} = 0 \;\Rightarrow\; {latex(num)} = 0", )
        F = expand(num)

    if F.is_polynomial(x):
        sols = _solve_poly(F, x, steps)
    else:
        sols = solve(F, x)
        if not sols:
            raise SolverError("No solutions were found.")
        steps.add("Solve using inverse operations / identities.",
                  r",\quad ".join(f"{latex(x)} = {latex(s)}" for s in sols))

    if excluded:
        bad = [s for s in sols if s in excluded]
        if bad:
            steps.add(f"Reject ${', '.join(latex(b) for b in bad)}$: it makes the denominator zero.")
        sols = [s for s in sols if s not in excluded]

    real = [s for s in sols if s.is_real is not False]
    cplx = [s for s in sols if s.is_real is False]
    if not sols:
        steps.add("There are **no solutions**.")
        return result(r"\text{No solution}", steps)
    if cplx and real:
        steps.add(f"Complex solutions: ${', '.join(latex(c) for c in cplx)}$.")
    shown = real or cplx
    ans = r",\quad ".join(f"{latex(x)} = {latex(s)}" for s in shown)
    decs = [approx(s) for s in shown]
    approx_str = ", ".join(f"{x} ≈ {d}" for d in decs if d) if any(
        d and d != latex(s) for d, s in zip(decs, shown)) else None
    steps.add("**Solution(s):**", ans)
    if trig_note(F, x):
        steps.add("For trig equations these are the principal solutions; add multiples of the period "
                  "(e.g. $+2\\pi k$) for all solutions.")
    return result(ans, steps, approx_str)


def trig_note(F, x):
    from sympy import sin, cos, tan, sec, csc, cot
    return F.has(sin, cos, tan, sec, csc, cot)
