"""Limits with steps: substitution, factor & cancel, dominant terms, L'Hôpital, ln trick."""
from sympy import (
    limit, oo, zoo, nan, fraction, cancel, factor, diff, log, exp, Pow, Mul, Add,
    together, degree, LT, simplify, AccumBounds, Symbol, S,
)

from common import Steps, SolverError, latex, parse, pick_variable, tidy, result, approx, is_finite_number


def lim_tex(x, a, d):
    arrow = latex(a) + ("^{+}" if d == "+" and a not in (oo, -oo) else "^{-}" if d == "-" and a not in (oo, -oo) else "")
    return rf"\lim_{{{latex(x)} \to {arrow}}}"


def _lim(e, x, a, d):
    if a in (oo, -oo):
        return limit(e, x, a)
    return limit(e, x, a, d if d in ("+", "-") else "+-")


def _kind(v):
    if v == 0:
        return "0"
    if v in (oo, -oo, zoo):
        return "inf"
    if v.has(AccumBounds) or v is nan:
        return "osc"
    return "num"


def explain(expr, x, a, d, steps, depth=0, budget=5, quotient=None):
    """Add explanation steps for lim expr. The caller trusts SymPy for the final value.

    quotient=(num, den) keeps a rewritten quotient intact; SymPy would otherwise
    auto-simplify e.g. ln(1 + 1/x) / (1/x) straight back into a product.
    """
    L = lim_tex(x, a, d)
    if budget <= 0:
        return

    # 1. Direct substitution
    if a not in (oo, -oo) and not quotient:
        try:
            v = simplify(expr.subs(x, a))
        except Exception:
            v = nan
        if is_finite_number(v) and v.is_real is not False:
            steps.add(f"**Direct substitution:** plug in ${latex(x)} = {latex(a)}$ "
                      "(the function is continuous there).",
                      f"{L} {latex(expr)} = {latex(v)}", depth)
            return

    if quotient:
        num, den = quotient
    else:
        num, den = fraction(together(expr)) if not isinstance(expr, Pow) else (expr, S(1))

    # 2. Quotients
    if den != 1 and den.has(x):
        Ln, Ld = _lim(num, x, a, d), _lim(den, x, a, d)
        kn, kd = _kind(Ln), _kind(Ld)
        if not ((kn, kd) in (("0", "0"), ("inf", "inf"))):
            if kd == "0" and kn in ("num", "inf"):
                steps.add(f"The numerator approaches ${latex(Ln)}$ while the denominator approaches $0$, "
                          "so the quotient grows without bound. Check the sign from each side.", None, depth)
            else:
                steps.add(f"The numerator approaches ${latex(Ln)}$ and the denominator approaches ${latex(Ld)}$.",
                          None, depth)
            return
        form = r"\frac{0}{0}" if kn == "0" else r"\frac{\infty}{\infty}"
        steps.add(f"Substituting gives the **indeterminate form** ${form}$, so we need another method.", None, depth)

        is_rational = expr.is_rational_function(x)
        if is_rational and a not in (oo, -oo):
            c = cancel(expr)
            if c != expr:
                steps.add("**Factor and cancel** the common factor.",
                          rf"\frac{{{latex(factor(num))}}}{{{latex(factor(den))}}} = {latex(c)}", depth)
                explain(c, x, a, d, steps, depth, budget - 1)
                return
        if is_rational and a in (oo, -oo):
            p, q = degree(num, x), degree(den, x)
            steps.add(f"**Dominant terms:** as ${latex(x)} \\to {latex(a)}$ only the highest powers matter. "
                      f"The numerator has degree ${p}$ and the denominator has degree ${q}$.",
                      rf"{L} {latex(expr)} = {L} \frac{{{latex(LT(num, x))}}}{{{latex(LT(den, x))}}}", depth)
            if p < q:
                steps.add("The denominator's degree is larger, so the limit is $0$.", None, depth)
            elif p == q:
                steps.add("The degrees are equal, so the limit is the ratio of the leading coefficients.", None, depth)
            else:
                steps.add("The numerator's degree is larger, so the quotient grows without bound.", None, depth)
            return

        n1, d1 = diff(num, x), diff(den, x)
        new = cancel(n1 / d1) if (n1 / d1).is_rational_function(x) else n1 / d1
        steps.add(r"**L'Hôpital's rule:** $\lim \frac{f}{g} = \lim \frac{f'}{g'}$. Differentiate the numerator and denominator separately.",
                  rf"f' = {latex(n1)}, \qquad g' = {latex(d1)}", depth)
        steps.add("The new limit is:", rf"{L} \frac{{{latex(n1)}}}{{{latex(d1)}}}", depth)
        new = tidy(new)
        if latex(new) != latex(n1 / d1) or n1.is_Add or d1.is_Add:
            steps.add("Simplify.", rf"{L} {latex(new)}", depth)
        explain(new, x, a, d, steps, depth, budget - 1)
        return

    # 3. Exponential indeterminate forms 1^∞, 0^0, ∞^0
    if isinstance(expr, Pow) and expr.base.has(x) and expr.exp.has(x):
        b, g = expr.base, expr.exp
        Lb, Lg = _lim(b, x, a, d), _lim(g, x, a, d)
        form = {("1", "inf"): r"1^{\infty}", ("0", "0"): "0^0", ("inf", "0"): r"\infty^0"}.get(
            ("1" if Lb == 1 else _kind(Lb), _kind(Lg)))
        if form:
            steps.add(f"This has the indeterminate form ${form}$. Use the **natural log trick**: "
                      f"let $y = {latex(expr)}$, so $\\ln y = {latex(g * log(b))}$.", None, depth)
            steps.add("Write $\\ln y$ as a quotient so L'Hôpital's rule can apply.",
                      rf"{L} \ln y = {L} \frac{{{latex(log(b))}}}{{{latex(1 / g)}}}", depth)
            explain(g * log(b), x, a, d, steps, depth + 1, budget - 1, quotient=(log(b), 1 / g))
            Lln = _lim(g * log(b), x, a, d)
            steps.add(f"So $\\ln y \\to {latex(Lln)}$, which means $y \\to e^{{{latex(Lln)}}}$.",
                      f"{L} {latex(expr)} = {latex(exp(Lln))}", depth)
            return

    # 4. 0·∞ products
    if isinstance(expr, Mul):
        zero = [f for f in expr.args if f.has(x) and _lim(f, x, a, d) == 0]
        big = [f for f in expr.args if f.has(x) and _lim(f, x, a, d) in (oo, -oo)]
        if zero and big:
            f, g = zero[0], Mul(*[t for t in expr.args if t is not zero[0]])
            steps.add(r"This has the indeterminate form $0 \cdot \infty$. Rewrite the product as a quotient.",
                      rf"{latex(expr)} = \frac{{{latex(g)}}}{{{latex(1 / f)}}}", depth)
            explain(expr, x, a, d, steps, depth, budget - 1, quotient=(g, 1 / f))
            return

    # 5. ∞ − ∞
    if isinstance(expr, Add):
        comb = together(expr)
        if comb != expr and fraction(comb)[1].has(x):
            steps.add(r"Combine into a single fraction (this resolves a possible $\infty - \infty$ form).",
                      f"{latex(expr)} = {latex(comb)}", depth)
            explain(comb, x, a, d, steps, depth, budget - 1)
            return

    val = _lim(expr, x, a, d)
    steps.add("Evaluate the limit using the dominant (leading) behavior of each term.",
              f"{L} {latex(expr)} = {latex(val)}", depth)


def limit_op(p):
    expr = parse(p["expr"])
    x = pick_variable(expr, p.get("var"))
    a = parse(p.get("point") or "0")
    d = p.get("dir") or "both"
    steps = Steps()
    if a in (oo, -oo):
        d = "both"

    L = lim_tex(x, a, d if d in "+-" else "")
    steps.add("We want to evaluate:", f"{L} {latex(expr)}")

    if d == "both" and a not in (oo, -oo):
        right, left = limit(expr, x, a, "+"), limit(expr, x, a, "-")
        if right != left:
            steps.add("The expression behaves differently on each side, so check the one-sided limits.")
            steps.add(f"### Right-hand limit (${latex(x)} \\to {latex(a)}^+$)")
            explain(expr, x, a, "+", steps, 1)
            steps.add(f"Right-hand limit $= {latex(right)}$.")
            steps.add(f"### Left-hand limit (${latex(x)} \\to {latex(a)}^-$)")
            explain(expr, x, a, "-", steps, 1)
            steps.add(f"Left-hand limit $= {latex(left)}$.")
            steps.add("The one-sided limits are not equal, so the two-sided limit **does not exist**.")
            return result(r"\text{Does not exist}", steps, None,
                          {"expression": rf"\text{{left}} = {latex(left)},\ \text{{right}} = {latex(right)}"})
        val = right
    else:
        val = _lim(expr, x, a, d)

    explain(expr, x, a, d, steps)
    if val.has(AccumBounds) or val is nan:
        steps.add("The function oscillates and never settles on a value, so the limit **does not exist**.")
        return result(r"\text{Does not exist}", steps)
    val = tidy(val)
    steps.add("**Result:**", f"{L} {latex(expr)} = {latex(val)}")
    return result(latex(val), steps, approx(val))
