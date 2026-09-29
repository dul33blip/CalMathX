"""Taylor/Maclaurin polynomials and series convergence tests."""
from sympy import (
    Symbol, Sum, factorial, diff, limit, oo, zoo, nan, Abs, simplify, combsimp, Add, Mul,
    Pow, integrate, Integral, Interval, S, is_decreasing, AccumBounds, powsimp, gamma, cos, pi,
)

from common import Steps, SolverError, latex, parse, parse_symbol, pick_variable, tidy, result, approx, is_finite_number


# ---------------------------------------------------------------- Taylor series

def taylor(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    a = parse(p.get("center") or "0")
    n = int(p.get("order") or 5)
    if not 0 <= n <= 15:
        raise SolverError("Order must be between 0 and 15.")
    steps = Steps()
    kind = "Maclaurin" if a == 0 else "Taylor"
    xa = latex(x) if a == 0 else rf"\left({latex(x - a)}\right)"
    steps.add(f"The degree-${n}$ **{kind} polynomial** centered at ${latex(x)} = {latex(a)}$ is",
              rf"P_{{{n}}}({latex(x)}) = \sum_{{k=0}}^{{{n}}} \frac{{f^{{(k)}}({latex(a)})}}{{k!}}{xa}^k")
    steps.add("Compute each derivative and evaluate it at the center.")
    terms = []
    current = expr
    for k in range(n + 1):
        if k > 0:
            current = tidy(diff(current, x))
        val = tidy(current.subs(x, a))
        if not is_finite_number(val) and val.is_number:
            raise SolverError(f"f^({k})({a}) is undefined, so there is no Taylor series centered at {a}.")
        name = "f" if k == 0 else ("f" + "'" * k if k <= 3 else f"f^{{({k})}}")
        term = val / factorial(k) * (x - a) ** k
        terms.append(term)
        steps.add(f"$k = {k}$:",
                  rf"{name}({latex(x)}) = {latex(current)}, \qquad {name}({latex(a)}) = {latex(val)}"
                  rf" \;\Rightarrow\; \text{{term}} = \frac{{{latex(val)}}}{{{k}!}}{xa}^{{{k}}} = {latex(term)}", 1)
    shown = _poly_tex(terms)
    steps.add("Add the terms.", rf"P_{{{n}}}({latex(x)}) = {shown}")
    return result(shown, steps)


def _poly_tex(terms):
    """LaTeX for a sum of terms in the given order, e.g. (x-1) - (x-1)^2/2 + ..."""
    out = ""
    for t in terms:
        if t == 0:
            continue
        tex = latex(t)
        if not out:
            out = tex
        elif tex.startswith("-"):
            out += " - " + tex[1:].lstrip()
        else:
            out += " + " + tex
    return out or "0"


# ---------------------------------------------------------------- Convergence

def _sum_tex(a, n, start):
    return rf"\sum_{{{latex(n)}={latex(start)}}}^{{\infty}} {latex(a)}"


def _positive_part(a, n):
    """b_n with (-1)^n style factors removed, or None if the series isn't alternating."""
    signs = [f for f in Mul.make_args(a)
             if isinstance(f, Pow) and f.base == -1 and f.exp.has(n)]
    if signs:
        return Mul(*[f for f in Mul.make_args(a) if f not in signs]), signs[0]
    cosf = [f for f in Mul.make_args(a) if f == cos(pi * n)]
    if cosf:
        return Mul(*[f for f in Mul.make_args(a) if f not in cosf]), cosf[0]
    return None, None


def _positive_tests(a, n, start, steps, depth):
    """Decide convergence of a series with (eventually) positive terms. Returns True/False/None."""
    ratio = simplify(combsimp(powsimp(a.subs(n, n + 1) / a)))

    # Geometric
    if not ratio.has(n) and ratio != 1:
        r = ratio
        steps.add(f"**Geometric series:** consecutive terms have constant ratio $r = {latex(r)}$.",
                  rf"\frac{{a_{{n+1}}}}{{a_n}} = {latex(r)}", depth)
        if Abs(r) < 1:
            first = a.subs(n, start)
            total = tidy(first / (1 - r))
            steps.add(f"Since $|r| < 1$ the series **converges** to $\\frac{{a_{{{latex(start)}}}}}{{1 - r}}$.",
                      rf"\frac{{{latex(first)}}}{{1 - {latex(r)}}} = {latex(total)}", depth)
            return True, total
        steps.add("Since $|r| \\ge 1$ the series **diverges**.", None, depth)
        return False, None

    # p-series (c / n^p)
    c, rest = a.as_independent(n, as_Add=False)
    if isinstance(rest, Pow) and rest.base == n and not rest.exp.has(n):
        pexp = -rest.exp
        steps.add(f"**p-series:** the terms have the form $\\frac{{c}}{{n^p}}$ with $p = {latex(pexp)}$.", None, depth)
        if pexp > 1:
            steps.add("Since $p > 1$, the series **converges**.", None, depth)
            return True, None
        steps.add("Since $p \\le 1$, the series **diverges**.", None, depth)
        return False, None

    # Ratio test for factorials/exponentials
    if a.has(factorial, gamma) or any(isinstance(t, Pow) and t.exp.has(n) and not t.base.has(n)
                                     for t in a.atoms(Pow)):
        L = limit(Abs(ratio), n, oo)
        steps.add(r"**Ratio test:** compute $L = \lim_{n\to\infty} \left|\frac{a_{n+1}}{a_n}\right|$.",
                  rf"\left|\frac{{a_{{n+1}}}}{{a_n}}\right| = {latex(Abs(ratio))} \;\to\; L = {latex(L)}", depth)
        if L.is_number and L < 1:
            steps.add("Since $L < 1$, the series **converges** (absolutely).", None, depth)
            return True, None
        if L.is_number and L > 1 or L == oo:
            steps.add("Since $L > 1$, the series **diverges**.", None, depth)
            return False, None
        steps.add("$L = 1$, so the ratio test is inconclusive. Try another test.", None, depth)

    # Limit comparison with a p-series
    try:
        from sympy import log as ln
        p_eff = -limit(ln(Abs(a)) / ln(n), n, oo)
        if p_eff.is_number and p_eff.is_finite and p_eff.is_rational:
            b = 1 / n ** p_eff
            L = limit(a / b, n, oo)
            if L.is_number and L.is_finite and L > 0:
                verdict = p_eff > 1
                steps.add(f"**Limit comparison test** with the p-series $b_n = {latex(b)}$:",
                          rf"\lim_{{n\to\infty}} \frac{{a_n}}{{b_n}} = {latex(L)}", depth)
                steps.add(f"The limit is finite and positive, so both series behave the same. "
                          f"$\\sum {latex(b)}$ is a p-series with $p = {latex(p_eff)}$, which "
                          f"{'converges' if verdict else 'diverges'}, so our series **{'converges' if verdict else 'diverges'}**.",
                          None, depth)
                return verdict, None
    except Exception:
        pass

    # Integral test
    t = Symbol("x", positive=True)
    f = a.subs(n, t)
    try:
        dec = is_decreasing(f, Interval(max(start, 2), oo))
    except Exception:
        dec = None
    if dec:
        val = integrate(f, (t, start, oo))
        if not val.has(Integral):
            conv = is_finite_number(val)
            steps.add(f"**Integral test:** $f(x) = {latex(f)}$ is positive and decreasing, so compare with the improper integral.",
                      rf"\int_{{{latex(start)}}}^{{\infty}} {latex(f)}\,dx = {latex(val)}", depth)
            steps.add(f"The integral {'converges' if conv else 'diverges'}, so the series "
                      f"**{'converges' if conv else 'diverges'}**.", None, depth)
            return conv, None

    return None, None


def _term_limit(a, n):
    """lim a_n, falling back to |a_n| (SymPy can't always take limits of (-1)^n terms)."""
    try:
        return limit(a, n, oo)
    except Exception:
        La = limit(Abs(a), n, oo)
        return S(0) if La == 0 else AccumBounds(-La, La)


def convergence(p):
    a = parse(p["term"])
    n = parse_symbol(p.get("var") or "n", "n")
    if n not in a.free_symbols and a.free_symbols:
        n = pick_variable(a, None, "n")
    start = parse(p.get("start") or "1")
    steps = Steps()
    steps.add("Determine whether the series converges:", _sum_tex(a, n, start))

    # nth-term test
    L = _term_limit(a, n)
    steps.add(r"**Divergence (nth-term) test:** find $\lim_{n\to\infty} a_n$.",
              rf"\lim_{{n\to\infty}} {latex(a)} = {latex(L) if not L.has(AccumBounds) else r'\text{does not exist}'}")
    if L != 0:
        steps.add("The terms don't approach $0$, so the series **diverges**.")
        return result(r"\text{Diverges}", steps)
    steps.add("The terms approach $0$, so this test is inconclusive. Keep going.")

    verdict, total = None, None
    b, sign = _positive_part(a, n)
    if b is not None:
        steps.add(f"### Alternating series: $a_n = {latex(sign)} \\cdot b_n$ with $b_n = {latex(b)}$")
        steps.add("First check **absolute convergence**, i.e. whether $\\sum b_n$ converges.")
        abs_conv, _ = _positive_tests(b, n, start, steps, 1)
        if abs_conv:
            steps.add("$\\sum |a_n|$ converges, so the series **converges absolutely**.")
            verdict, label = True, r"\text{Converges absolutely}"
        else:
            t = Symbol("x", positive=True)
            try:
                dec = is_decreasing(b.subs(n, t), Interval(max(start, 1), oo))
            except Exception:
                dec = None
            steps.add(r"**Alternating series test:** need $b_n \to 0$ and $b_n$ eventually decreasing.",
                      rf"\lim_{{n\to\infty}} {latex(b)} = {latex(limit(b, n, oo))}, \quad "
                      rf"b_n \text{{ decreasing: }} {'yes' if dec else 'unclear'}")
            if limit(b, n, oo) == 0 and dec:
                steps.add("Both conditions hold, so the series **converges conditionally**."
                          if abs_conv is False else "Both conditions hold, so the series **converges**.")
                verdict = True
                label = r"\text{Converges conditionally}" if abs_conv is False else r"\text{Converges}"
            else:
                verdict, label = None, None
    else:
        verdict, total = _positive_tests(a, n, start, steps, 0)
        label = {True: r"\text{Converges}", False: r"\text{Diverges}"}.get(verdict)

    if verdict is None:
        conv = Sum(a, (n, start, oo)).is_convergent()
        steps.add("The standard tests were inconclusive here, so a comparison-based analysis was used.",
                  rf"\text{{Result: }} \text{{{'converges' if conv else 'diverges'}}}")
        verdict = bool(conv)
        label = r"\text{Converges}" if conv else r"\text{Diverges}"

    extra = {}
    if verdict:
        if total is None:
            try:
                s = Sum(a, (n, start, oo)).doit()
                if not s.has(Sum) and is_finite_number(s):
                    total = tidy(s)
            except Exception:
                pass
        if total is not None:
            steps.add("The exact sum is:", f"{_sum_tex(a, n, start)} = {latex(total)}")
            label += rf",\ \ {_sum_tex(a, n, start)} = {latex(total)}"
            extra["approx"] = approx(total)
    return result(label, steps, extra.get("approx"))
