"""Shared helpers: input parsing, LaTeX output and the Steps collector."""
import builtins
import keyword
import re

from sympy import (
    Basic, E, I, pi, oo, zoo, nan, Symbol, Eq, sympify, latex as _latex, log, sqrt,
    asin, acos, atan, acot, asec, acsc, sec, csc, cot, sinh, cosh, tanh, Abs,
    factorial, exp, N,
)
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

TRANSFORMS = standard_transformations + (implicit_multiplication_application, convert_xor)

LOCALS = {
    "e": E, "E": E, "pi": pi, "π": pi,
    "inf": oo, "infinity": oo, "oo": oo, "∞": oo,
    "ln": log, "log": log, "sqrt": sqrt, "exp": exp, "abs": Abs, "Abs": Abs,
    "arcsin": asin, "arccos": acos, "arctan": atan, "arccot": acot,
    "arcsec": asec, "arccsc": acsc, "asin": asin, "acos": acos, "atan": atan,
    "sec": sec, "csc": csc, "cot": cot, "sinh": sinh, "cosh": cosh, "tanh": tanh,
    "factorial": factorial,
    # Common variable names that must not be split into letters
    "theta": Symbol("theta"), "phi": Symbol("phi"), "rho": Symbol("rho"),
    "lam": Symbol("lambda"), "t": Symbol("t"),
}

# Names SymPy's parser would resolve to something other than a plain symbol. parse_expr is
# eval-based, so anything outside the math allowlist below must be rejected, not passed through.
ALLOWED_NAMES = set(LOCALS) | {
    "sin", "cos", "tan", "asinh", "acosh", "atanh", "acot", "asec", "acsc",
    "sign", "floor", "ceiling", "erf", "gamma", "cbrt", "root", "Rational", "Integer", "Float",
}
_BLOCKED_NAMES = set(dir(builtins)) | set(keyword.kwlist)
try:
    _sympy_ns = {}
    exec("from sympy import *", _sympy_ns)
    _BLOCKED_NAMES |= {k for k in _sympy_ns if len(k) > 1}
except Exception:
    pass
_BLOCKED_NAMES -= ALLOWED_NAMES


class SolverError(Exception):
    """An error whose message is safe and useful to show to the user."""


def _validate(text):
    if len(text) > 500:
        raise SolverError("Input is too long (500 characters max).")
    bad = re.search(r"[_'\"\\\[\]{};:@#$`?~&]", text)
    if bad:
        raise SolverError(f"The character '{bad.group()}' isn't allowed in a math expression.")
    # A '.' is only allowed as a decimal point (followed by a digit, not after a name)
    if re.search(r"\.(?!\d)|(?<=[A-Za-z)])\.", text):
        raise SolverError("Use '.' only for decimals, like 0.5.")
    for name in re.findall(r"[A-Za-z][A-Za-z0-9]*", text):
        if name in _BLOCKED_NAMES:
            raise SolverError(f"Unknown function '{name}'.")


def _clean(text):
    text = str(text).strip()
    if not text:
        raise SolverError("Input is empty.")
    text = text.replace("**", "^").replace("·", "*").replace("×", "*").replace("÷", "/")
    text = text.replace("−", "-").replace("√", "sqrt")
    # |expr| -> Abs(expr) for simple, non-nested bars
    text = re.sub(r"\|([^|]+)\|", r"Abs(\1)", text)
    # log_b(x) -> log(x, b)
    text = re.sub(r"log_([A-Za-z0-9]+)\s*\(([^()]*)\)", r"log(\2, \1)", text)
    _validate(text)
    return text


def parse(text):
    """Parse a user expression such as '3x^2 sin(x) + e^x'."""
    text = _clean(text)
    if "=" in text:
        raise SolverError("Expected an expression, not an equation (remove the '=').")
    try:
        expr = parse_expr(text, local_dict=dict(LOCALS), transformations=TRANSFORMS)
    except Exception:
        raise SolverError(f"Couldn't understand '{text}'. Check parentheses and operators.")
    if not isinstance(expr, Basic):
        raise SolverError(f"Couldn't understand '{text}' as a math expression.")
    return expr.subs(Symbol("e"), E)


def parse_equation(text):
    """Parse 'lhs = rhs' into an Eq. Plain expressions are treated as expr = 0."""
    text = _clean(text)
    if text.count("=") > 1:
        raise SolverError("An equation can only contain one '='.")
    if "=" in text:
        lhs, rhs = text.split("=")
        return Eq(parse(lhs), parse(rhs), evaluate=False)
    return Eq(parse(text), 0, evaluate=False)


def parse_symbol(text, default="x"):
    name = (str(text).strip() if text else "") or default
    if not re.fullmatch(r"[A-Za-z_]\w*", name):
        raise SolverError(f"'{name}' is not a valid variable name.")
    return LOCALS.get(name) if isinstance(LOCALS.get(name), Symbol) else Symbol(name)


def pick_variable(expr, requested=None, default="x"):
    """Use the requested variable, else x if present, else the only free symbol."""
    if requested and str(requested).strip():
        return parse_symbol(requested)
    free = sorted(expr.free_symbols, key=lambda s: s.name)
    names = [s.name for s in free]
    if default in names or not free:
        return Symbol(default)
    if len(free) == 1:
        return free[0]
    raise SolverError(f"Several variables found ({', '.join(names)}). Please specify which one to use.")


def latex(expr):
    return _latex(expr, ln_notation=True, inv_trig_style="full")


def is_finite_number(v):
    return v is not None and v.is_number and v not in (oo, -oo, zoo, nan) and not v.has(nan, zoo)


def approx(expr, digits=10):
    """Decimal approximation as a string, or None if not a plain number."""
    try:
        if not expr.is_number or expr.has(oo, -oo, zoo, nan):
            return None
        val = N(expr, digits)
        if val.has(I) and abs(N(val.as_real_imag()[1])) > 1e-12:
            return latex(val)
        val = N(val.as_real_imag()[0], digits)
        return str(val).rstrip("0").rstrip(".") if "." in str(val) else str(val)
    except Exception:
        return None


def tidy(expr):
    """Return the simplest-looking of a few equivalent forms of expr."""
    from sympy import simplify, factor, cancel, expand, count_ops, trigsimp
    candidates = [expr]
    for fn in (simplify, factor, cancel, trigsimp, expand):
        try:
            candidates.append(fn(expr))
        except Exception:
            pass
    return min(candidates, key=lambda c: (count_ops(c), len(str(c))))


class Steps:
    """Ordered list of explanation steps.

    Each step has plain text (may contain inline $latex$), optional display math
    and a depth used by the UI to indent sub-work.
    """

    def __init__(self):
        self.items = []

    def add(self, text, math=None, depth=0):
        self.items.append({"text": text, "math": math, "depth": depth})

    def extend(self, other, depth_offset=0):
        for it in other.items:
            self.items.append({**it, "depth": it["depth"] + depth_offset})


def result(answer_latex, steps, approx_value=None, extra=None):
    out = {"answer": answer_latex, "steps": steps.items}
    if approx_value:
        out["approx"] = approx_value
    if extra:
        out.update(extra)
    return out
