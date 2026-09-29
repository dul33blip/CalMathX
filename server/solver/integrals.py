"""Integrals with steps, built from SymPy's manualintegrate rule tree."""
from sympy import (
    E, Symbol, Dummy, Integral, integrate, diff, simplify, limit, oo, S, Interval,
    singularities, zoo, nan, fraction, Poly, Add, factor, together, apart, sin, cos, tan, sec, csc, cot,
)
from sympy.integrals import manualintegrate as mi

from common import (
    Steps, SolverError, latex, parse, pick_variable, tidy, result, approx, is_finite_number,
)

ATOMIC = {
    "ConstantRule": r"\int c\,dx = cx",
    "PowerRule": r"\int x^n\,dx = \frac{x^{n+1}}{n+1} \quad (n \neq -1)",
    "ReciprocalRule": r"\int \frac{1}{x}\,dx = \ln|x|",
    "ExpRule": r"\int a^x\,dx = \frac{a^x}{\ln a}",
    "SinRule": r"\int \sin x\,dx = -\cos x",
    "CosRule": r"\int \cos x\,dx = \sin x",
    "Sec2Rule": r"\int \sec^2 x\,dx = \tan x",
    "Csc2Rule": r"\int \csc^2 x\,dx = -\cot x",
    "SecTanRule": r"\int \sec x \tan x\,dx = \sec x",
    "CscCotRule": r"\int \csc x \cot x\,dx = -\csc x",
    "ArctanRule": r"\int \frac{1}{a^2 + x^2}\,dx = \frac{1}{a}\arctan\frac{x}{a}",
    "ArcsinRule": r"\int \frac{1}{\sqrt{1 - x^2}}\,dx = \arcsin x",
    "ArcsinhRule": r"\int \frac{1}{\sqrt{1 + x^2}}\,dx = \operatorname{arsinh} x",
    "SinhRule": r"\int \sinh x\,dx = \cosh x",
    "CoshRule": r"\int \cosh x\,dx = \sinh x",
}

NAMES = {
    "ConstantRule": "Constant rule",
    "PowerRule": "Power rule",
    "ReciprocalRule": "Reciprocal rule",
    "ExpRule": "Exponential rule",
    "SinRule": "Standard integral", "CosRule": "Standard integral",
    "Sec2Rule": "Standard integral", "Csc2Rule": "Standard integral",
    "SecTanRule": "Standard integral", "CscCotRule": "Standard integral",
    "SinhRule": "Standard integral", "CoshRule": "Standard integral",
    "ArctanRule": "Inverse-tangent form", "ArcsinRule": "Inverse-sine form",
    "ArcsinhRule": "Inverse-hyperbolic-sine form",
}


def disp(e):
    """LaTeX with SymPy's internal Dummy symbols shown by their plain name."""
    e = S(e)
    return latex(e.xreplace({d: Symbol(d.name) for d in e.atoms(Dummy)}))


def I(f, x):
    body = disp(f)
    if isinstance(S(f), Add):
        body = rf"\left({body}\right)"
    return rf"\int {body}\,d{disp(x)}"


def _has_unknown(rule):
    return "DontKnowRule" in repr(rule)


def rule_steps(rule, steps, depth=0):
    """Explain one node of the rule tree. Returns its antiderivative."""
    name = type(rule).__name__
    f, x = rule.integrand, rule.variable
    F = rule.eval()

    if name == "AlternativeRule":
        return rule_steps(rule.alternatives[0], steps, depth)

    if name == "ExpRule" and rule.base == E:
        steps.add(r"**Exponential rule:** $\int e^x\,dx = e^x$", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name in ATOMIC:
        steps.add(f"**{NAMES[name]}:** ${ATOMIC[name]}$", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name == "ConstantTimesRule":
        steps.add(f"**Constant multiple:** pull the constant ${disp(rule.constant)}$ outside the integral.",
                  f"{I(f, x)} = {disp(rule.constant)} {I(rule.other, x)}", depth)
        inner = rule_steps(rule.substep, steps, depth + 1)
        steps.add("Multiply by the constant.", f"{I(f, x)} = {disp(rule.constant * inner)}", depth)
        return F

    if name == "AddRule":
        terms = [s.integrand for s in rule.substeps]
        steps.add("**Sum rule:** integrate each term separately.",
                  f"{I(f, x)} = " + " + ".join(I(t, x) for t in terms), depth)
        for s in rule.substeps:
            rule_steps(s, steps, depth + 1)
        steps.add("Combine the results.", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name == "URule":
        u, g = rule.u_var, rule.u_func
        du = diff(g, x)
        steps.add(f"**u-substitution:** let $u = {disp(g)}$.",
                  rf"u = {disp(g)} \quad\Rightarrow\quad du = {disp(du)}\,d{disp(x)}", depth)
        steps.add("Rewrite the integral in terms of $u$.",
                  f"{I(f, x)} = {I(rule.substep.integrand, u)}", depth)
        Fu = rule_steps(rule.substep, steps, depth + 1)
        steps.add(f"Substitute back $u = {disp(g)}$.", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name == "PartsRule":
        u, dv = rule.u, rule.dv
        du = diff(u, x)
        steps.add(r"**Integration by parts:** $\int u\,dv = uv - \int v\,du$.",
                  rf"u = {disp(u)}, \qquad dv = {disp(dv)}\,d{disp(x)}", depth)
        steps.add(f"Differentiate $u$ and integrate $dv$:", rf"du = {disp(du)}\,d{disp(x)}", depth + 1)
        v = rule_steps(rule.v_step, steps, depth + 2) if rule.v_step else integrate(dv, x)
        steps.add("Apply the formula.",
                  rf"{I(f, x)} = {disp(u * v)} - {I(v * du, x)}", depth)
        if rule.second_step is not None:
            steps.add("Evaluate the remaining integral:", None, depth + 1)
            rule_steps(rule.second_step, steps, depth + 2)
        steps.add("Put it together.", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name == "CyclicPartsRule":
        steps.add("**Integration by parts (cyclic):** applying parts repeatedly brings the original "
                  "integral back, so we can solve for it algebraically.", None, depth)
        for pr in rule.parts_rules:
            steps.add(rf"Parts with $u = {disp(pr.u)}$, $dv = {disp(pr.dv)}\,d{disp(x)}$.", None, depth + 1)
        steps.add(rf"The original integral reappears with coefficient ${disp(rule.coefficient)}$. "
                  r"Move it to the left side and divide.", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name == "TrigSubstitutionRule":
        th = rule.theta
        steps.add(f"**Trig substitution:** let ${disp(x)} = {disp(rule.func)}$.",
                  rf"d{disp(x)} = {disp(diff(rule.func, th))}\,d{disp(th)}", depth)
        steps.add("The integral becomes:", f"{I(rule.rewritten, th)}", depth)
        rule_steps(rule.substep, steps, depth + 1)
        steps.add(f"Convert back to ${disp(x)}$ (using a reference triangle).", f"{I(f, x)} = {disp(F)}", depth)
        return F

    if name in ("RewriteRule", "CompleteSquareRule") and hasattr(rule, "rewritten"):
        shown = rule.rewritten
        if f.is_rational_function(x) and fraction(together(f))[1].has(x):
            try:
                shown = apart(f, x)
            except Exception:
                pass
            why = "**Partial fractions:** split the rational function into simpler fractions."
        elif f.has(sin, cos, tan, sec, csc, cot):
            why = "**Trig identity:** rewrite the integrand in an easier form."
        else:
            why = "**Rewrite** the integrand in an easier form."
        steps.add(why, f"{disp(f)} = {disp(shown)}", depth)
        rule_steps(rule.substep, steps, depth + 1)
        return F

    if hasattr(rule, "substep") and rule.substep is not None:
        steps.add("Transform the integrand.", f"{I(f, x)} = {I(rule.substep.integrand, rule.substep.variable)}", depth)
        rule_steps(rule.substep, steps, depth + 1)
        return F

    steps.add("Use a standard integral formula.", f"{I(f, x)} = {disp(F)}", depth)
    return F


def _partial_fractions(expr, x, steps, depth):
    """If expr is a rational function worth decomposing, explain and return the decomposition."""
    if not expr.is_rational_function(x):
        return None
    num, den = fraction(together(expr))
    if not den.has(x) or Poly(den, x).degree() < 2:
        return None
    pf = apart(expr, x)
    if pf == expr or len(Add.make_args(pf)) < 2:
        return None
    if Poly(num, x).degree() >= Poly(den, x).degree():
        steps.add("The numerator's degree is at least the denominator's, so start with **polynomial long division**.",
                  None, depth)
    steps.add("**Partial fractions:** factor the denominator and split into simpler fractions "
              "(solve for the unknown constants by matching coefficients or plugging in roots).",
              rf"{latex(expr)} = \frac{{{latex(num)}}}{{{latex(factor(den))}}} = {latex(pf)}", depth)
    return pf


def antiderivative_steps(expr, x, steps, depth=0, check=True, decompose=True):
    """Find an antiderivative with steps. Returns F (without +C)."""
    pf = _partial_fractions(expr, x, steps, depth) if decompose else None
    if pf is not None:
        steps.add("Integrate each piece:", f"{I(expr, x)} = {I(pf, x)}", depth)
        F = antiderivative_steps(pf, x, steps, depth + 1, check=False, decompose=False)
        steps.add("Combine.", f"{I(expr, x)} = {latex(F)}", depth)
        return F
    try:
        rule = mi.integral_steps(expr, x)
    except Exception:
        rule = None
    if rule is None or _has_unknown(rule):
        F = integrate(expr, x)
        if F.has(Integral):
            raise SolverError(f"No closed-form antiderivative was found for {expr}. "
                              "Try a definite integral for a numeric answer.")
        steps.add("This integral doesn't fit the standard hand techniques, so it was solved with a "
                  "complete symbolic algorithm (Risch). The result is:",
                  f"{I(expr, x)} = {latex(F)}", depth)
        return F
    F = rule_steps(rule, steps, depth)
    nice = tidy(F)
    if nice != F:
        steps.add("Simplify.", f"{I(expr, x)} = {latex(nice)}", depth)
        F = nice
    if check:
        try:
            if simplify(diff(F, x) - expr) == 0:
                steps.add(f"✓ **Check:** differentiating the answer gives back the integrand.",
                          rf"\frac{{d}}{{d{latex(x)}}}\left[{latex(F)}\right] = {latex(expr)}", depth)
        except Exception:
            pass
    return F


def _bound_value(F, x, b, side):
    """F evaluated at a bound, via a limit when the bound is infinite or F is undefined there."""
    if b in (oo, -oo):
        return limit(F, x, b)
    v = F.subs(x, b)
    if not is_finite_number(v) and v.is_number:
        return limit(F, x, b, side)
    return v


def definite_steps(expr, x, a, b, steps, depth=0):
    """Evaluate ∫_a^b expr dx with steps. Returns the exact value."""
    improper = a in (oo, -oo) or b in (oo, -oo)
    inner_sing = []
    try:
        if a.is_number and b.is_number and not improper:
            sing = singularities(expr, x, Interval(a, b))
            inner_sing = sorted(sing) if sing.is_finite_set else []
    except Exception:
        pass
    if inner_sing:
        improper = True
        steps.add(f"The integrand is undefined at ${', '.join(latex(s) for s in inner_sing)}$, "
                  "so this is an **improper integral** and must be evaluated with limits.", None, depth)
    elif improper:
        steps.add("An infinite bound makes this an **improper integral**, evaluated as a limit.", None, depth)

    steps.add("**Step 1:** find an antiderivative.", None, depth)
    F = antiderivative_steps(expr, x, steps, depth + 1)
    lo, hi = latex(a), latex(b)
    steps.add(r"**Step 2:** apply the Fundamental Theorem of Calculus: $\int_a^b f\,dx = F(b) - F(a)$.",
              rf"\int_{{{lo}}}^{{{hi}}} {latex(expr)}\,d{latex(x)} = \Big[{latex(F)}\Big]_{{{lo}}}^{{{hi}}}", depth)

    exact = integrate(expr, (x, a, b))
    if inner_sing or exact.has(Integral):
        if exact.has(Integral):
            val = S(exact.evalf(15))
            steps.add("No closed form exists, so evaluate numerically.", f"\\approx {latex(val)}", depth)
            return val
        steps.add("Split at the singular point(s) and take one-sided limits.",
                  f"= {latex(exact)}", depth)
        if exact in (oo, -oo, zoo) or exact.has(nan):
            steps.add("The limit is infinite, so the integral **diverges**.", None, depth)
        return exact

    Fb, Fa = _bound_value(F, x, b, "-"), _bound_value(F, x, a, "+")
    if improper:
        t = Symbol("t")
        side = b if b in (oo, -oo) else a
        steps.add(f"Take the limit as $t \\to {latex(side)}$.",
                  (rf"\lim_{{t \to {latex(b)}}} \left[{latex(F.subs(x, t))}\right] - \left({latex(Fa)}\right)"
                   if b in (oo, -oo) else
                   rf"{latex(Fb)} - \lim_{{t \to {latex(a)}}} \left[{latex(F.subs(x, t))}\right]"),
                  depth)
    else:
        steps.add("Substitute the bounds.",
                  rf"= \left({latex(F.subs(x, b))}\right) - \left({latex(F.subs(x, a))}\right)", depth)
    val = tidy(exact)
    steps.add("Simplify.", f"= {latex(val)}", depth)
    if val in (oo, -oo, zoo):
        steps.add("The result is infinite, so the integral **diverges**.", None, depth)
    return val


def integral(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    lower, upper = p.get("lower"), p.get("upper")
    steps = Steps()
    if lower not in (None, "") and upper not in (None, ""):
        a, b = parse(lower), parse(upper)
        val = definite_steps(expr, x, a, b, steps)
        return result(latex(val), steps, approx(val))
    if (lower not in (None, "")) != (upper not in (None, "")):
        raise SolverError("For a definite integral enter both bounds (or leave both empty).")
    F = antiderivative_steps(expr, x, steps)
    steps.add("Add the constant of integration $C$.", f"{I(expr, x)} = {latex(F)} + C")
    return result(f"{latex(F)} + C", steps)
