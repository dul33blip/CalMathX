"""Derivatives with human-style steps: sum/constant/product/quotient/power/chain rules."""
from sympy import (
    Add, Mul, Pow, Symbol, E, diff, sin, cos, tan, sec, csc, cot, exp, log, sqrt,
    asin, acos, atan, acot, asec, acsc, sinh, cosh, tanh, Abs, fraction, Integer,
    Rational, Derivative,
)

from common import (
    Steps, SolverError, latex, parse, parse_equation, parse_symbol, pick_variable,
    tidy, result, approx,
)

_u = Symbol("u")

# Derivative of the outer function f(u) with respect to u
OUTER = {
    sin: lambda u: cos(u),
    cos: lambda u: -sin(u),
    tan: lambda u: sec(u) ** 2,
    sec: lambda u: sec(u) * tan(u),
    csc: lambda u: -csc(u) * cot(u),
    cot: lambda u: -csc(u) ** 2,
    exp: lambda u: exp(u),
    log: lambda u: 1 / u,
    asin: lambda u: 1 / sqrt(1 - u ** 2),
    acos: lambda u: -1 / sqrt(1 - u ** 2),
    atan: lambda u: 1 / (1 + u ** 2),
    acot: lambda u: -1 / (1 + u ** 2),
    asec: lambda u: 1 / (Abs(u) * sqrt(u ** 2 - 1)),
    acsc: lambda u: -1 / (Abs(u) * sqrt(u ** 2 - 1)),
    sinh: lambda u: cosh(u),
    cosh: lambda u: sinh(u),
    tanh: lambda u: 1 - tanh(u) ** 2,
    Abs: lambda u: u / Abs(u),
}


def D(x, e, partial=False):
    d = r"\partial" if partial else "d"
    return rf"\frac{{{d}}}{{{d} {latex(x)}}}\left[{latex(e)}\right]"


def diff_steps(expr, x, steps, depth=0, partial=False):
    """Differentiate expr w.r.t. x, appending explanation to steps. Returns the derivative."""
    Dx = lambda e: D(x, e, partial)
    xs = f"${latex(x)}$"
    v, d = latex(x), (r"\partial" if partial else "d")

    def add(text, math=None, dep=depth):
        # Rule formulas are written with x; show them in terms of the actual variable
        def fix(s):
            if not s:
                return s
            return (s.replace(r"\frac{d}{dx}", rf"\frac{{{d}}}{{{d} {v}}}")
                     .replace("x^n", f"{v}^n").replace("x^{n-1}", f"{v}^{{n-1}}")
                     .replace("a^x", f"a^{{{v}}}"))
        steps.add(fix(text), fix(math), dep)

    if not expr.has(x):
        why = "is constant with respect to" if not partial else "does not contain"
        add(f"${latex(expr)}$ {why} {xs}, so its derivative is $0$.", f"{Dx(expr)} = 0", depth)
        return Integer(0)

    if expr == x:
        add(f"The derivative of {xs} with respect to itself is $1$.", f"{Dx(expr)} = 1", depth)
        return Integer(1)

    if isinstance(expr, Add):
        terms = expr.as_ordered_terms()
        add("**Sum rule:** differentiate each term separately.",
                  f"{Dx(expr)} = " + " + ".join(Dx(t) for t in terms), depth)
        parts = [diff_steps(t, x, steps, depth + 1, partial) for t in terms]
        res = Add(*parts)
        add("Add the results together.", f"{Dx(expr)} = {latex(res)}", depth)
        return res

    if isinstance(expr, Mul):
        coeff, rest = expr.as_independent(x, as_Add=False)
        if coeff != 1:
            add(f"**Constant multiple rule:** pull the constant ${latex(coeff)}$ out front.",
                      f"{Dx(expr)} = {latex(coeff)} \\cdot {Dx(rest)}", depth)
            inner = diff_steps(rest, x, steps, depth + 1, partial)
            res = coeff * inner
            add("Multiply by the constant.", f"{Dx(expr)} = {latex(res)}", depth)
            return res

        num, den = fraction(expr)
        if den != 1 and den.has(x) and num.has(x):
            add(
                f"**Quotient rule:** with $f = {latex(num)}$ and $g = {latex(den)}$,",
                r"\frac{d}{dx}\left[\frac{f}{g}\right] = \frac{f'g - fg'}{g^2}", depth)
            add(f"Find $f'$, the derivative of the numerator:", None, depth + 1)
            fp = diff_steps(num, x, steps, depth + 2, partial)
            add(f"Find $g'$, the derivative of the denominator:", None, depth + 1)
            gp = diff_steps(den, x, steps, depth + 2, partial)
            res = (fp * den - num * gp) / den ** 2
            add(
                "Substitute into the quotient rule.",
                rf"{Dx(expr)} = \frac{{\left({latex(fp)}\right)\left({latex(den)}\right) - "
                rf"\left({latex(num)}\right)\left({latex(gp)}\right)}}{{\left({latex(den)}\right)^2}}",
                depth)
            return res

        factors = expr.as_ordered_factors()
        f, g = factors[0], Mul(*factors[1:])
        add(f"**Product rule:** with $f = {latex(f)}$ and $g = {latex(g)}$,",
                  r"\frac{d}{dx}\left[f g\right] = f' g + f g'", depth)
        add("Find $f'$:", None, depth + 1)
        fp = diff_steps(f, x, steps, depth + 2, partial)
        add("Find $g'$:", None, depth + 1)
        gp = diff_steps(g, x, steps, depth + 2, partial)
        res = fp * g + f * gp
        add("Substitute into the product rule.",
                  rf"{Dx(expr)} = \left({latex(fp)}\right)\left({latex(g)}\right) + "
                  rf"\left({latex(f)}\right)\left({latex(gp)}\right)", depth)
        return res

    if isinstance(expr, Pow):
        base, n = expr.as_base_exp()
        if base.has(x) and not n.has(x):
            if base == x:
                note = ""
                if n.is_negative or (n.is_Rational and not n.is_Integer):
                    note = f" (here ${latex(expr)} = {latex(x)}^{{{latex(n)}}}$)"
                res = n * x ** (n - 1)
                add(f"**Power rule:** $\\frac{{d}}{{dx}} x^n = n x^{{n-1}}$ with $n = {latex(n)}${note}.",
                    f"{Dx(expr)} = {latex(n)} \\cdot {latex(x)}^{{{latex(n - 1)}}} = {latex(res)}"
                    if n - 1 not in (0, 1) else f"{Dx(expr)} = {latex(res)}", depth)
                return res
            add(
                f"**Chain rule + power rule:** let $u = {latex(base)}$, so the expression is $u^{{{latex(n)}}}$.",
                rf"\frac{{d}}{{dx}}\left[u^{{{latex(n)}}}\right] = {latex(n)}\,u^{{{latex(n - 1)}}} \cdot u'", depth)
            add(f"Find $u'$:", None, depth + 1)
            up = diff_steps(base, x, steps, depth + 2, partial)
            res = n * base ** (n - 1) * up
            add("Substitute $u$ and $u'$ back in.", f"{Dx(expr)} = {latex(res)}", depth)
            return res

        if not base.has(x) and n.has(x):
            outer = expr * log(base)
            rule = rf"\frac{{d}}{{dx}}\left[a^u\right] = a^u \ln(a) \cdot u'"
            if n == x:
                add(f"**Exponential rule:** $\\frac{{d}}{{dx}} a^x = a^x \\ln a$ with $a = {latex(base)}$.",
                          f"{Dx(expr)} = {latex(outer)}", depth)
                return outer
            add(f"**Chain rule + exponential rule:** let $u = {latex(n)}$.", rule, depth)
            add("Find $u'$:", None, depth + 1)
            up = diff_steps(n, x, steps, depth + 2, partial)
            res = outer * up
            add("Combine.", f"{Dx(expr)} = {latex(res)}", depth)
            return res

        # Variable base and variable exponent: logarithmic differentiation
        add(
            "**Logarithmic differentiation:** the variable is in both the base and exponent. "
            f"Let $y = {latex(expr)}$ and take $\\ln$ of both sides.",
            rf"\ln y = {latex(n * log(base))}", depth)
        add("Differentiate the right-hand side:", None, depth + 1)
        inner = diff_steps(n * log(base), x, steps, depth + 2, partial)
        res = expr * inner
        add(r"Since $\frac{d}{dx}\ln y = \frac{y'}{y}$, multiply by $y$.",
                  f"{Dx(expr)} = {latex(res)}", depth)
        return res

    if expr.func in OUTER and len(expr.args) == 1:
        u = expr.args[0]
        fname = latex(expr.func(_u))
        fprime = OUTER[expr.func](_u)
        if u == x:
            res = OUTER[expr.func](x)
            add(f"Standard derivative: $\\frac{{d}}{{du}} {fname} = {latex(fprime)}$.",
                      f"{Dx(expr)} = {latex(res)}", depth)
            return res
        add(
            f"**Chain rule:** outer function $f(u) = {fname}$, inner function $u = {latex(u)}$.",
            rf"\frac{{d}}{{dx}} f(u) = f'(u) \cdot u' = {latex(fprime)} \cdot u'", depth)
        add("Find $u'$:", None, depth + 1)
        up = diff_steps(u, x, steps, depth + 2, partial)
        res = OUTER[expr.func](u) * up
        add("Substitute $u$ back in.", f"{Dx(expr)} = {latex(res)}", depth)
        return res

    res = diff(expr, x)
    add("Differentiate using the standard rules.", f"{Dx(expr)} = {latex(res)}", depth)
    return res


def finish(raw, steps, lhs_latex):
    """Show a simplification step if it helps, return the tidy form."""
    nice = tidy(raw)
    if nice != raw:
        steps.add("Simplify.", f"{lhs_latex} = {latex(nice)}")
    return nice


def derivative(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    order = int(p.get("order") or 1)
    if not 1 <= order <= 10:
        raise SolverError("Order must be between 1 and 10.")
    steps = Steps()
    current = expr
    for k in range(1, order + 1):
        name = "f'" if k == 1 else ("f''" if k == 2 else f"f^{{({k})}}")
        if order > 1:
            steps.add(f"### Derivative #{k}: differentiate ${latex(current)}$")
        raw = diff_steps(current, x, steps)
        current = finish(raw, steps, f"{name}({latex(x)})")

    ans = current
    extra = {}
    if p.get("point") not in (None, ""):
        a = parse(p["point"])
        val = tidy(current.subs(x, a))
        steps.add(f"Evaluate at ${latex(x)} = {latex(a)}$.",
                  f"{latex(current)}\\Big|_{{{latex(x)} = {latex(a)}}} = {latex(val)}")
        return result(latex(val), steps, approx(val), {"expression": latex(ans)})
    return result(latex(ans), steps)


def partial(p):
    expr = parse(p["expr"])
    order = [s for s in str(p.get("vars") or "").replace(",", " ").split()]
    # "xy" means d/dx then d/dy
    names = []
    for chunk in order:
        names.extend(list(chunk) if len(chunk) > 1 and chunk not in ("theta", "phi", "rho", "lambda") else [chunk])
    if not names:
        raise SolverError("Enter which variable(s) to differentiate with respect to, e.g. x or xy.")
    steps = Steps()
    steps.add("For a partial derivative, differentiate with respect to one variable and "
              "treat every other variable as a constant.")
    current = expr
    sub = ""
    for nm in names:
        v = parse_symbol(nm)
        sub += latex(v)
        steps.add(f"### Differentiate with respect to ${latex(v)}$")
        raw = diff_steps(current, v, steps, partial=True)
        current = finish(raw, steps, f"f_{{{sub}}}")
    if p.get("point"):
        pt = parse_point(p["point"], expr, names)
        val = tidy(current.subs(pt))
        steps.add("Evaluate at the point.", f"f_{{{sub}}} = {latex(val)}")
        return result(latex(val), steps, approx(val), {"expression": latex(current)})
    return result(f"f_{{{sub}}} = {latex(current)}", steps)


def parse_point(text, expr, fallback_names=()):
    """'x=1, y=2' or '(1, 2)' (assigned to sorted free symbols) -> dict."""
    text = str(text).strip().strip("()")
    parts = [s.strip() for s in text.split(",") if s.strip()]
    if all("=" in s for s in parts):
        return {parse_symbol(s.split("=")[0]): parse(s.split("=")[1]) for s in parts}
    syms = sorted(expr.free_symbols, key=lambda s: s.name)
    if len(parts) != len(syms):
        raise SolverError(f"Point has {len(parts)} coordinate(s) but the function has variables "
                          f"{', '.join(s.name for s in syms)}. Use the form x=1, y=2.")
    return dict(zip(syms, [parse(s) for s in parts]))


def implicit(p):
    eq = parse_equation(p["equation"])
    x = parse_symbol(p.get("x") or "x")
    y = parse_symbol(p.get("y") or "y", "y")
    F = eq.lhs - eq.rhs
    steps = Steps()
    steps.add("Move everything to one side so the equation reads $F(x, y) = 0$.",
              f"F({latex(x)}, {latex(y)}) = {latex(F)} = 0")
    steps.add(f"Differentiating both sides with respect to ${latex(x)}$ (treating ${latex(y)}$ as a function of "
              f"${latex(x)}$) gives $F_x + F_y \\frac{{dy}}{{dx}} = 0$, so",
              rf"\frac{{d{latex(y)}}}{{d{latex(x)}}} = -\frac{{F_{{{latex(x)}}}}}{{F_{{{latex(y)}}}}}")
    steps.add(f"### Find $F_{{{latex(x)}}}$ (treat ${latex(y)}$ as a constant)")
    Fx = tidy(diff_steps(F, x, steps, partial=True))
    steps.add(f"### Find $F_{{{latex(y)}}}$ (treat ${latex(x)}$ as a constant)")
    Fy = tidy(diff_steps(F, y, steps, partial=True))
    if Fy == 0:
        raise SolverError(f"F_{y} = 0, so dy/dx is undefined for this equation.")
    raw = -Fx / Fy
    steps.add("Substitute into the formula.",
              rf"\frac{{d{latex(y)}}}{{d{latex(x)}}} = -\frac{{{latex(Fx)}}}{{{latex(Fy)}}}")
    ans = finish(raw, steps, rf"\frac{{d{latex(y)}}}{{d{latex(x)}}}")
    lhs = rf"\frac{{d{latex(y)}}}{{d{latex(x)}}}"
    if p.get("point"):
        pt = parse_point(p["point"], F)
        val = tidy(ans.subs(pt))
        steps.add("Evaluate at the given point.", f"{lhs} = {latex(val)}")
        return result(latex(val), steps, approx(val), {"expression": latex(ans)})
    return result(f"{lhs} = {latex(ans)}", steps)
